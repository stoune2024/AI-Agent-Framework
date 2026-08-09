import structlog

from app.models.agent import (
    AgentRequest,
    AgentResult,
)

logger = structlog.get_logger()


class AgentService:
    def __init__(
        self,
        executor,
        uow_factory,
    ):
        self._executor = executor
        self._uow_factory = uow_factory

    async def invoke(
        self,
        conversation_id: int | None,
        message: str,
    ) -> AgentResult:

        async with self._uow_factory() as uow:
            if conversation_id is None:
                conversation = await uow.conversations.create_conversation()
                conversation_id = conversation.id
                logger.info(
                    "conversation.created",
                    conversation_id=conversation_id,
                )

            await uow.conversations.add_message(
                conversation_id=conversation_id,
                role="user",
                content=message,
            )

            history = await uow.conversations.get_history(conversation_id)

        logger.info(
            "agent.request",
            conversation_id=conversation_id,
            message_length=len(message),
        )

        request = AgentRequest(
            messages=history,
        )

        execution = await self._executor.invoke(request)

        async def stream():

            chunks: list[str] = []

            try:
                async for token in execution.stream:
                    chunks.append(token)

                    yield token

                result = await execution.get_result()

                usage = result.metrics.token_usage

                async with self._uow_factory() as uow:
                    await uow.conversations.add_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=result.message.content,
                        prompt_tokens=(
                            result.metrics.token_usage.prompt_tokens
                            if result.metrics.token_usage
                            else None
                        ),
                        completion_tokens=(
                            result.metrics.token_usage.completion_tokens
                            if result.metrics.token_usage
                            else None
                        ),
                        total_tokens=(
                            result.metrics.token_usage.total_tokens
                            if result.metrics.token_usage
                            else None
                        ),
                    )
                logger.info(
                    "agent.response_saved",
                    conversation_id=conversation_id,
                    iterations=result.metrics.iterations,
                    execution_time=(result.metrics.execution_time),
                    token_usage=(
                        {
                            "prompt_tokens": usage.prompt_tokens,
                            "completion_tokens": usage.completion_tokens,
                            "total_tokens": usage.total_tokens,
                        }
                        if usage
                        else None
                    ),
                )
            except Exception:
                logger.exception(
                    "agent.stream_failed",
                    conversation_id=conversation_id,
                )

                raise

        return AgentResult(
            conversation_id=conversation_id,
            stream=stream(),
        )
