from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.openclaw_agent import router as openclaw_router


def create_app() -> FastAPI:
    app = FastAPI(title="OpenClaw MVP Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5174",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(openclaw_router, prefix="/api/openclaw", tags=["openclaw"])

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app


app = create_app()
