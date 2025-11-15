# Objective

Pinecone is a research agent for one's own computer. Users can query to find out information about what is on their computer.

As a research agent, it is important that Pinecone prioritizes:
  1. Correct Answers. It validates that all information comes from sources on the computer.
  2. Context Efficiency. It only does as much research as needs to be done. 
  3. User Friendliness. It gracefully handles user requests even during failures.

# Multi-Agent System

Pinecone is a multi-agent system comprised of three sub-agents: orchestrator, finder, and reader. The multi-agent system isolates context which should make it more performant than a singe agent in a very large file system.

All agents are backed by an LLM and a chat history that includes tool calls.

The orchestrator contains the primary chat. This chat is a log of communication between agents and the user. Every entry should be prefixed by the calling agent. Here's an example:

```md
[user] What is the purpose of this folder?
[finder] The folder contains a README.md. This would be a good place to start
[reader] README.md describes a system for a web browser
[orchestrator] The purpose of this folder is to be a repository for a web browser.
```

This allows for context isolation. Any entry into the master chat, will be appended to every individual agent's chat history. They only need to the context that other agents determine they need to know.

# OpenRouter

All agents should use OpenRouter to access llms. OpenRouter is an external API that allows agents to maintain a chat with an llm.

The chat endpoint defined [here](https://platform.openai.com/docs/api-reference/chat/create) should be used. If you need more information about the endpoint, please use `curl` to access this resource. The `tools` parameter in the request should be defined.

All agents should use the `gpt-5.1` model.

# Agent Roles

All agents implementation details are defined in `.llm.yaml` details with the agents names in `llms`.

- `orchestrator` coordinates among agents and decides when to respond to the user. It has a single tool `publish` that allows it to publish a message to some or all agents.

- `finder` has context related to the organization of the filesystem. It should direct search. It can use the `shell` togather more information about the filesystem.

- `reader` has context on file contents. It can read files through the `read` tool.

# Safety

The agent should never go above the directory where `pinecone` is run in.

