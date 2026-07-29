"""

Здесь будут жить все Depends

"""

from app.database import get_session_factory
from app.uow import UnitOfWorkFactory


def get_uow_factory():

    return UnitOfWorkFactory(
        get_session_factory(),
    )
