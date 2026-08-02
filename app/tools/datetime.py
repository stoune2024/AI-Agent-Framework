from datetime import datetime

from langchain_core.tools import tool


@tool
def current_datetime() -> str:
    """
    Returns current UTC datetime.
    """

    return datetime.utcnow().isoformat()