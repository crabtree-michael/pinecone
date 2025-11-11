# Orchestration Strategy

The orchestrator maintains a master chat between all agents. Each agent manage it's own chats history. 

All responses are sent to all agents. However, all agents are not always expected to respond. The orchestrator can specifically 

The following strategy is used till the orchestrator finds an answer:

1. Orchestrator requests information from one or more available agents
2. Orchestrator waits for agents to respond or timeout
3. Orchestrator reflects on available information and determines either to respond or prompt agents for more information


# SPAR Framework

## Sense

Orchestrator uses the master chat record as its primary sense.

## Plan

Orchestrator should plan which agents it expects to hear back from and wait for their response or timeout.

## Act

Orchestrator either outputs an answer or it queries the other agents again

## Reflect

Orchestrator gets input from responses and better understands its context on that particular problem.


# Prompt

You are an orchestrator agent. You are coordinating with a finder and reader agent to help answer questions about the file system and it's contents. 

finder is responsible for providing orginzaitonal knowledge about the system. 

reader is responsible for providing knowledge about the content of certain files.

You should directly target all your messages. Your messages can target a specific agent or multiple agents. They can 