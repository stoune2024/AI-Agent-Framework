from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI


class OpenAILLMClient:
    def __init__(
        self,
        api_key: str,
        model: str,
    ):

        self._model = ChatOpenAI(
            api_key=api_key,
            model=model,
        )

    async def invoke(
        self,
        messages: list[BaseMessage],
    ) -> AIMessage:

        return await self._model.ainvoke(messages)
