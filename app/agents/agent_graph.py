import asyncio
import time
from collections.abc import AsyncIterator

import structlog
from langchain_core.messages import AIMessage, BaseMessage

from app.agents.graph_state import AgentGraphState
from app.models.agent import (
    AgentExecution,
    AgentFinalResult,
    AgentRunMetrics,
)
from app.providers.base import ModelProviderProtocol
from app.tools.registry import ToolRegistry

logger = structlog.get_logger()


class AgentGraph:
    MAX_ITERATIONS = 10

    def __init__(
        self,
        provider: ModelProviderProtocol,
        registry: ToolRegistry,
    ):
        self._registry = registry

        self._model = provider.get_model().bind_tools(
            registry.tools,
        )

        self._graph = self._build_graph()

    def _build_graph(self):

        from langgraph.graph import END, START, StateGraph
        from langgraph.prebuilt import ToolNode

        graph = StateGraph(AgentGraphState)

        graph.add_node(
            "agent",
            self._call_model,
        )

        graph.add_node(
            "tools",
            ToolNode(self._registry.tools),
        )

        graph.add_edge(
            START,
            "agent",
        )

        graph.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "end": END,
            },
        )

        graph.add_edge(
            "tools",
            "agent",
        )

        return graph.compile()

    async def _call_model(
        self,
        state: AgentGraphState,
    ) -> dict:

        response = await self._model.ainvoke(
            state["messages"],
        )

        return {
            "messages": [response],
        }

    def _should_continue(
        self,
        state: AgentGraphState,
    ) -> str:

        last_message = state["messages"][-1]

        if isinstance(last_message, AIMessage):
            if last_message.tool_calls:
                return "tools"

        return "end"

    async def invoke(
        self,
        messages: list[BaseMessage],
    ) -> AgentExecution:

        started_at = time.perf_counter()

        queue: asyncio.Queue[str | None] = asyncio.Queue()

        result_future = asyncio.get_running_loop().create_future()

        async def run() -> None:

            try:
                result = await self._graph.ainvoke(
                    {
                        "messages": messages,
                    },
                )

                final_message = result["messages"][-1]

                if not isinstance(final_message, AIMessage):
                    raise RuntimeError("Graph finished without AIMessage.")

                execution_time = time.perf_counter() - started_at

                metrics = AgentRunMetrics(
                    iterations=0,
                    execution_time=execution_time,
                    token_usage=None,
                )

                final_result = AgentFinalResult(
                    message=final_message,
                    metrics=metrics,
                )

                if not result_future.done():
                    result_future.set_result(
                        final_result,
                    )

                content = final_message.content

                if isinstance(content, str):
                    await queue.put(content)

            except Exception as exc:
                logger.exception(
                    "agent.graph.failed",
                )

                if not result_future.done():
                    result_future.set_exception(exc)

            finally:
                await queue.put(None)

        task = asyncio.create_task(run())

        async def stream() -> AsyncIterator[str]:

            try:
                while True:
                    token = await queue.get()

                    if token is None:
                        break

                    yield token

                await task

            except asyncio.CancelledError:
                task.cancel()

                raise

        async def get_result() -> AgentFinalResult:

            return await result_future

        return AgentExecution(
            stream=stream(),
            get_result=get_result,
        )
