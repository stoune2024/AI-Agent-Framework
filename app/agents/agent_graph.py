import asyncio
import time
from collections.abc import AsyncIterator

import structlog
from langchain_core.messages import AIMessage, BaseMessage

from app.agents.event_logger import AgentEventLogger
from app.agents.graph_state import AgentGraphState
from app.models.agent import (
    AgentExecution,
    AgentFinalResult,
    AgentRunMetrics,
)
from app.models.llm import TokenUsage
from app.providers.base import ModelProviderProtocol
from app.tools.registry import ToolRegistry

logger = structlog.get_logger()


class AgentGraph:
    MAX_ITERATIONS = 10

    def __init__(
        self,
        provider: ModelProviderProtocol,
        registry: ToolRegistry,
        event_logger: AgentEventLogger | None = None,
    ):
        self._registry = registry
        self._event_logger = event_logger or AgentEventLogger()

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
            "iterations": state["iterations"] + 1,
        }

    def _should_continue(
        self,
        state: AgentGraphState,
    ) -> str:

        last_message = state["messages"][-1]

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            if state["iterations"] >= self.MAX_ITERATIONS:
                logger.warning(
                    "agent.max_iterations",
                    iterations=state["iterations"],
                )

                return "end"

            return "tools"

        return "end"

    async def invoke(
        self,
        messages: list[BaseMessage],
    ) -> AgentExecution:

        started_at = time.perf_counter()

        queue: asyncio.Queue[str | None] = asyncio.Queue()

        result_future: asyncio.Future[AgentFinalResult] = (
            asyncio.get_running_loop().create_future()
        )

        async def run() -> None:

            token_usage = TokenUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            )

            try:
                final_message: AIMessage | None = None
                iterations = 0

                async for event in self._graph.astream_events(
                    {
                        "messages": messages,
                        "iterations": 0,
                    },
                    version="v2",
                ):
                    await self._event_logger.handle(event)

                    event_name = event.get("event")

                    if event_name == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]

                        content = chunk.content

                        if isinstance(content, str) and content:
                            await queue.put(content)

                    elif event_name == "on_chat_model_end":
                        usage = self._extract_token_usage(event)

                        if usage is not None:
                            token_usage.prompt_tokens += usage.prompt_tokens or 0

                            token_usage.completion_tokens += (
                                usage.completion_tokens or 0
                            )

                            token_usage.total_tokens += usage.total_tokens or 0

                    elif event_name == "on_chain_end":
                        output = event.get("data", {}).get("output")

                        if not isinstance(output, dict):
                            continue

                        output_messages = output.get("messages")

                        if output_messages:
                            candidate = output_messages[-1]

                            if isinstance(candidate, AIMessage):
                                final_message = candidate

                        output_iterations = output.get("iterations")

                        if isinstance(output_iterations, int):
                            iterations = output_iterations

                if final_message is None:
                    raise RuntimeError(
                        "Graph finished without AIMessage.",
                    )

                execution_time = time.perf_counter() - started_at

                metrics = AgentRunMetrics(
                    iterations=iterations,
                    execution_time=execution_time,
                    token_usage=token_usage,
                )

                logger.info(
                    "agent.completed",
                    iterations=metrics.iterations,
                    execution_time=metrics.execution_time,
                    token_usage={
                        "prompt_tokens": token_usage.prompt_tokens,
                        "completion_tokens": token_usage.completion_tokens,
                        "total_tokens": token_usage.total_tokens,
                    },
                )

                final_result = AgentFinalResult(
                    message=final_message,
                    metrics=metrics,
                )

                if not result_future.done():
                    result_future.set_result(final_result)

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

    @staticmethod
    def _extract_token_usage(
        event: dict,
    ) -> TokenUsage | None:

        output = event.get("data", {}).get("output")

        if output is None:
            return None

        usage = getattr(
            output,
            "usage_metadata",
            None,
        )

        if not usage:
            return None

        return TokenUsage(
            prompt_tokens=usage.get("input_tokens"),
            completion_tokens=usage.get("output_tokens"),
            total_tokens=usage.get("total_tokens"),
        )
