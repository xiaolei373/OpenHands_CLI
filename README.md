<a name="readme-top"></a>

<div align="center">
  <h1>OpenHands CLI (Headless)</h1>
  <p><i>A headless, single-task runner for the OpenHands agent — powered by a vendored <a href="https://github.com/OpenHands/software-agent-sdk">OpenHands Software Agent SDK</a>.</i></p>
</div>

<hr>

Give it one task, it drives the agent to completion, prints a conversation summary,
and exits. Built for CI pipelines, scripts, and automation. Ships either as a Python
package run through `uv`, or as a single standalone binary.

> This is a customized fork. The OpenHands SDK is vendored under `vendor/` so we can
> modify it directly and compile it into the binary. See `AGENTS.md` for the full
> developer guide.

## Installation

### From source (development)

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/) 0.11.6+.

```bash
uv sync                       # install dependencies (vendored SDK as editable)
uv run openhands --task "..." # run
```

### Standalone binary

Build a single-file executable with PyInstaller:

```bash
./build.sh --install-pyinstaller   # first build (installs pyinstaller)
./build.sh                         # subsequent builds
./dist/openhands --help            # smoke test
```

Optionally put it on your PATH:

```bash
sudo install -m755 dist/openhands /usr/local/bin/openhands
```

## Usage

The CLI runs exactly one task and exits. `--task` or `--file` is required.

```bash
# Run a task
openhands --task "Fix the failing test in auth.py"

# Read the task from a file
openhands --file task.md

# Resume a previous conversation and continue
openhands --resume <conversation-id> --task "continue"
```

### Options

| Flag | Description |
| --- | --- |
| `-t`, `--task <text>` | Task text to run |
| `-f`, `--file <path>` | Read the task text from a file |
| `--resume <id>` | Resume an existing conversation by ID |
| `--llm-approve` | Enable the LLM security analyzer (only high-risk actions are confirmed). Without it, all actions are auto-approved |
| `--override-with-envs` | Apply `LLM_API_KEY` / `LLM_MODEL` / `LLM_BASE_URL` from the environment (ignored by default, not persisted) |
| `-v`, `--version` | Print the version and exit |

On completion the CLI prints the conversation ID and a hint to resume it:

```
Conversation ID: f4a88f49...
Hint: run openhands --resume f4a88f49-... to resume this conversation.
```

## Configuration

### LLM settings

By default `LLM_API_KEY`, `LLM_MODEL`, and `LLM_BASE_URL` in the environment are
**ignored**. Pass `--override-with-envs` to apply them for the run. A `.env` file in
the current directory is loaded automatically on startup.

### Paths (overridable via environment)

| Env var | Default | Purpose |
| --- | --- | --- |
| `OPENHANDS_PERSISTENCE_DIR` | `~/.openhands` | Agent settings (`agent_settings.json`) and `mcp.json` |
| `OPENHANDS_CONVERSATIONS_DIR` | `~/.openhands/conversations` | Stored conversations (used by `--resume`) |
| `OPENHANDS_WORK_DIR` | current directory | Where the agent operates |

### MCP servers

Extend the agent with [Model Context Protocol](https://modelcontextprotocol.io/)
servers by editing `~/.openhands/mcp.json`. Enabled servers are attached to the agent
automatically at runtime. Example:

```json
{
  "mcpServers": {
    "tavily": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.tavily.com/mcp/?tavilyApiKey=<key>"],
      "enabled": true
    }
  }
}
```

## Development

```bash
make install        # uv sync
make install-dev    # uv sync --group dev
make lint           # ruff check openhands_cli/
make format         # ruff format
make test           # pytest (excludes tests/snapshots)
uv run pyright      # type check
```

Modifying the SDK: edit source under `vendor/openhands-sdk/` or
`vendor/openhands-tools/` (editable, changes take effect immediately), verify with
`uv run openhands --task "..."`, then rebuild the binary with `./build.sh`. See
`AGENTS.md` for details.

## License

MIT License — see [LICENSE](LICENSE) for details.
