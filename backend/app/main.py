from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes.auth import router as auth_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.health import router as health_router
from app.api.routes.insights import router as insights_router
from app.api.routes.journeys import router as journeys_router
from app.api.routes.memories import router as memories_router
from app.api.routes.voice import router as voice_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.security import hash_password
from app.db.database import SessionLocal, get_engine
from app.db.models import Base, User

setup_logging()
logger = get_logger(__name__)

# Default admin user for local testing (email=admin_sam@icloud.com, password=1234)
_ADMIN_EMAIL = "admin_sam@icloud.com"
_ADMIN_PASSWORD = "1234"
_ADMIN_NAME = "Sam"


def _run_migrations() -> None:
    """Add new columns to existing tables without dropping data (SQLite-safe)."""
    engine = get_engine()
    with engine.connect() as conn:
        def _add_col_if_missing(table: str, col: str, col_def: str) -> None:
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            existing = {row[1] for row in result.fetchall()}
            if col not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_def}"))
                logger.info(f"Migration: added {table}.{col}")

        _add_col_if_missing("conversations", "user_id", "user_id VARCHAR(36)")
        _add_col_if_missing("memories", "user_id", "user_id VARCHAR(36)")
        _add_col_if_missing("conversations", "summary", "summary TEXT DEFAULT ''")
        _add_col_if_missing(
            "conversations", "summarized_through_count", "summarized_through_count INTEGER DEFAULT 0"
        )
        conn.commit()


def _seed_admin_and_migrate(admin_id: str) -> None:
    """Assign all orphaned rows (user_id=NULL) to the admin user."""
    db = SessionLocal()
    try:
        db.execute(
            text("UPDATE conversations SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": admin_id},
        )
        db.execute(
            text("UPDATE memories SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": admin_id},
        )
        db.commit()
        logger.info(f"Migrated orphaned rows → admin user {admin_id[:8]}")
    except Exception as exc:
        db.rollback()
        logger.warning(f"Migration step failed: {exc}")
    finally:
        db.close()


def _ensure_admin_user() -> str:
    """Return admin user ID, creating the user if not exists."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == _ADMIN_EMAIL).first()
        if not user:
            user = User(
                email=_ADMIN_EMAIL,
                hashed_password=hash_password(_ADMIN_PASSWORD),
                display_name=_ADMIN_NAME,
            )
            db.add(user)
            db.commit()
            logger.info(f"Seeded admin user: {_ADMIN_EMAIL}")
        return user.id
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    Base.metadata.create_all(bind=get_engine())
    _run_migrations()
    admin_id = _ensure_admin_user()
    _seed_admin_and_migrate(admin_id)
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
    app.include_router(auth_router, prefix="/api")
    app.include_router(voice_router, prefix="/api")
    app.include_router(conversations_router, prefix="/api")
    app.include_router(memories_router, prefix="/api")
    app.include_router(journeys_router, prefix="/api")
    app.include_router(insights_router, prefix="/api")

    return app


app = create_app()
