# Repository Guidelines

## Repository Purpose
OpenHands CLI is a **headless, single-task runner** for the OpenHands agent, shipped
as a standalone PyInstaller binary. You give it one task (via `--task` or `--file`),
it drives the agent to completion, prints a conversation summary, and exits.

> History: this repo used to ship a full Textual TUI (with `openhands web`,
> `openhands serve`, ACP, cloud login, interactive conversations). That UX has been
> **removed** and replaced by the headless runner. Ignore any TUI-era references you
> find in stale files (see "Legacy remnants" below).

### References
- Agent-sdk example: https://github.com/All-Hands-AI/agent-sdk/blob/main/examples/hello_world.py
- If you need to compare with upstream OpenHands code, use `$GITHUB_TOKEN` for access.

## What the CLI does

Single console script: `openhands = "openhands_cli.entrypoint:main"` (see
`pyproject.toml` `[project.scripts]`). There are **no subcommands**. Flags:

- `--task, -t <text>`: task text to run
- `--file, -f <path>`: read task text from a file
- `--resume <conversation-id>`: resume an existing conversation
- `--llm-approve`: enable the LLM security analyzer (only high-risk actions are
  confirmed; default is auto-approve everything)
- `--override-with-envs`: take LLM settings from `LLM_API_KEY` / `LLM_BASE_URL` /
  `LLM_MODEL` env vars (ignored by default)
- `--version, -v`

`--task` or `--file` is required; otherwise the parser errors.

## Project Structure & Module Organization
- `openhands_cli/`: core code. Current modules:
  - `entrypoint.py`: parses args, loads `.env`, runs one task, prints summary.
  - `argparsers/`: argument parser (`main_parser.py`, `util.py`).
  - `task_runner.py`: headless executor — picks the confirmation policy, drives the
    SDK conversation, returns the conversation id.
  - `setup.py`: builds the conversation / agent spec, applies LLM analyzer and hooks.
  - `stores/`: agent spec storage, settings, tool resolution.
  - `mcp/`: `mcp_utils.py` only — loads MCP server config from JSON.
  - `shared/`: helpers (e.g. conversation summary extraction).
  - `locations.py`: persistence path helpers (`PERSISTENCE_DIR`, etc.).
  - `utils.py`: LLM config and tool helpers.
  - `skills/`: vendored public skills (SKILL.md + references + scripts), shipped as
    data and bundled into the binary. Treated as third-party content — do not lint or
    reformat (ruff `extend-exclude` in `pyproject.toml`).
  - Keep new modules snake_case and colocate tests under `tests/`.
- `vendor/`: vendored `openhands-sdk` / `openhands-tools` source (see next section).
- `tests/`: pytest suite (mirrors source layout).
- `hooks/`: PyInstaller runtime hooks (`rthook_profile_imports.py`).
- Tooling & packaging: `Makefile`, `build.sh` / `build.py` (PyInstaller),
  `openhands-cli.spec` (frozen binary config), `uv.lock`.

## Setup, Build, and Development Commands
This repo uses **uv** for dependency management and tooling. Use `uv` 0.11.6 or newer.
Avoid `pip install ...` directly.

- install dependencies: `make install` (runs `uv sync`)
- install dev dependencies: `make install-dev` (runs `uv sync --group dev`)
- build dev env + pre-commit hooks: `make build`
- lint (ruff): `make lint`
- format (ruff): `make format`
- type-check: `uv run pyright`
- run the CLI (headless): `uv run openhands --task "..."` (or `-f task.md`). Note:
  `make run` runs `uv run openhands` with no args and will error asking for a task —
  pass flags directly instead.
- run tests: `make test` (runs `uv run pytest --ignore=tests/snapshots`)
- build the standalone binary: `./build.sh --install-pyinstaller` (first time, installs
  PyInstaller), then `./build.sh` for subsequent builds. Output: `dist/openhands`
  (single-file executable). Smoke-test with `./dist/openhands --help`.

## Vendored OpenHands SDK (`vendor/`)

The `openhands-sdk` and `openhands-tools` packages are **vendored as source** under
`vendor/` instead of being pulled from PyPI, so the team can modify SDK internals,
review those changes in this repo's CR flow, and compile them into the binary.

- **Location**: `vendor/openhands-sdk/`, `vendor/openhands-tools/` — source lifted
  from upstream `github.com/OpenHands/software-agent-sdk` tag `v1.19.1` (nested
  `.git` and the rest of the upstream monorepo scaffolding were removed; these are
  now plain tracked directories in this repo).
- **Wiring**: `pyproject.toml` `[tool.uv.sources]` points both packages at their
  vendored paths with `editable = true`. `uv sync` installs them as editable, so
  edits under `vendor/` take effect immediately without reinstalling.
