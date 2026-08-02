from fastapi import APIRouter, Depends

from app.agents.service import AgentService
from app.dependencies import get_agent_service
from app.models import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


@router.post(
    "/invoke",
    response_model=ChatResponse,
)
async def invoke_agent(
    request: ChatRequest,
    service: AgentService = Depends(get_agent_service),
) -> ChatResponse:

    answer = await service.invoke(
        request.message,
    )

    return ChatResponse(
        response=answer,
    )
