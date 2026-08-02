# Security Agent

Security Agent is a small CLI orchestrator for running DeepAgents workflows over
tools exposed by an MCP server. It takes a natural-language request, loads a
bounded set of MCP tools over stdio, creates a supervisor agent plus one worker
subagent pool, and returns the final assistant response to stdout.

The project is intentionally thin: this repository owns the orchestration,
configuration, prompts, and MCP connection layer. The actual security tooling is
provided by whichever MCP server you configure at runtime.

## What It Does

- Accepts a user request from CLI arguments or stdin.
- Loads runtime settings from environment variables and `.env`.
- Connects to one MCP server using `langchain-mcp-adapters`.
- Limits the number of tools registered with the agent using `MAX_TOOLS`.
- Builds a DeepAgents supervisor with QuickJS workflow execution.
- Registers a configurable pool of generic worker subagents, defaulting to 10,
  that can choose among the shared MCP tools and run independent tasks
  concurrently.
- Prints only the final response to stdout, keeping operational details in
  logs.

## Project Layout

```text
.
├── main.py             # CLI entrypoint and DeepAgents assembly
├── config.py           # Environment parsing and validated settings
├── prompts.py          # Supervisor and worker system prompts
├── mcp/
│   ├── __init__.py
│   └── connect.py      # Async MCP connection and tool loading
├── test_main.py        # CLI regression tests
├── test_mcp.py         # Manual MCP connectivity smoke test
├── pyproject.toml      # Project metadata and dependencies
├── requirements.txt    # pip-compatible dependency list
└── uv.lock             # Locked dependency graph for uv users
```

## Requirements

- Python 3.11+
- An OpenRouter-compatible API key for the configured chat model
- A working MCP server command that exposes the tools you want the agent to use

Install with either `pip`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Or with `uv`:

```bash
uv sync
```

## Configuration

Create a `.env` file in the repository root. `.env` is intentionally ignored by
git.

```bash
OPENROUTER_API_KEY=your_openrouter_key

# Model passed to LangChain's OpenRouter chat model initialization.
MODEL=anthropic:claude-sonnet-4-6

# MCP server process configuration.
MCP_SERVER_NAME=security
MCP_COMMAND=python3
MCP_ARGS='["/absolute/path/to/your_mcp_server.py", "--server", "http://localhost:8888"]'

# Runtime behavior.
MAX_TOOLS=50
SUBAGENT_COUNT=10
LOG_LEVEL=INFO
```

`MCP_ARGS` can be either a JSON string array, as shown above, or a shell-style
argument string. JSON is preferred because it avoids quoting surprises.

## Usage

Pass the request as arguments:

```bash
python main.py "run a scoped security assessment for https://example.com"
```

Or pipe it through stdin:

```bash
echo "summarize the available MCP security tools" | python main.py
```

The CLI exits with:

- `0` when the agent completes successfully
- `1` when configuration, MCP connection, or agent execution fails
- `130` when interrupted with `Ctrl-C`

## How It Works

1. `main.py` parses the user request from argv or stdin.
2. `config.py` loads and validates the model, MCP command, MCP args, tool limit,
   server name, and log level.
3. `MCPToolLoader` starts a stdio MCP session and loads LangChain-compatible
   tools.
4. `build_agent()` creates the supervisor DeepAgent and disables the default
   DeepAgents subagent profile so only the configured worker pool is available.
5. The supervisor can use QuickJS to create dynamic workflows, delegate focused
   tasks across the worker pool with `Promise.all`, and reconcile the final
   answer.

## Testing

Run the fast CLI regression tests:

```bash
python -m unittest test_main.py
```

Run a syntax check over the root Python files:

```bash
python -m py_compile main.py config.py prompts.py mcp/connect.py test_mcp.py test_main.py
```

`test_mcp.py` is a manual smoke test for MCP connectivity. It assumes your MCP
server path and service URL are available in the local environment, so it is not
part of the default fast test path.

## Responsible Use

Only run security assessments against systems you own or are explicitly
authorized to test. Keep scope, rate limits, credentials, and logging
requirements clear before connecting powerful MCP tools to the agent.

## Troubleshooting

- `MCP_COMMAND is required`: set `MCP_COMMAND` in `.env`.
- `MCP_ARGS JSON must be a list of strings`: use a valid JSON array or switch to
  shell-style arguments.
- `MAX_TOOLS must be greater than zero`: set `MAX_TOOLS` to a positive integer.
- `SUBAGENT_COUNT must be greater than zero`: set `SUBAGENT_COUNT` to a
  positive integer.
- Missing import errors: install dependencies with `pip install -r
  requirements.txt` or `uv sync`.
- No MCP tools are available: verify the MCP server command works by itself, then
  run `test_mcp.py` as a local smoke test.
