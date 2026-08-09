from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from app.agents.service import AgentService
from app.models.agent import (
    AgentFinalResult,
    AgentRunMetrics,
)


@pytest.mark.asyncio
async def test_agent_service_creates_conversation():

    conversation = MagicMock()
    conversation.id = 42

    conversations = MagicMock()

    conversations.create_conversation = AsyncMock(
        return_value=conversation
    )

    conversations.add_message = AsyncMock()

    conversations.get_history = AsyncMock(
        return_value=[]
    )

    uow = MagicMock()
    uow.conversations = conversations

    uow.__aenter__ = AsyncMock(
        return_value=uow
    )

    uow.__aexit__ = AsyncMock(
        return_value=None
    )

    uow_factory = MagicMock(
        return_value=uow
    )

    executor = MagicMock()

    executor.invoke = AsyncMock(
        return_value=AgentFinalResult(
            message=AIMessage(
                content="425"
            ),
            metrics=AgentRunMetrics(
                iterations=1,
                execution_time=0.1,
                token_usage=None,
            ),
        )
    )

    service = AgentService(
        executor=executor,
        uow_factory=uow_factory,
    )

    result = await service.invoke(
        conversation_id=None,
        message="25 * 17",
    )

    assert result.conversation_id == 42

    conversations.create_conversation.assert_awaited_once()

    conversations.add_message.assert_awaited()