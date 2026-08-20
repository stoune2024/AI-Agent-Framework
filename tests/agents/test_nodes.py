from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.agent_graph import AgentGraph


@pytest.mark.asyncio
async def test_call_model_returns_response_and_increments_iterations():

    graph = object.__new__(AgentGraph)

    response = AIMessage(
        content="Hello",
    )

    graph._model = AsyncMock()
    graph._model.ainvoke.return_value = response

    state = {
        "messages": [
            HumanMessage(
                content="Hello",
            ),
        ],
        "iterations": 0,
    }

    result = await graph._call_model(state)

    assert result["messages"] == [response]
    assert result["iterations"] == 1

    graph._model.ainvoke.assert_awaited_once_with(
        state["messages"],
    )


@pytest.mark.asyncio
async def test_call_model_increments_existing_iterations():

    graph = object.__new__(AgentGraph)

    response = AIMessage(
        content="Second response",
    )

    graph._model = AsyncMock()
    graph._model.ainvoke.return_value = response

    state = {
        "messages": [
            HumanMessage(
                content="Hello",
            ),
        ],
        "iterations": 3,
    }

    result = await graph._call_model(state)

    assert result["messages"] == [response]
    assert result["iterations"] == 4


def test_should_continue_when_ai_message_contains_tool_call():

    graph = object.__new__(AgentGraph)

    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "calculator",
                        "args": {
                            "expression": "2 + 2",
                        },
                        "id": "call-1",
                        "type": "tool_call",
                    },
                ],
            ),
        ],
        "iterations": 1,
    }

    result = graph._should_continue(state)

    assert result == "tools"


def test_should_end_when_ai_message_has_no_tool_call():

    graph = object.__new__(AgentGraph)

    state = {
        "messages": [
            AIMessage(
                content="Result: 4",
            ),
        ],
        "iterations": 1,
    }

    result = graph._should_continue(state)

    assert result == "end"


def test_should_end_when_last_message_is_not_ai_message():

    graph = object.__new__(AgentGraph)

    state = {
        "messages": [
            HumanMessage(
                content="Hello",
            ),
        ],
        "iterations": 0,
    }

    result = graph._should_continue(state)

    assert result == "end"
