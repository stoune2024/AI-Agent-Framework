from langchain_core.messages import HumanMessage

from app.agents.graph_state import AgentGraphState


def test_agent_graph_state_contains_messages():

    state: AgentGraphState = {
        "messages": [
            HumanMessage(
                content="Hello",
            ),
        ],
        "iterations": 0,
    }

    assert len(state["messages"]) == 1
    assert state["messages"][0].content == "Hello"
    assert state["iterations"] == 0
