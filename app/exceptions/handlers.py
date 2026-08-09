import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    MaxIterationsExceededError,
    ToolExecutionError,
    ToolNotFoundError,
)

logger = structlog.get_logger()


async def tool_not_found_handler(
    request: Request,
    exc: ToolNotFoundError,
) -> JSONResponse:

    logger.warning(
        "tool.not_found",
        error=str(exc),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=400,
        content={
            "error": "tool_not_found",
            "detail": str(exc),
        },
    )


async def tool_execution_handler(
    request: Request,
    exc: ToolExecutionError,
) -> JSONResponse:

    logger.error(
        "tool.execution_failed",
        error=str(exc),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "tool_execution_failed",
            "detail": str(exc),
        },
    )


async def max_iterations_handler(
    request: Request,
    exc: MaxIterationsExceededError,
) -> JSONResponse:

    logger.error(
        "agent.max_iterations",
        error=str(exc),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "max_iterations_exceeded",
            "detail": str(exc),
        },
    )
