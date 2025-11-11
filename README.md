# Pinecone

Pinecone is a local-first research agent that lets you ask questions about the files on your computer. It uses a multi-agent architecture with an orchestrator that coordinates finder and reader agents through a master chat shown in the CLI.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) with the `gpt-oss:20b` model installed

## Installation

```bash
pip install -e .
```

## Usage

Run the Pinecone CLI from the project root:

```bash
python -m pinecone
```

Commands inside the CLI:

- Type any question to start an investigation.
- Use `:history` to print the current master chat.
- Use `:reset` to clear all agent state.
- Use `:quit` to exit.

The orchestrator follows the SPAR methodology and will only make shell calls that remain inside the current workspace.
