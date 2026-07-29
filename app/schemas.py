from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ConversationSchema(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    messages: Mapped[list["MessageSchema"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class MessageSchema(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))

    role: Mapped[str] = mapped_column(String(20))

    content: Mapped[str] = mapped_column(String)

    prompt_tokens: Mapped[int | None]

    completion_tokens: Mapped[int | None]

    total_tokens: Mapped[int | None]

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation: Mapped["ConversationSchema"] = relationship(back_populates="messages")
