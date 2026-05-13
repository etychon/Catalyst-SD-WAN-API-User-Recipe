from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from sdwan_recipes.config import Settings
from sdwan_recipes.util import unwrap_data

logger = logging.getLogger("sdwan_recipes")


class SdwanApiError(RuntimeError):
    """Unexpected SD-WAN Manager response or parse failure."""


_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "refresh",
        "csrf",
        "j_password",
        "authorization",
        "cookie",
        "set-cookie",
        "jsessionid",
        "vsessionid",
        "v_session_id",
    }
)


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: ("***" if str(k).lower() in _SENSITIVE_KEYS else _redact(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact(x) for x in obj[:50]]  # cap list size in logs
    return obj


class ManagerClient:
    """
    Minimal Cisco Catalyst SD-WAN Manager API client for Release 20.18.

    Supports JWT authentication (POST /jwt/login) and session authentication
    (POST /j_security_check + GET /dataservice/client/token) per DevNet.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = httpx.Client(
            base_url=settings.base_url,
            verify=settings.verify_ssl,
            timeout=httpx.Timeout(
                connect=settings.connect_timeout,
                read=settings.read_timeout,
                write=settings.read_timeout,
                pool=settings.connect_timeout,
            ),
            follow_redirects=True,
        )
        self._jwt_token: str | None = None
        self._jwt_refresh: str | None = None
        self._csrf: str | None = None
        self._vsession_id: str | None = None

    def close(self) -> None:
        if self._settings.auth_mode == "session":
            try:
                self._client.post("/logout")
            except httpx.HTTPError:
                logger.debug("logout request failed", exc_info=True)
        self._client.close()

    def __enter__(self) -> "ManagerClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def login(self) -> None:
        if self._settings.jwt_token:
            self._apply_preconfigured_jwt()
            return
        if self._settings.auth_mode == "auto":
            self._jwt_token = None
            self._jwt_refresh = None
            self._csrf = None
            try:
                self._login_jwt()
            except (httpx.HTTPStatusError, httpx.RequestError, KeyError, json.JSONDecodeError) as exc:
                logger.info("auto: JWT login unavailable (%s), falling back to session", exc)
                self._jwt_token = None
                self._jwt_refresh = None
                self._csrf = None
                self._login_session()
            return
        if self._settings.auth_mode == "jwt":
            self._login_jwt()
        else:
            self._login_session()

    def _apply_preconfigured_jwt(self) -> None:
        """Use JWT (and optional CSRF/refresh) from Settings; skip POST /jwt/login."""
        self._jwt_token = self._settings.jwt_token
        self._csrf = (self._settings.jwt_csrf or "").strip() or None
        self._jwt_refresh = (self._settings.jwt_refresh or "").strip() or None
        self._vsession_id = self._settings.vsession_id
        logger.info("JWT from environment (skipping /jwt/login)")
        self._bootstrap_csrf_for_bearer()

    def _bootstrap_csrf_for_bearer(self) -> None:
        """
        When using Bearer without XSRF, some Manager builds reject statistics POSTs
        (SessionTokenFilter). GET /dataservice/client/token with Authorization often
        returns the XSRF string paired to that JWT session.
        """
        if not self._jwt_token or self._csrf:
            return
        try:
            r = self._client.get(
                "/dataservice/client/token",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self._jwt_token}",
                },
            )
            if not r.is_success:
                logger.debug("GET /dataservice/client/token (Bearer) -> %s", r.status_code)
                return
            tok = (r.text or "").strip().strip('"')
            if tok:
                self._csrf = tok
                logger.info("XSRF obtained from GET /dataservice/client/token for Bearer auth")
        except httpx.HTTPError as exc:
            logger.debug("Bearer CSRF bootstrap failed: %s", exc)

    def _login_jwt(self) -> None:
        body: dict[str, Any] = {
            "username": self._settings.username,
            "password": self._settings.password,
        }
        if self._settings.tenant:
            body["tenant"] = self._settings.tenant
        if self._settings.jwt_duration is not None:
            body["duration"] = self._settings.jwt_duration
        r = self._client.post("/jwt/login", json=body, headers={"Content-Type": "application/json"})
        if r.status_code == httpx.codes.UNAUTHORIZED:
            raise httpx.HTTPStatusError("JWT login failed", request=r.request, response=r)
        r.raise_for_status()
        data = r.json()
        self._jwt_token = data["token"]
        self._csrf = data.get("csrf")
        self._jwt_refresh = data.get("refresh")
        self._vsession_id = self._settings.vsession_id
        logger.info(
            "JWT login ok user=%s tenant=%s",
            data.get("sub", ""),
            data.get("tenant", ""),
        )
        self._bootstrap_csrf_for_bearer()

    def _login_session(self) -> None:
        payload = {
            "j_username": self._settings.username,
            "j_password": self._settings.password,
        }
        r = self._client.post(
            "/j_security_check",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        text = r.text or ""
        if r.status_code != 200 or "<html" in text.lower():
            raise httpx.HTTPStatusError(
                "Session login failed (check credentials or SSO requirement)",
                request=r.request,
                response=r,
            )
        tok = self._client.get(
            "/dataservice/client/token",
            headers={"Content-Type": "application/json"},
        )
        tok.raise_for_status()
        self._csrf = (tok.text or "").strip().strip('"') or None
        self._jwt_token = None
        logger.info("Session login ok (JSESSIONID cookie established)")
        self._attach_vsession_after_session_login()

    def _attach_vsession_after_session_login(self) -> None:
        """Provider-as-tenant: optional VSessionId from env or from tenant list + vsessionid API."""
        if self._settings.vsession_id:
            self._vsession_id = self._settings.vsession_id
            logger.info("VSessionId from environment")
            return
        if not self._settings.tenant_subdomain:
            return
        tid = self._resolve_tenant_id_by_subdomain(self._settings.tenant_subdomain)
        data = self.dataservice_post_json(f"/dataservice/tenant/{tid}/vsessionid", json_body={})
        self._vsession_id = data.get("VSessionId")
        if not self._vsession_id:
            raise SdwanApiError("POST /dataservice/tenant/.../vsessionid did not return VSessionId")
        logger.info("VSessionId obtained for tenant_id=%s", tid[:8] + "..." if len(tid) > 8 else tid)

    def _resolve_tenant_id_by_subdomain(self, want: str) -> str:
        payload = self.dataservice_json("/dataservice/tenant")
        rows = unwrap_data(payload)
        if not isinstance(rows, list):
            rows = [rows] if isinstance(rows, dict) else []
        want_l = want.strip().lower()
        for row in rows:
            if not isinstance(row, dict):
                continue
            sd = row.get("subDomain") or row.get("subdomain") or ""
            if str(sd).strip().lower() == want_l:
                tid = row.get("tenantId") or row.get("tenant_id")
                if tid:
                    return str(tid)
        raise SdwanApiError(f"No tenant found with subDomain matching {want!r}")

    def _default_headers(self, method: str, *, omit_xsrf: bool = False) -> dict[str, str]:
        h: dict[str, str] = {"Accept": "application/json"}
        if self._jwt_token:
            h["Authorization"] = f"Bearer {self._jwt_token}"
        if self._vsession_id:
            h["VSessionId"] = self._vsession_id
        m = method.upper()
        if (
            not omit_xsrf
            and m in {"POST", "PUT", "PATCH", "DELETE"}
            and self._csrf
        ):
            h["X-XSRF-TOKEN"] = self._csrf
        return h

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        omit_xsrf: bool = False,
    ) -> httpx.Response:
        headers = self._default_headers(method, omit_xsrf=omit_xsrf)
        if json_body is not None:
            headers.setdefault("Content-Type", "application/json")
        r = self._client.request(method, path, params=params, json=json_body, headers=headers)
        if r.status_code == httpx.codes.UNAUTHORIZED and self._jwt_token:
            self._try_refresh_jwt()
            headers = self._default_headers(method, omit_xsrf=omit_xsrf)
            r = self._client.request(method, path, params=params, json=json_body, headers=headers)
        logger.debug("HTTP %s %s -> %s", method, path, r.status_code)
        return r

    def _try_refresh_jwt(self) -> None:
        if not self._jwt_refresh:
            return
        body: dict[str, Any] = {"refresh": self._jwt_refresh}
        if self._settings.jwt_duration is not None:
            body["duration"] = self._settings.jwt_duration
        r = self._client.post("/jwt/refresh", json=body, headers={"Content-Type": "application/json"})
        if not r.is_success:
            logger.info("JWT refresh failed: %s", r.status_code)
            return
        data = r.json()
        self._jwt_token = data.get("token", self._jwt_token)
        self._jwt_refresh = data.get("refresh", self._jwt_refresh)
        logger.info("JWT refreshed")

    def dataservice_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        r = self.request("GET", path, params=params)
        r.raise_for_status()
        try:
            return r.json()
        except json.JSONDecodeError:
            logger.warning("Non-JSON response for %s: %s", path, r.text[:200])
            raise

    def dataservice_post_json(self, path: str, *, json_body: Any) -> Any:
        """POST to /dataservice/... Short paths get /dataservice prefixed."""
        p = path
        if not p.startswith("/dataservice"):
            p = "/dataservice" + (p if p.startswith("/") else "/" + p)
        r = self.request("POST", p, json_body=json_body)
        if r.status_code == httpx.codes.FORBIDDEN and self._jwt_token and "SessionTokenFilter" in (r.text or ""):
            if not self._csrf:
                self._bootstrap_csrf_for_bearer()
                if self._csrf:
                    r = self.request("POST", p, json_body=json_body)
            if (
                r.status_code == httpx.codes.FORBIDDEN
                and self._jwt_token
                and "SessionTokenFilter" in (r.text or "")
                and self._csrf
            ):
                logger.info(
                    "POST %s returned SessionTokenFilter 403 with X-XSRF-TOKEN; retrying without X-XSRF-TOKEN",
                    p,
                )
                r = self.request("POST", p, json_body=json_body, omit_xsrf=True)
        if r.status_code >= 400:
            raise SdwanApiError(f"{p} failed HTTP {r.status_code}: {r.text[:400]}")
        text = (r.text or "").strip()
        if not text:
            return {}
        try:
            return r.json()
        except json.JSONDecodeError as exc:
            raise SdwanApiError(f"{p} did not return JSON") from exc

    def log_json_sample(self, label: str, data: Any) -> None:
        """Safe debug logging (redacted, truncated)."""
        red = _redact(data)
        try:
            s = json.dumps(red, indent=2)[:8000]
        except (TypeError, ValueError):
            s = str(red)[:8000]
        logger.debug("%s sample:\n%s", label, s)
