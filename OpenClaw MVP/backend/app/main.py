import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.openclaw_agent import router as openclaw_router


logger = logging.getLogger("openclaw.backend.debug")


def debug_requests_enabled() -> bool:
    return os.getenv("OPENCLAW_DEBUG_REQUESTS", "").lower() in {"1", "true", "yes", "on"}


def _format_body(body: bytes) -> str:
    if not body:
        return "<empty>"
    return body.decode("utf-8", errors="replace")


class RequestDebugMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        logger.info("BACKEND IN  %s %s", request.method, request.url)

        async def receive_with_logging() -> Message:
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if body:
                    logger.info("BACKEND IN  body=%s", _format_body(body))
            return message

        async def send_with_logging(message: Message) -> None:
            if message["type"] == "http.response.start":
                logger.info(
                    "BACKEND OUT %s %s -> %s",
                    request.method,
                    request.url.path,
                    message["status"],
                )
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    logger.info("BACKEND OUT body=%s", _format_body(body))
            await send(message)

        await self.app(scope, receive_with_logging, send_with_logging)


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = FastAPI(title="OpenClaw MVP Backend", version="0.1.0")

    if debug_requests_enabled():
        app.add_middleware(RequestDebugMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5174",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:4174",
            "http://localhost:4174",
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