- **Packaging**: `openhands-cli.spec` adds the two vendor roots to `pathex`. This is
  required because uv installs editable packages via a setuptools *strict-editable*
  import finder (`__editable___openhands_sdk_*_finder.py`) that PyInstaller cannot
  follow; without the `pathex` entries the frozen binary raises
  `ImportError: cannot import name 'Agent' from 'openhands.sdk' (unknown location)`.
  Prompt templates (`.j2`) and other data still come in via the existing
  `collect_data_files('openhands.sdk' / 'openhands.tools')` calls.

### Workflow for changing the SDK

1. Edit source under `vendor/openhands-sdk/` or `vendor/openhands-tools/`.
2. Verify at source level: `uv run openhands --task "..."`.
3. Rebuild the binary: `./build.sh` → `dist/openhands`.
4. Smoke-test the binary: `./dist/openhands --help` (should print the correct
   `OpenHands SDK vX.Y.Z` banner and no `ImportError`).
5. Commit `vendor/`, `pyproject.toml`, `uv.lock`, and (if touched) `openhands-cli.spec`
   together; SDK and CLI changes are reviewed in the same PR.

### Version bumps

`vendor/*/pyproject.toml` `version` and the `openhands-sdk==` / `openhands-tools==`
pins in the root `pyproject.toml` must stay in sync (both currently `1.19.1`).
Changing one without the other makes `uv sync` unsatisfiable.

## Development Guidelines

### Linting Requirements
**Before any commit, run `make lint` and only commit after it passes.** Run it before
every commit (not after) to avoid CI failures.

### Typing Requirements
Prefer modern typing syntax (`X | None` over `Optional[X]`). Type-check with
`uv run pyright`; prefer type hints on new functions and public interfaces.

### Documentation Guidelines
- Don't add new root-level `.md` files or "summary updates" to `README.md` unless
  explicitly requested — use this `AGENTS.md` for repo guidance.

## Coding Style & Naming Conventions
- Python 3.12, ruff formatting (88-char line limit, double quotes).
- Ruff enforced rules: pycodestyle, pyflakes, isort, pyupgrade, unused-arg checks
  (tests allow fixture-style args), and guards against mutable defaults.
- Keep modules/dirs snake_case; classes in CapWords; user-facing flags kebab-case.

## Testing Guidelines
- Unit/integration tests live under `tests/` (mirrors `openhands_cli/`); run via
  `make test`.
- Pytest discovery: files `test_*.py`, classes `Test*`, functions `test_*`. Use
  `@pytest.mark.integration` for costly flows.
- Add fixtures in `tests/conftest.py` when shared.
- `tests/test_cli_help.py` covers `--help` output; `tests/test_main.py` covers arg
  parsing and the headless run path.
- Run `make test` before PRs.

## Commit & Pull Request Guidelines
- Follow the repo's pattern: `<scope>: <concise message>` (see `git log`), where scope
  is the touched area (e.g., `fix`, `mcp`, `skills`, `headless`).
- Keep commits focused; include tests and formatting in the same change when practical.
- PRs should describe behavior changes, list key commands run (tests/build), and link
  related issues.
- Check in `uv.lock` changes when dependency versions move; avoid committing secrets or
  local config.
- Before opening a PR:
  1. `make lint`
  2. `make test`
  3. If you touched packaging or the binary (`openhands-cli.spec`, `build.*`, `vendor/`,
     `mcp/`, entrypoint): run `./build.sh` and smoke-test `./dist/openhands --help`.

## Security & Configuration Tips
- Do not embed API keys or endpoints in code; rely on runtime env vars / config.
- When packaging, verify no sensitive files are included in `dist/`; adjust
  `openhands-cli.spec` if new assets are added.

## Legacy remnants (TUI era — do not trust)

The refactor to headless left some dead scaffolding behind. Treat these as stale until
they are cleaned up; do not use them as a model for new work:

- **Unused deps** in `pyproject.toml`: `textual`, `textual-autocomplete`,
  `textual-serve`, and dev dep `pytest-textual-snapshot` are no longer imported by
  `openhands_cli/` code.
- **Stale Makefile targets**: `make run-watch` (calls `scripts/run_watch.py`),
  `make test-snapshots` (`tests/snapshots/` has no snapshots), `make test-binary`
  (`tui_e2e/` does not exist), `make test-all`. These reference removed features.
- **Stale scripts/tests**: `scripts/acp/` (ACP was removed); some files under `tests/`
  (e.g. `tests/cloud/`, and mocks referencing `openhands_cli.tui.*`) target deleted
  modules and may fail — prefer `make test` scoped to current modules.
