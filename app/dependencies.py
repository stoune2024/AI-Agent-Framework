"""

Здесь будут жить все Depends

"""

from fastapi import Depends

from app.agents.service import AgentService
from app.database import get_session_factory
from app.llm.ollama import OllamaLLMClient
from app.llm.openai import OpenAILLMClient
from app.protocols.llm import LLMClientProtocol
from app.uow import UnitOfWorkFactory
from settings.settings import get_settings


def get_uow_factory():

    return UnitOfWorkFactory(
        get_session_factory(),
    )


def get_llm_client() -> LLMClientProtocol:

    settings = get_settings()

    match settings.LLM_PROVIDER:
        case "ollama":
            return OllamaLLMClient(
                host=settings.OLLAMA_HOST,
                model=settings.LLM_MODEL,
            )

        case "openai":
            return OpenAILLMClient(
                api_key=settings.OPENAI_API_KEY,
                model=settings.LLM_MODEL,
            )

        case _:
            raise ValueError("Unknown LLM provider")


def get_agent_llm_service(
    llm: LLMClientProtocol = Depends(get_llm_client),
) -> AgentService:

    return AgentService(
        llm=llm,
    )
