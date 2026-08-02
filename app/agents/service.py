from langchain_core.messages import HumanMessage

from app.protocols.llm import LLMClientProtocol


class AgentService:
    def __init__(
        self,
        llm: LLMClientProtocol,
    ):
        self._llm = llm

    async def invoke(self, message: str) -> str:

        response = await self._llm.invoke([HumanMessage(content=message)])

        return response.content
