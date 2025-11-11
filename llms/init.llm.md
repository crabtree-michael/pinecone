# Objective

Pinecone is a research agent for one's own computer. Users can query to find out information about what is on their computer.

As a research agent, it is important that Pinecone prioritizes:
  1. Correct Answers. It validates that all information comes from sources on the computer.
  2. Context Efficiency. It only does as much research as needs to be done. 
  3. User Friendliness. It gracefully handles user requests even during failures.


# Chat Interface

The primary application will be a CLI that displays the master chat record from the orchestrator.


# Methodology

## Multi-Agent Approach

Pinecone is made up of the following agents:

1. Orchestrator - handles user input, distributing tasks
2. Reader - summarizes files
3. Finder - explores file system and identifies overall organization

# Security

No agent should ever make calls that leave the current directory.

## SPAR Framework

Each agent should follow the SPAR framework.

SPAR stands for:

- Sense; agent has means to measure qualities about its environment.
- Plan; agent can make plans based on an objective and what it has sensed.
- Act; agent can act out elements of the plan.
- Reflect; agent can reflect on outcomes reevaluate the plan and inform future action.

# Ollama

All agents should use Ollama as a backing to access llms. All agents should use the `gpt-oss:20b` model.  
