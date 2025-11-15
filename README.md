# Pinecone

Pinecone is a local-first research agent that answers questions about the files on your own computer. It runs a small multi-agent system that keeps file discovery, file reading, and orchestration responsibilities isolated so each agent only needs the context it can act on.

## Architecture
- **Orchestrator** (`pinecone/agents/orchestrator.py`) is the primary chat surface. It decides when to respond to the user and uses the `publish` tool to ask the other agents for help. Requests run with a five-minute timeout and every response is replayed to the rest of the team to maintain shared context.
- **Finder** (`pinecone/agents/finder.py`) focuses on filesystem structure. It seeds its prompt with a depth-limited tree of the workspace and can execute bounded shell commands through the `shell` tool for targeted discovery.
- **Reader** (`pinecone/agents/reader.py`) is responsible for reading file contents via the `read` tool. It primes itself by loading the first few files in the workspace.
- **LLM backend** (`pinecone/llm.py`) is a thin wrapper over the OpenRouter (OpenAI-compatible) chat completions API. All agents default to the `gpt-5.1` model and require an `OPENROUTER_API_KEY`; `OPENROUTER_BASE_URL` defaults to `https://openrouter.ai/api/v1`.
- **Prompts and specs** live under `pinecone/prompts/` and `llm/`. The `.llm.md` and `.llm.yaml` files document requirements for each agent; follow them when making changes, but do not edit them directly from the CLI workflow.

Tools such as `ShellTool`, `ReadTool`, and `PublishTool` in `pinecone/tools.py` enforce that every operation stays within the Pinecone working directory.

## Requirements
- Python >= 3.9.6
- pip (or another PEP 517 compatible installer)
- [OpenRouter](https://openrouter.ai/) account and API key (exported as `OPENROUTER_API_KEY`)
- macOS/Linux shell (the CLI scripts are zsh/bash friendly)

Install dependencies in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Configure your OpenRouter credentials:

```bash
export OPENROUTER_API_KEY="sk-or-..."
# Optional: override the base URL if you are proxying OpenRouter
# export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
```

Alternatively, place the same key/value pairs inside `pinecone/.env`; the package auto-loads this file on import and sets any variables that are not already defined in the process environment.

## Running the agents
Each agent ships with a standalone CLI entry point (registered in `pyproject.toml` under `[project.scripts]`):

```bash
# Finder-only exploration
pinecone-finder --root /path/to/workspace

# Reader-only inspection
pinecone-reader --root /path/to/workspace

# Full orchestrator (spins up finder + reader sub-agents)
pinecone-orchestrator --root /path/to/workspace
```

Helpful flags:
- `--prompt`, `--finder-prompt`, `--reader-prompt` let you swap in custom prompt templates from `pinecone/prompts/`.
- `--model`, `--finder-model`, `--reader-model` override the default `gpt-5.1` model per agent.

When the orchestrator runs, you interact through a single chat loop. Behind the scenes it forwards research tasks to the finder/reader via the `publish` tool and streams their responses back into the shared transcript before replying to you.

## Repository layout
```
pinecone/
├── agents/             # Orchestrator, finder, reader implementations
├── cli.py              # Finder CLI entry point (others live in reader_cli.py/orchestrator_cli.py)
├── cli_utils.py        # Shared chat loop + prompt loading helpers
├── llm.py              # OpenRouter chat wrapper
├── prompts/            # Prompt templates injected into each agent
├── tools.py            # Tool implementations (shell, read, publish)
└── types.py            # Typed chat + tool payload structures
llm/                    # System design documents (do not modify from CLI workflow)
pyproject.toml          # Package metadata and console script wiring
```

## Development notes
- Always work from an `llm-*` branch and review the `llm/*.llm.md` / `.llm.yaml` files for requirements before coding.
- Keep changes scoped to the Pinecone working directory; the built-in tools enforce this constraint at runtime.
- Prompts are plain Markdown—tweak them to adjust behavior, then rerun the respective CLI to test.
- There are no automated tests yet; exercise the CLI agents manually after changes (start with `pinecone-finder` to ensure filesystem access works).
