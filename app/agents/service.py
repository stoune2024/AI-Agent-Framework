class AgentService:
    def __init__(
        self,
        executor,
    ):
        self._executor = executor

    async def invoke(
        self,
        message: str,
    ):

        response = await self._executor.invoke(message)

        print(response.tool_calls)

        return response.content
