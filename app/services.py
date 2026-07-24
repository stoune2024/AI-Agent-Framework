"""

Основная бизнес логика приложения

"""

from typing import AsyncIterator

from app.models import MessageRole
from app.protocols import (
    LLMClientProtocol,
    UnitOfWorkFactoryProtocol,
)

