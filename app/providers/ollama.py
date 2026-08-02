from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama


class OllamaProvider:

    def __init__(
        self,
        host: str,
        model: str,
    ):
        self._host = host
        self._model = model

    def get_model(self) -> BaseChatModel:

        return ChatOllama(
            base_url=self._host,
            model=self._model,
        )