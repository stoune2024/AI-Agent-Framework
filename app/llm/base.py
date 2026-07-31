from typing import Protocol

from langchain_core.messages import BaseMessage
from langchain_core.messages import AIMessage


class LLMClientProtocol(Protocol):

    async def invoke(
        self,
        messages: list[BaseMessage],
    ) -> AIMessage:
        ...