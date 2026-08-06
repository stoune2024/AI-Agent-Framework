from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.agents.service import AgentService
from app.dependencies import get_agent_service
from app.models import AgentChatRequest

router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


@router.post("/chat")
async def chat(
    request: AgentChatRequest,
    service: AgentService = Depends(get_agent_service),
):

    result = await service.invoke(
        conversation_id=request.conversation_id,
        message=request.message,
    )

    return StreamingResponse(
        result.stream,
        media_type="text/plain",
        headers={"X-Conversation-ID": str(result.conversation_id)},
    )
