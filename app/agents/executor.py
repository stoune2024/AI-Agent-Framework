import time

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agents.models import AgentResult, AgentRunMetrics
from app.agents.state import AgentState
from app.providers.base import ModelProviderProtocol
from app.tools.registry import ToolRegistry


class AgentExecutor:
    def __init__(
        self,
        provider: ModelProviderProtocol,
        registry: ToolRegistry,
    ):
        self._model = provider.get_model().bind_tools(registry.tools)
        self._registry = registry
        self.MAX_ITERATIONS = 10

    async def invoke(
        self,
        message: str,
    ) -> AgentResult:

        started_at = time.perf_counter()

        state = AgentState()
        state.messages.append(HumanMessage(content=message))

        while self._should_continue(state):
            response = await self._call_model(state)
            state.messages.append(response)

            if not response.tool_calls:
                metrics = AgentRunMetrics(
                    iterations=state.iterations,
                    execution_time=time.perf_counter() - started_at,
                    token_usage=None,  # добавим позже
                )

                return AgentResult(
                    message=response,
                    metrics=metrics,
                )

            tool_messages = await self._execute_tools(response)

            state.messages.extend(tool_messages)

            state.iterations += 1

        raise RuntimeError("Maximum iterations exceeded.")

    async def _call_model(
        self,
        state: AgentState,
    ):

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
