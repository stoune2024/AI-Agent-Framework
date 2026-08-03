from dataclasses import dataclass, field

from langchain_core.messages import BaseMessage


@dataclass(slots=True)
class AgentState:
    messages: list[BaseMessage] = field(default_factory=list)

    iterations: int = 0
