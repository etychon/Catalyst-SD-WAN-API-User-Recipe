# SD-WAN recipes — Python samples

Install in editable mode from this directory:

```bash
pip install -e .
```

Configuration: copy `.env.example` to `.env` in this directory and set variables. See the root [README.md](../README.md) for usage of individual scripts under `scripts/`. **Do not commit `.env`** (gitignored).

**UX 2.0 CSV onboard (SD-Routing default):** operator recipe [config-group-csv-onboard-deploy.md](../docs/recipes/config-group-csv-onboard-deploy.md); script `scripts/config_group_onboard.py` (module and function docstrings); library `src/sdwan_recipes/config_group.py`, `device_actions.py`.

## Smoke test (live cluster)

With `samples/.env` configured locally (never commit it):

```bash
pip install -e .
python scripts/smoke_recipes.py
```

Use `--skip-collect-dashboard-snapshot` if `/dataservice/health/devices` is 403 for your token. Use `--require-federation` to require `SDWAN_FEDERATION`. Outputs go under `output/smoke/` (parent `output/` is gitignored).
