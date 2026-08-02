from langchain_core.messages import AIMessage, BaseMessage
from langchain_ollama import ChatOllama


class OllamaLLMClient:
    def __init__(
        self,
        host: str,
        model: str,
    ):
        self._model = ChatOllama(
            base_url=host,
            model=model,
        )

    async def invoke(
        self,
        messages: list[BaseMessage],
    ) -> AIMessage:

        return await self._model.ainvoke(messages)
