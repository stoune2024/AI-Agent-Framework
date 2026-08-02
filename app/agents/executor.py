from langchain_core.messages import HumanMessage

from app.providers.base import ModelProviderProtocol
from app.tools.registry import ToolRegistry


class AgentExecutor:
    def __init__(
        self,
        provider: ModelProviderProtocol,
        registry: ToolRegistry,
    ):
        self._model = provider.get_model().bind_tools(registry.tools)

    async def invoke(
        self,
        message: str,
    ):

        response = await self._model.ainvoke([HumanMessage(content=message)])

        print(response.tool_calls)

        return response
