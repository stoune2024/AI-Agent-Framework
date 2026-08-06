import time
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, ToolMessage

from app.agents.state import AgentState
from app.models.agent import (
    AgentExecution,
    AgentFinalResult,
    AgentRequest,
    AgentRunMetrics,
)
from app.providers.base import ModelProviderProtocol
from app.tools.registry import ToolRegistry


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

        while self._should_continue(state):
            response = await self._call_model(state)

            state.messages.append(response)

            if not response.tool_calls:
                final_message = response

                async def stream() -> AsyncIterator[str]:

                    yield final_message.content

                async def get_result() -> AgentFinalResult:

                    return AgentFinalResult(
                        message=final_message,
                        metrics=AgentRunMetrics(
                            iterations=state.iterations,
                            execution_time=time.perf_counter() - started_at,
                            token_usage=None,
                        ),
                    )

                return AgentExecution(
                    stream=stream(),
                    get_result=get_result,
                )

            tool_messages = await self._execute_tools(response)

            state.messages.extend(tool_messages)

            state.iterations += 1

        raise RuntimeError("Maximum iterations exceeded.")

    async def _call_model(
        self,
        state: AgentState,
    ) -> AIMessage:

        return await self._model.ainvoke(state.messages)

    async def _execute_tools(
        self,
        response: AIMessage,
    ) -> list[ToolMessage]:

        messages = []

        for call in response.tool_calls:
            tool = self._registry.get(call["name"])

            result = await tool.ainvoke(call["args"])

            messages.append(
                ToolMessage(
                    tool_call_id=call["id"],
                    content=str(result),
                )
            )

        return messages

    def _should_continue(
        self,
        state: AgentState,
    ) -> bool:

        return state.iterations < self.MAX_ITERATIONS
