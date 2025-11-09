# Pinecone Research Agent

Local SPAR-style research agent that uses a nearby Ollama model to examine files on your computer using limited shell tools.

## Requirements
- Python 3.9+
- [Ollama](https://ollama.com) running locally with a chat-capable model (default `llama3`).

## Quick start
```bash
pip install -e .
pinecone-agent "Summarize findings in llms/init.llm.md"
```

Environment overrides:
- `PINECONE_MODEL` – Ollama model name.
- `PINECONE_ROOT` – directory the agent can inspect (defaults to current working directory).
- `PINECONE_MEMORY` – directory for markdown memories (defaults to `<root>/memory`).
- `PINECONE_MAX_STEPS`, `PINECONE_MAX_TOOL_CHARS`, `PINECONE_TEMPERATURE` to adjust behavior.

The agent loops through SPAR steps, asking the LLM for structured JSON actions. It can run `ls`, `cat`, `rg`, or `grep`, store short reflections as markdown memories, and responds with answers citing local files.
