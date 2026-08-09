import asyncio
import time
from collections.abc import AsyncIterator

import structlog
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

from app.agents.state import AgentState
from app.exceptions import (
    MaxIterationsExceededError,
    ToolExecutionError,
    ToolNotFoundError,
)
from app.models.agent import (
    AgentExecution,
    AgentFinalResult,
    AgentRequest,
    AgentRunMetrics,
)
from app.providers.base import ModelProviderProtocol
from app.tools.registry import ToolRegistry

logger = structlog.get_logger()


class AgentExecutor:
    MAX_ITERATIONS = 10

    def __init__(
        self,
        provider: ModelProviderProtocol,
        registry: ToolRegistry,
    ):
        self._model = provider.get_model().bind_tools(registry.tools)
        self._registry = registry

    async def invoke(
        self,
        request: AgentRequest,
    ) -> AgentExecution:

        started_at = time.perf_counter()

        state = AgentState()
        state.messages.extend(request.messages)

        queue: asyncio.Queue[str | None] = asyncio.Queue()

        result_future: asyncio.Future[AgentFinalResult] = (
            asyncio.get_running_loop().create_future()
        )

        async def run() -> None:
            try:
                logger.info(
                    "agent.started",
                    message_count=len(state.messages),
                )

                while self._should_continue(state):
                    response = await self._stream_model(
                        state,
                        queue,
                    )

                    state.messages.append(response)

                    logger.info(
                        "agent.model_response",
                        iteration=state.iterations,
                        tool_calls=len(response.tool_calls),
                    )

                    if not response.tool_calls:
                        execution_time = time.perf_counter() - started_at

                        metrics = AgentRunMetrics(
                            iterations=state.iterations,
                            execution_time=execution_time,
                            token_usage=None,
                        )

                        logger.info(
                            "agent.completed",
                            iterations=state.iterations,
                            execution_time=execution_time,
                        )

                        result = AgentFinalResult(
                            message=response,
                            metrics=metrics,
                        )

                        if not result_future.done():
                            result_future.set_result(result)

                        return

                    tool_messages = await self._execute_tools(response)

                    state.messages.extend(tool_messages)

                    state.iterations += 1

                error = MaxIterationsExceededError("Maximum agent iterations exceeded.")

                logger.error(
                    "agent.max_iterations",
                    iterations=state.iterations,
                )

                if not result_future.done():
                    result_future.set_exception(error)

            except Exception as exc:
                logger.exception(
                    "agent.failed",
                )

                if not result_future.done():
                    result_future.set_exception(exc)

                raise

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

    async def _stream_model(
        self,
        state: AgentState,
        queue: asyncio.Queue[str | None],
    ) -> AIMessage:

        message: AIMessageChunk | None = None

        async for event in self._model.astream_events(
            state.messages,
            version="v2",
        ):
            event_name = event["event"]

            if event_name != "on_chat_model_stream":
                continue

            chunk = event["data"]["chunk"]

            if not isinstance(chunk, AIMessageChunk):
                continue

            if message is None:
                message = chunk
            else:
                message = message + chunk

            content = chunk.content

            if isinstance(content, str) and content:
                await queue.put(content)

        if message is None:
            raise RuntimeError("LLM returned no response.")

        return AIMessage(
            content=message.content,
            additional_kwargs=message.additional_kwargs,
            response_metadata=message.response_metadata,
            tool_calls=message.tool_calls,
            invalid_tool_calls=message.invalid_tool_calls,
        )

    async def _execute_tools(
        self,
        response: AIMessage,
    ) -> list[ToolMessage]:

        messages: list[ToolMessage] = []

        for call in response.tool_calls:
            tool_name = call["name"]
            arguments = call["args"]
            tool_call_id = call["id"]

            logger.info(
                "tool.call",
                tool=tool_name,
                arguments=arguments,
                tool_call_id=tool_call_id,
            )

            try:
                tool = self._registry.get(tool_name)

            except ToolNotFoundError:
                logger.error(
                    "tool.not_found",
                    tool=tool_name,
                    arguments=arguments,
                    tool_call_id=tool_call_id,
                )
                raise

            try:
                result = await tool.ainvoke(arguments)

            except Exception as exc:
                logger.exception(
                    "tool.execution_failed",
                    tool=tool_name,
                    arguments=arguments,
                    tool_call_id=tool_call_id,
                )

                raise ToolExecutionError(
                    f"Tool '{tool_name}' execution failed."
                ) from exc

            logger.info(
                "tool.result",
                tool=tool_name,
                result=str(result),
                tool_call_id=tool_call_id,
            )

            messages.append(
                ToolMessage(
                    tool_call_id=tool_call_id,
                    content=str(result),
                    name=tool_name,
                )
            )

        return messages

    def _should_continue(
        self,
        state: AgentState,
    ) -> bool:

        return state.iterations < self.MAX_ITERATIONS
