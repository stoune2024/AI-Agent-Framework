from typing import Protocol

from langchain_core.language_models import BaseChatModel


class ModelProviderProtocol(Protocol):
    def get_model(self) -> BaseChatModel: ...
