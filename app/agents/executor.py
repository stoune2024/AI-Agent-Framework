import time
from collections.abc import AsyncIterator

import structlog
from langchain_core.messages import AIMessage, ToolMessage

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

        logger.info(
            "agent.started",
            message_count=len(state.messages),
        )

        while self._should_continue(state):
            response = await self._call_model(state)

            state.messages.append(response)

            logger.info(
                "agent.model_response",
                iteration=state.iterations,
                tool_calls=len(response.tool_calls),
            )

            if not response.tool_calls:
                final_message = response

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

                async def stream() -> AsyncIterator[str]:

                    content = final_message.content

                    if isinstance(content, str):
                        yield content

                async def get_result() -> AgentFinalResult:

                    return AgentFinalResult(message=final_message, metrics=metrics)

                return AgentExecution(
                    stream=stream(),
                    get_result=get_result,
                )

            tool_messages = await self._execute_tools(response)

            state.messages.extend(tool_messages)

            state.iterations += 1

        logger.error(
            "agent.max_iterations",
            iterations=state.iterations,
        )

        raise MaxIterationsExceededError("Maximum agent iterations exceeded.")

    async def _call_model(
        self,
        state: AgentState,
    ) -> AIMessage:

        return await self._model.ainvoke(state.messages)

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
                tool = self._registry.get(call["name"])

            except ToolNotFoundError:
                logger.error(
                    "tool.not_found",
                    tool=tool_name,
                    arguments=arguments,
                    tool_call_id=tool_call_id,
                )
                raise

            try:
                result = await tool.ainvoke(call["args"])

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
                    tool_call_id=tool_call_id, content=str(result), name=tool_name
                )
            )

        return messages

    def _should_continue(
        self,
        state: AgentState,
    ) -> bool:

        return state.iterations < self.MAX_ITERATIONS
