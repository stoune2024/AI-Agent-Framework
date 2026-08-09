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
    """
    Результат работы AgentService.

    """

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
    Финальный результат выполнения AgentExecutor.
    """

    message: AIMessage
    metrics: AgentRunMetrics


@dataclass(slots=True)
class AgentExecution:
    """
        Результат запуска AgentExecutor.

    stream:
        Поток ответа для HTTP-клиента.

    get_result:
        Получение финального результата и метрик
        после завершения выполнения.

    """

    stream: AsyncIterator[str]

    get_result: Callable[
        [],
        Awaitable[AgentFinalResult],
    ]
