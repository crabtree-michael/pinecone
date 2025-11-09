from __future__ import annotations

"""Prompt and tool specifications for the Pinecone agent."""

ACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "action",
        "description": (
            "Report the next Pinecone step: share your thought, micro-plan, and choose one of "
            "`plan`, `memory`, or `noop`, along with any inputs such as memory text."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "Concise reflection for the current SPAR step.",
                },
                "plan": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ordered list of the next micro-steps.",
                },
                "action": {
                    "type": "string",
                    "enum": ["plan", "memory", "noop"],
                    "description": "Which non-command action to take now.",
                },
                "action_input": {
                    "type": "object",
                    "description": "Inputs for the action (memory body, etc.).",
                }
            },
            "required": ["action", "action_input"],
            "additionalProperties": False,
        },
    },
}

COMMAND_TOOL = {
    "type": "function",
    "function": {
        "name": "command",
        "description": "Execute a sandboxed shell command (ls, cat, rg, grep) within the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["ls", "cat", "rg", "grep"],
                    "description": "The binary to execute.",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Arguments passed to the command.",
                    "default": [],
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
}

RESPOND_TOOL = {
    "type": "function",
    "function": {
        "name": "respond",
        "description": "Provide the final answer to the user and end the session.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The final response text to show the user.",
                }
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    },
}

TOOLS = [COMMAND_TOOL, ACTION_TOOL, RESPOND_TOOL]

SYSTEM_PROMPT = """
You are Pinecone, a SPAR research agent that inspects the user's local computer.
Follow the SPAR loop:
  Sense: review chat history, tool outputs, and memories.
  Plan: outline the minimal next steps.
  Act: call tools to run ls/cat/rg/grep, store new memories, or respond.
  Reflect: after each action, tighten the plan based on outcomes.

Rules:
- Be concise; avoid repeating the full objective every turn.
- Prefer the minimal command needed. When using cat, provide a small context by combining it with 'rg -n' where helpful.
- Store reflections that can help future tasks using the memory action with short markdown text.
- Always use the `command` tool whenever you need to run ls/cat/rg/grep.
- Use the `action` tool for planning, storing memories, or staying idle. Use the `respond` tool to deliver the final answer once the objective is met.
- Do not write free-form text outside these tool calls.
"""
