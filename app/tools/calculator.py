from langchain_core.tools import tool


@tool
def calculator(
    expression: str,
) -> str:
    """
    Evaluate mathematical expression.
    """

    return str(eval(expression))
