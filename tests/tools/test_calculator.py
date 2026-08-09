import pytest

from app.tools.calculator import calculator


@pytest.fixture
def calculator_fixt():
    return calculator


@pytest.mark.asyncio
async def test_calculator_addition(
    calculator_fixt,
):
    result = await calculator.ainvoke(
        {
            "expression": "2 + 2",
        }
    )

    assert result == "4"


@pytest.mark.asyncio
async def test_calculator_multiplication(
    calculator_fixt,
):
    result = await calculator.ainvoke(
        {
            "expression": "25 * 17",
        }
    )

    assert result == "425"