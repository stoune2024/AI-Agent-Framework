from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage


@dataclass(slots=True)
class AgentRunMetrics:
    iterations: int
    execution_time: float
    token_usage: Any | None = None


@dataclass(slots=True)
class AgentResult:
    message: AIMessage
    metrics: AgentRunMetrics
