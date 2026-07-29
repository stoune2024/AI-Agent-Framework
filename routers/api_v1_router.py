from fastapi import FastAPI

from app.controllers import router
from app.database import lifespan

app = FastAPI(lifespan=lifespan, root_path="/api/v1")


app.include_router(router)
