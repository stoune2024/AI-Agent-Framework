from langchain_core.tools import BaseTool


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

        return self._tools[name]

    def exists(
        self,
        name: str,
    ) -> bool:

        return name in self._tools
