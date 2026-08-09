from langchain_core.tools import BaseTool

from app.exceptions import ToolNotFoundError


class ToolRegistry:
    def __init__(
        self,
        tools: list[BaseTool],
    ):
        self._tools = {tool.name: tool for tool in tools}

    @property
    def tools(
        self,
    ) -> list[BaseTool]:

        return list(self._tools.values())

    def get(
        self,
        name: str,
    ) -> BaseTool:

        try:
            return self._tools[name]

        except KeyError as exc:
            raise ToolNotFoundError(f"Tool '{name}' not found.") from exc

    def exists(
        self,
        name: str,
    ) -> bool:

        return name in self._tools
