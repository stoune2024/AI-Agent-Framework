from typing import Protocol, Self

from app.protocols.repository import ConversationRepositoryProtocol


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
