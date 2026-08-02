from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI


class OpenAIProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
    ):
        self._api_key = api_key
        self._model = model

    def get_model(self) -> BaseChatModel:

        return ChatOpenAI(
            api_key=self._api_key,
            model=self._model,
        )
