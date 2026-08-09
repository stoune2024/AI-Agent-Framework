import json

import pytest
from langchain_core.messages import AIMessageChunk, HumanMessage

from app.agents.executor import AgentExecutor
from app.models.agent import AgentRequest


class FakeCalculator:
    name = "calculator"

    def __init__(self):
        self.calls = []

    async def ainvoke(self, arguments):
        self.calls.append(arguments)
        return "384"


class FakeRegistry:
    def __init__(self, calculator):
        self.calculator = calculator
        self.tools = [calculator]

    def get(self, name):
        assert name == "calculator"
        return self.calculator


class FakeModel:
    def __init__(self):
        self.calls = 0

    def bind_tools(self, tools):
        self.tools = tools
        return self

    async def astream_events(self, messages, version="v2"):
        self.calls += 1

        # Первый вызов LLM:
        # модель решает воспользоваться calculator.
        if self.calls == 1:
            yield {
                "event": "on_chat_model_stream",
                "data": {
                    "chunk": AIMessageChunk(
                        content="",
                        tool_call_chunks=[
                            {
                                "name": "calculator",
                                "args": json.dumps({"expression": "24 * 16"}),
                                "id": "call-1",
                                "index": 0,
                            }
                        ],
                    )
                },
            }

            return

        # Второй вызов LLM:
        # после получения ToolMessage модель формирует
        # финальный текстовый ответ.
        if self.calls == 2:
            text = "Результат: 384"

            for token in ("Результат: ", "384"):
                yield {
                    "event": "on_chat_model_stream",
                    "data": {
                        "chunk": AIMessageChunk(
                            content=token,
                        )
                    },
                }

            return


class FakeProvider:
    def __init__(self, model):
        self.model = model

    def get_model(self):
        return self.model


@pytest.fixture
def calculator():
    return FakeCalculator()


@pytest.fixture
def model():
    return FakeModel()


@pytest.fixture
def executor(model, calculator):
    registry = FakeRegistry(calculator)

    return AgentExecutor(
        provider=FakeProvider(model),
        registry=registry,
    )


@pytest.mark.asyncio
async def test_executor_executes_tool_and_calls_model_again(
    executor,
    calculator,
    model,
):
    request = AgentRequest(messages=[HumanMessage(content="Сколько будет 24 * 16?")])

    execution = await executor.invoke(request)

    chunks = []

    async for chunk in execution.stream:
        chunks.append(chunk)

    result = await execution.get_result()

    answer = "".join(chunks)

    assert answer == "Результат: 384"

    assert result.message.content == "Результат: 384"

    assert result.metrics.iterations == 1

    assert model.calls == 2

    assert calculator.calls == [{"expression": "24 * 16"}]
