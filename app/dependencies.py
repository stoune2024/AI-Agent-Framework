from fastapi import Depends

from app.agents.executor import AgentExecutor
from app.agents.service import AgentService
from app.providers.base import ModelProviderProtocol
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider
from app.tools.calculator import calculator
from app.tools.datetime import current_datetime
from app.tools.registry import ToolRegistry
from settings.settings import get_settings


def get_model_provider() -> ModelProviderProtocol:

    settings = get_settings()

    match settings.LLM_PROVIDER:
        case "ollama":
            return OllamaProvider(
                host=settings.OLLAMA_HOST,
                model=settings.LLM_MODEL,
            )

        case "openai":
            return OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.LLM_MODEL,
            )

        case _:
            raise ValueError(
                settings.LLM_PROVIDER,
            )


def get_tool_registry() -> ToolRegistry:

    return ToolRegistry(
        tools=[
            calculator,
            current_datetime,
        ]
    )


def get_agent_executor(
    provider: ModelProviderProtocol = Depends(get_model_provider),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> AgentExecutor:

    return AgentExecutor(
        provider=provider,
        registry=registry,
    )


def get_agent_service(
    executor: AgentExecutor = Depends(get_agent_executor),
) -> AgentService:

    return AgentService(
        executor=executor,
    )
