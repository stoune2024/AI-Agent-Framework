from enum import StrEnum

from pydantic import BaseModel


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


"""

HTTP DTO модели

"""


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
