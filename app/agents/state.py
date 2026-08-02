from dataclasses import dataclass

from langchain_core.messages import BaseMessage


@dataclass
class AgentState:
    messages: list[BaseMessage]
