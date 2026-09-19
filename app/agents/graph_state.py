from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentGraphState(TypedDict):
    """
    Runtime state одного запуска AgentGraph.

    messages:
        История сообщений текущего workflow.

    iterations:
        Количество выполненных проходов через agent node.

    tool_calls:
        Количество выполненных tool calls.

    last_tool_result:
        Результат последнего вызванного инструмента.
    """

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    iterations: int
    tool_calls: int
    last_tool_result: str | None
