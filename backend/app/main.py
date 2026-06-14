from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.conversations import router as conversations_router
from app.api.routes.health import router as health_router
from app.api.routes.insights import router as insights_router
from app.api.routes.journeys import router as journeys_router
from app.api.routes.memories import router as memories_router
from app.api.routes.voice import router as voice_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.database import get_engine
from app.db.models import Base

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    Base.metadata.create_all(bind=get_engine())
    Path(settings.audio_output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Echo backend started | port={settings.port}")
    if not settings.anthropic_api_key:
        logger.warning("⚠  ANTHROPIC_API_KEY not set")
    yield
    logger.info("Shutting down.")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Echo API",
        description="Echo — Emotional Experience Platform",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(voice_router, prefix="/api")
    app.include_router(conversations_router, prefix="/api")
    app.include_router(memories_router, prefix="/api")
    app.include_router(journeys_router, prefix="/api")
    app.include_router(insights_router, prefix="/api")

    return app


app = create_app()
