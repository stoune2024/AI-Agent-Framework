from app.agents.executor import AgentExecutor
from app.agents.models import AgentResult


class AgentService:
    def __init__(
        self,
        executor: AgentExecutor,
    ):
        self._executor = executor

    async def invoke(
        self,
        message: str,
    ) -> AgentResult:

        return await self._executor.invoke(message)
