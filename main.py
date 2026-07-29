import uvicorn

from app.dependencies import get_settings

if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "routers.api_v1_router:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
    )
