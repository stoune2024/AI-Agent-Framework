from datetime import datetime

import pytest

from app.tools.datetime import current_datetime


@pytest.mark.asyncio
async def test_datetime_tool():

    tool = current_datetime

    result = await tool.ainvoke({})

    assert isinstance(result, str)

    datetime.fromisoformat(result)
