# Objective

Pinecone is a research agent for one's own computer. Users can query to find out information about what is on their computer.

As a research agent, it is important that Pinecone prioritizes:
  1. Correct Answers. It validates that all information comes from sources on the computer.
  2. Context Efficiency. It only does as much research as needs to be done. 
  3. User Friendliness. It gracefully handles user requests even during failures.


# Methodology

## SPAR Framework

Pinecone should follow the SPAR framework for agent-based AI.

SPAR stands for:

- Sense; agent has means to measure qualities about its environment.
- Plan; agent can make plans based on an objective and what it has sensed.
- Act; agent can act out elements of the plan.
- Reflect; agent can reflect on outcomes reevaluate the plan and inform future action.

How Pinecone accomplishes each is described below.

## Sense

Pinecone can sense in three ways:
  1. Chat-interface; A chat UX allows users to define Pinceone's objectives.
  2. Tooling; Pinecone can use basic bash commands to gather information about the computer system. It has access to ls, cat, and grep.
  3. Memory. Pinecone has the ability to read memories about previous actions taken.

## Plan

Pinecone will recursively call a large-language model to reason and form plans.

## Act

Pinecone will prompt the large-language model to issue commands that invoke tools. These tools include:
1. The agent should be able to perform bash actions to find out information about its environment.
2. The agent should be able to issue respond commands when it has found an answer.
3. The agent should be able to issue memory commands to form memories.

## Reflect

Pinecone will reflect after each action. It can remember examples of effects on its environment. It can use the memory command to append a Markdown file to it's memory folder. The markdown file contains the action to take and the outcome. 