#!/usr/bin/env python3
"""
Run all recipe-linked sample scripts against one Manager (credentials from samples/.env).

- Loads environment from ``<samples>/.env`` before spawning children (same as ``Settings.load()``).
- Does **not** print secrets; child stderr is shown only on failure (truncated).
- Exit code 0 only if every **required** step succeeds. ``federation_demo`` is skipped when
  ``SDWAN_FEDERATION`` is unset (optional multi-cluster recipe).

Usage (from ``samples/`` after ``pip install -e .``)::

    python scripts/smoke_recipes.py

Never commit ``.env``; it stays gitignored. Copy from ``.env.example`` only locally.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def _load_dotenv(repo: Path) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Install dependencies: pip install -e .") from exc
    env_path = repo / ".env"
    if not env_path.is_file():
        raise SystemExit(
            f"Missing {env_path}. Copy samples/.env.example to samples/.env locally (do not commit .env)."
        )
    load_dotenv(env_path)
    # Optional local overrides (also gitignored if named .env.local)
    load_dotenv(repo / ".env.local", override=False)


def _run(
    repo: Path,
    argv: list[str],
    *,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=str(repo),
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Smoke-test all recipe sample scripts against samples/.env")
    p.add_argument(
        "--samples-repo",
        type=Path,
        default=_REPO,
        help="Path to the samples/ directory (contains .env, scripts/, src/)",
    )
    p.add_argument("--timeout", type=int, default=180, help="Per-script timeout in seconds")
    p.add_argument(
        "--skip-collect-dashboard-snapshot",
        action="store_true",
        help="Skip collect_dashboard_snapshot.py (e.g. if /dataservice/health/devices is 403 for this token)",
    )
    p.add_argument(
        "--require-federation",
        action="store_true",
        help="Fail if SDWAN_FEDERATION is unset (default: skip federation_demo when unset)",
    )
    p.add_argument(
        "--skip-config-group-ux2",
        action="store_true",
        help="Skip config_group_ux2.py (e.g. if Config Group-read RBAC is missing)",
    )
    args = p.parse_args()

    repo = args.samples_repo.resolve()
    if not (repo / "scripts").is_dir():
        raise SystemExit(f"Not a samples repo: {repo}")

    _load_dotenv(repo)

    py = sys.executable
    out_dir = repo / "output" / "smoke"
    out_dir.mkdir(parents=True, exist_ok=True)

    steps: list[tuple[str, list[str]]] = [
        ("inventory_devices", [py, "scripts/inventory_devices.py", "--limit", "2"]),
        ("inventory_status", [py, "scripts/inventory_status.py"]),
    ]

    if not args.skip_config_group_ux2:
        steps.append(
            (
                "config_group_ux2",
                [
                    py,
                    "scripts/config_group_ux2.py",
                    "--out-of-sync-only",
                    "--output",
                    str(out_dir / "config_group_ux2.json"),
                ],
            )
        )
    else:
        print("SKIP config_group_ux2 (--skip-config-group-ux2)")

    steps.extend(
        [
        ("health_tunnels", [py, "scripts/health_tunnels.py", "--limit", "2"]),
        ("topology_location", [py, "scripts/topology_location.py"]),
        ("transport_underlay", [py, "scripts/transport_underlay.py"]),
        ("cellular_thresholds", [py, "scripts/cellular_thresholds.py"]),
        (
            "location_history_demo",
            [
                py,
                "scripts/location_history_demo.py",
                "--db",
                str(out_dir / "location_history.sqlite3"),
            ],
        ),
        ("alarms_events", [py, "scripts/alarms_events.py"]),
        ("cli_bulk_demo", [py, "scripts/cli_bulk_demo.py", "--limit", "2"]),
        ("multitenant_context", [py, "scripts/multitenant_context.py"]),
        ]
    )

    if not args.skip_collect_dashboard_snapshot:
        steps.append(
            (
                "collect_dashboard_snapshot",
                [
                    py,
                    "scripts/collect_dashboard_snapshot.py",
                    "--hours",
                    "1",
                    "--output",
                    str(out_dir / "dashboard_snapshot.json"),
                ],
            )
        )

    fed_env = os.getenv("SDWAN_FEDERATION", "").strip()
    if fed_env:
        steps.append(
            (
                "federation_demo",
                [py, "scripts/federation_demo.py", "--output", str(out_dir / "federation.json")],
            )
        )
    elif args.require_federation:
        print("FAIL federation_demo (SDWAN_FEDERATION unset but --require-federation)")
        return 1
    else:
        print("SKIP federation_demo (SDWAN_FEDERATION unset)")

    failures = 0
    for name, argv in steps:
        try:
            cp = _run(repo, argv, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            print(f"FAIL {name} (timeout {args.timeout}s)")
            failures += 1
            continue
        if cp.returncode != 0:
            failures += 1
            tail_err = (cp.stderr or "")[-1200:]
            tail_out = (cp.stdout or "")[-400:]
            print(f"FAIL {name} exit={cp.returncode}")
            if tail_err.strip():
                print("--- stderr (tail) ---")
                print(tail_err.rstrip())
            if tail_out.strip():
                print("--- stdout (tail) ---")
                print(tail_out.rstrip())
        else:
            print(f"OK   {name}")

    if failures:
        print(f"\nSmoke finished with {failures} failure(s).")
        return 1
    print("\nSmoke finished: all required steps passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
