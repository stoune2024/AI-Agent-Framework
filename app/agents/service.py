from app.models.agent import (
    AgentRequest,
    AgentResult,
)


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

            await uow.conversations.add_message(
                conversation_id=conversation_id,
                role="user",
                content=message,
            )

            history = await uow.conversations.get_history(conversation_id)

        request = AgentRequest(
            messages=history,
        )

        execution = await self._executor.invoke(request)

        async def stream():

            chunks = []

            async for token in execution.stream:
                chunks.append(token)

                yield token

            result = await execution.get_result()

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

        return AgentResult(
            conversation_id=conversation_id,
            stream=stream(),
        )
