from typing import Protocol

from langchain_core.messages import AIMessage, BaseMessage


class LLMClientProtocol(Protocol):
    async def invoke(
        self,
        messages: list[BaseMessage],
    ) -> AIMessage: ...
