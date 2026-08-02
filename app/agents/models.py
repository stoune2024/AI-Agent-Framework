from dataclasses import dataclass


@dataclass(slots=True)
class AgentResponse:
    answer: str


@dataclass(slots=True)
class ToolCall: ...


@dataclass(slots=True)
class ToolResult: ...
