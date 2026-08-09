class AgentException(Exception):
    """Base exception for agent-related errors."""


class ToolNotFoundError(AgentException):
    """Requested tool does not exist."""


class ToolExecutionError(AgentException):
    """Tool execution failed."""


class MaxIterationsExceededError(AgentException):
    """Agent exceeded the maximum number of iterations."""
