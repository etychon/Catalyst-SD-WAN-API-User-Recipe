# Contributing

Thank you for helping improve this repository. Before you contribute, please read **[DISCLAIMER.md](DISCLAIMER.md)** — this is community reference material, not an official Cisco offering, and there is no Cisco support obligation.

## Code of conduct

All participants must follow the **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)**. Violations may result in removal from discussions or blocked contributions at maintainer discretion.

## What to contribute

- **Documentation:** clarifications, corrections, or new recipes that stay aligned with [Cisco DevNet SD-WAN API 20.18](https://developer.cisco.com/docs/sdwan/) and label anything unvalidated in the field.
- **Samples:** small, focused changes to `samples/` that improve safety, readability, or correctness; avoid large refactors unless discussed first.
- **Issues:** reproducible steps, Manager release when relevant, and **no secrets** (redact URLs, hostnames, tokens, and payloads if needed).

## What not to submit

- Real **passwords**, API **tokens**, private **keys**, or production **hostnames** / customer-identifying data.
- **`.env`** files or raw **collector outputs** with live inventory (use synthetic examples).
- Content that contradicts **[DISCLAIMER.md](DISCLAIMER.md)** (e.g. implying Cisco endorsement or support).

## Development setup

```bash
cd samples
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"    # optional: includes ruff if defined in pyproject.toml
```

Sanity check (no network required):

```bash
python3 -m compileall -q samples/src samples/scripts
```

If `ruff` is installed:

```bash
cd samples && ruff check src scripts
```

## Pull requests

1. **One logical change per PR** when possible (one recipe fix, one script fix, etc.).
2. **Describe** what changed and why in the PR body (complete sentences).
3. **Link** related issues if any.
4. Confirm you are comfortable contributing under the **[LICENSE](LICENSE)** terms.

## Documentation style

- Recipes under `docs/recipes/` should keep **YAML frontmatter** (`title`, `release`, `tags`, `apis`, `related_script` where applicable).
- Prefer linking to **DevNet** for canonical API paths rather than duplicating large OpenAPI excerpts.

## Questions

Open a discussion or issue in this repository (or your org’s fork) as maintainers prefer. Do not use Cisco TAC for questions about this repo.
