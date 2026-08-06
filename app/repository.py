from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MessageRole
from app.schemas import ConversationSchema, MessageSchema


class ConversationRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self._session = session

    async def create_conversation(
        self,
    ) -> ConversationSchema:

        conversation = ConversationSchema()

        self._session.add(conversation)

        await self._session.flush()
        await self._session.refresh(conversation)

        return conversation

    async def get_conversation(
        self,
        conversation_id: int,
    ) -> ConversationSchema | None:

        statement = select(ConversationSchema).where(
            ConversationSchema.id == conversation_id
        )

        return await self._session.scalar(statement)

    async def get_messages(
        self,
        conversation_id: int,
    ) -> list[MessageSchema]:

        statement = (
            select(MessageSchema)
            .where(MessageSchema.conversation_id == conversation_id)
            .order_by(MessageSchema.created_at)
        )

        result = await self._session.scalars(statement)

        return list(result)

    async def get_history(
        self,
        conversation_id: int,
    ) -> list[BaseMessage]:

        messages = await self.get_messages(conversation_id)

        return [self._to_langchain_message(message) for message in messages]

    async def add_message(
        self,
        conversation_id: int,
        role: MessageRole,
        content: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> MessageSchema:

        message = MessageSchema(
            conversation_id=conversation_id,
            role=role,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        self._session.add(message)

        await self._session.flush()

        return message

    @staticmethod
    def _to_langchain_message(
        message: MessageSchema,
    ) -> BaseMessage:

        match message.role:
            case "user":
                return HumanMessage(content=message.content)

            case "assistant":
                return AIMessage(content=message.content)

            case _:
                raise ValueError(f"Unsupported message role: {message.role}")
