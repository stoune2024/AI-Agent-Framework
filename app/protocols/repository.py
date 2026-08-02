from typing import Protocol

from app.models import MessageRole
from app.schemas import MessageSchema


class ConversationRepositoryProtocol(Protocol):
    async def create_conversation(
        self,
    ): ...

    async def get_conversation(
        self,
        conversation_id: int,
    ): ...

    async def get_messages(
        self,
        conversation_id: int,
    ): ...

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
    ): ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
