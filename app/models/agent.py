from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage

from app.models.llm import TokenUsage


@dataclass(slots=True)
class AgentRunMetrics:
    """
    Метрики одного запуска агента
    """

    iterations: int
    execution_time: float
    token_usage: TokenUsage | None = None


@dataclass(slots=True)
class AgentResult:
    conversation_id: int
    stream: AsyncIterator[str]


@dataclass(slots=True)
class AgentRequest:
    """
    Входные данные для запуска агента
    """

    messages: list[BaseMessage]


@dataclass(slots=True)
class AgentFinalResult:
    """
    Результат выполнения AgentExecutor.
    """

    message: AIMessage
    metrics: AgentRunMetrics


@dataclass(slots=True)
class AgentExecution:
    stream: AsyncIterator[str]

    get_result: Callable[
        [],
        Awaitable[AgentFinalResult],
    ]
