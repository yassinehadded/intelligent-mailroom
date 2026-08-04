from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import analysis, audit, email, health, maarch
from src.config import get_settings
from src.utils import get_logger


settings = get_settings()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Application factory.
    Creates and configures the FastAPI application.
    """

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(health.router)
    api_router.include_router(maarch.router)
    api_router.include_router(email.router)
    api_router.include_router(analysis.router)
    api_router.include_router(audit.router)

    app.include_router(api_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "application": settings.app_name,
            "status": "running",
        }

    logger.info("FastAPI application initialized")

    return app
