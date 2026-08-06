from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.protocols.uow import UnitOfWorkProtocol
from app.repository import ConversationRepository


class UnitOfWork(UnitOfWorkProtocol):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self._session_factory = session_factory

    async def __aenter__(self):

        self._session = self._session_factory()

        self.conversations = ConversationRepository(self._session)

        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):

        try:
            if exc_type:
                await self.rollback()

            else:
                await self.commit()

        finally:
            await self._session.close()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()


class UnitOfWorkFactory:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self._session_factory = session_factory

    def __call__(self) -> UnitOfWork:
        return UnitOfWork(self._session_factory)
