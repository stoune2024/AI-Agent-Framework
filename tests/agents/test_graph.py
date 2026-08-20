from collections.abc import Sequence

import pytest
from langchain_core.messages import AIMessage, BaseMessage

from app.agents.agent_graph import AgentGraph
from app.tools.calculator import calculator
from app.tools.registry import ToolRegistry


class FakeModel:
    def __init__(self, responses: Sequence[AIMessage]):
        self._responses = iter(responses)

    def bind_tools(self, tools):
        return self

    async def ainvoke(
        self,
        messages: list[BaseMessage],
    ) -> AIMessage:
        return next(self._responses)


class FakeProvider:
    def __init__(self, responses: Sequence[AIMessage]):
        self._model = FakeModel(responses)

    def get_model(self):
        return self._model


@pytest.fixture
def calculator_registry():

    return ToolRegistry(
        tools=[
            calculator,
        ],
    )


@pytest.mark.asyncio
async def test_graph_returns_final_response(
    calculator_registry,
):

    provider = FakeProvider(
        [
            AIMessage(
                content="Hello",
            ),
        ],
    )

    graph = AgentGraph(
        provider=provider,
        registry=calculator_registry,
    )

    result = await graph._graph.ainvoke(
        {
            "messages": [],
            "iterations": 0,
        },
    )

    final_message = result["messages"][-1]

    assert isinstance(final_message, AIMessage)
    assert final_message.content == "Hello"
    assert result["iterations"] == 1


@pytest.mark.asyncio
async def test_graph_executes_tool_and_calls_model_again(
    calculator_registry,
):

    first_response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "calculator",
                "args": {
                    "expression": "29 * 17",
                },
                "id": "call-1",
                "type": "tool_call",
            },
        ],
    )

    second_response = AIMessage(
        content="Результат: 493",
    )

    provider = FakeProvider(
        [
            first_response,
            second_response,
        ],
    )

    graph = AgentGraph(
        provider=provider,
        registry=calculator_registry,
    )

    result = await graph._graph.ainvoke(
        {
            "messages": [],
            "iterations": 0,
        },
    )

    messages = result["messages"]

    assert len(messages) == 3

    assert isinstance(messages[0], AIMessage)
    assert messages[0].tool_calls

    assert messages[1].name == "calculator"
    assert messages[1].content == "493"

    assert isinstance(messages[2], AIMessage)
    assert messages[2].content == "Результат: 493"

    assert result["iterations"] == 2


@pytest.mark.asyncio
async def test_graph_routes_directly_to_end(
    calculator_registry,
):

    provider = FakeProvider(
        [
            AIMessage(
                content="Прямой ответ",
            ),
        ],
    )

    graph = AgentGraph(
        provider=provider,
        registry=calculator_registry,
    )

    result = await graph._graph.ainvoke(
        {
            "messages": [],
            "iterations": 0,
        },
    )

    assert result["messages"][-1].content == "Прямой ответ"
    assert result["iterations"] == 1
