from pydantic import BaseModel


class AgentChatRequest(BaseModel):
    conversation_id: int | None = None

    message: str
