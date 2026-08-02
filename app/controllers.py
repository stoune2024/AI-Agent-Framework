from fastapi import APIRouter, Depends

from app.agents.service import AgentService
from app.dependencies import get_agent_llm_service
from app.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: AgentService = Depends(get_agent_llm_service),
) -> ChatResponse:

    response = await service.invoke(request.message)

    return ChatResponse(
        response=response,
    )
