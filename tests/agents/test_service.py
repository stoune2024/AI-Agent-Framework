from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from app.agents.service import AgentService
from app.models.agent import (
    AgentExecution,
    AgentFinalResult,
    AgentRunMetrics,
)


async def empty_stream() -> AsyncIterator[str]:
    if False:
        yield ""


@pytest.mark.asyncio
async def test_agent_service_creates_conversation():

    conversation = MagicMock()
    conversation.id = 42

    conversations = MagicMock()

    conversations.create_conversation = AsyncMock(
        return_value=conversation,
    )

    conversations.add_message = AsyncMock()

    conversations.get_history = AsyncMock(
        return_value=[],
    )

    uow = MagicMock()
    uow.conversations = conversations

    uow.__aenter__ = AsyncMock(
        return_value=uow,
    )

    uow.__aexit__ = AsyncMock(
        return_value=None,
    )

    uow_factory = MagicMock(
        return_value=uow,
    )

    final_result = AgentFinalResult(
        message=AIMessage(
            content="425",
        ),
        metrics=AgentRunMetrics(
            iterations=1,
            execution_time=0.1,
            token_usage=None,
        ),
    )

    execution = AgentExecution(
        stream=empty_stream(),
        get_result=AsyncMock(
            return_value=final_result,
        ),
    )

    graph = MagicMock()

    graph.invoke = AsyncMock(
        return_value=execution,
    )

    service = AgentService(
        graph=graph,
        uow_factory=uow_factory,
    )

    result = await service.invoke(
        conversation_id=None,
        message="25 * 17",
    )

    assert result.conversation_id == 42

    conversations.create_conversation.assert_awaited_once()

    conversations.add_message.assert_any_await(
        conversation_id=42,
        role="user",
        content="25 * 17",
    )

    graph.invoke.assert_awaited_once_with(
        [],
    )


@pytest.mark.asyncio
async def test_agent_service_saves_final_response_after_stream():

    conversations = MagicMock()

    conversations.create_conversation = AsyncMock()

    conversations.add_message = AsyncMock()

    conversations.get_history = AsyncMock(
        return_value=[],
    )

    uow = MagicMock()
    uow.conversations = conversations

    uow.__aenter__ = AsyncMock(
        return_value=uow,
    )

    uow.__aexit__ = AsyncMock(
        return_value=None,
    )

    uow_factory = MagicMock(
        return_value=uow,
    )

    final_result = AgentFinalResult(
        message=AIMessage(
            content="Результат: 425",
        ),
        metrics=AgentRunMetrics(
            iterations=1,
            execution_time=0.1,
            token_usage=None,
        ),
    )

    execution = AgentExecution(
        stream=empty_stream(),
        get_result=AsyncMock(
            return_value=final_result,
        ),
    )

    graph = MagicMock()

    graph.invoke = AsyncMock(
        return_value=execution,
    )

    service = AgentService(
        graph=graph,
        uow_factory=uow_factory,
    )

    result = await service.invoke(
        conversation_id=42,
        message="25 * 17",
    )

    tokens = []

    async for token in result.stream:
        tokens.append(token)

    assert "".join(tokens) == ""

    execution.get_result.assert_awaited_once()

    assert conversations.add_message.await_count == 2

    conversations.add_message.assert_any_await(
        conversation_id=42,
        role="user",
        content="25 * 17",
    )

    conversations.add_message.assert_any_await(
        conversation_id=42,
        role="assistant",
        content="Результат: 425",
        prompt_tokens=None,
        completion_tokens=None,
        total_tokens=None,
    )
