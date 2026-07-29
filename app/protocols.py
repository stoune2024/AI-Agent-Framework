from typing import Protocol, Self

from app.models import ChatMessage, Conversation, MessageRole
from app.schemas import MessageSchema


class ConversationRepositoryProtocol(Protocol):
    async def create_conversation(
        self,
    ) -> Conversation: ...

    async def get_conversation(
        self,
        conversation_id: int,
    ) -> Conversation | None: ...

    async def get_messages(
        self,
        conversation_id: int,
    ) -> list[ChatMessage]: ...

    async def add_message(
        self,
        conversation_id: int,
        role: MessageRole,
        content: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> MessageSchema: ...

    async def get_history_for_llm(
        self,
        conversation_id: int,
    ) -> list[ChatMessage]: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class LLMClientProtocol(Protocol):
    async def chat(
        self,
        messages: list[ChatMessage],
    ) -> StreamResult: ...


class UnitOfWorkProtocol(Protocol):
    conversations: ConversationRepositoryProtocol

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ): ...

    async def commit(self): ...

    async def rollback(self): ...


class UnitOfWorkFactoryProtocol(Protocol):
    def __call__(self) -> UnitOfWorkProtocol: ...
