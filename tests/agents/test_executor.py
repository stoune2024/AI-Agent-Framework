from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from app.agents.executor import AgentExecutor
from app.models.agent import AgentRequest
from app.tools.calculator import calculator
from app.tools.registry import ToolRegistry


class FakeProvider:
    def __init__(self, model):
        self._model = model

    def get_model(self):
        return self._model


@pytest.mark.asyncio
async def test_executor_returns_final_answer():

    model = MagicMock()

    model.bind_tools.return_value = model

    model.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="Hello!",
        )
    )

    provider = FakeProvider(model)

    registry = ToolRegistry([])

    executor = AgentExecutor(
        provider=provider,
        registry=registry,
    )

    request = AgentRequest(
        messages=[],
    )

    result = await executor.invoke(request)

    final_result = await result.get_result()

    assert final_result.message.content == "Hello!"
    assert final_result.metrics.iterations == 0

    model.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_executor_executes_calculator():

    first_response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "calculator",
                "args": {
                    "expression": "25 * 17",
                },
                "id": "call_1",
                "type": "tool_call",
            }
        ],
    )

    second_response = AIMessage(
        content="Результат: 425",
    )

    model = MagicMock()

    model.bind_tools.return_value = model

    model.ainvoke = AsyncMock(
        side_effect=[
            first_response,
            second_response,
        ]
    )

    provider = FakeProvider(model)

    registry = ToolRegistry(
        [
            calculator,
        ]
    )

    executor = AgentExecutor(
        provider=provider,
        registry=registry,
    )

    request = AgentRequest(
        messages=[],
    )

    result = await executor.invoke(request)

    final_result = await result.get_result()

    assert final_result.message.content == "Результат: 425"

    assert final_result.metrics.iterations == 1

    assert model.ainvoke.await_count == 2
