from dataclasses import dataclass


@dataclass(slots=True)
class AgentResponse:
    answer: str


@dataclass(slots=True)
class ToolCall:
    name: str

    arguments: dict


@dataclass(slots=True)
class ToolResult:
    name: str

    result: str
