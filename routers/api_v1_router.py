from fastapi import FastAPI

from app.controllers import router
from app.database import lifespan
from app.exceptions import (
    MaxIterationsExceededError,
    ToolExecutionError,
    ToolNotFoundError,
)
from app.exceptions.handlers import (
    max_iterations_handler,
    tool_execution_handler,
    tool_not_found_handler,
)

app = FastAPI(lifespan=lifespan, root_path="/api/v1")


app.include_router(router)

app.add_exception_handler(
    ToolNotFoundError,
    tool_not_found_handler,
)

app.add_exception_handler(
    ToolExecutionError,
    tool_execution_handler,
)

app.add_exception_handler(
    MaxIterationsExceededError,
    max_iterations_handler,
)
