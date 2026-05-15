from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, lessons, runtime, shared_agents
from app.core.config import settings
from app.core.errors import install_error_handlers
from app.db.base import Base
from app.db.session import engine


def create_app() -> FastAPI:
    app = FastAPI(title="WalkiTalki Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_error_handlers(app)

    app.include_router(runtime.router, prefix="/api")
    app.include_router(agents.router, prefix="/api")
    app.include_router(shared_agents.router, prefix="/api")
    app.include_router(lessons.router, prefix="/api")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app


app = create_app()


def create_all_for_local_sqlite() -> None:
    """Convenience hook for local prototypes; production should use Alembic."""
    Base.metadata.create_all(bind=engine)
