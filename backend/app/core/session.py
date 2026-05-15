import hashlib
import hmac
import secrets
from threading import RLock
from typing import Dict, Optional

from fastapi import Request, Response

from app.core.config import settings


class ApiKeySessionStore:
    def __init__(self) -> None:
        self._keys: Dict[str, str] = {}
        self._lock = RLock()

    def set_key(self, session_id: str, api_key: str) -> None:
        with self._lock:
            self._keys[session_id] = api_key

    def get_key(self, session_id: str) -> Optional[str]:
        with self._lock:
            return self._keys.get(session_id)

    def delete_key(self, session_id: str) -> None:
        with self._lock:
            self._keys.pop(session_id, None)

    def has_key(self, session_id: str) -> bool:
        return self.get_key(session_id) is not None


api_key_store = ApiKeySessionStore()


def ensure_session(request: Request, response: Response) -> str:
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        session_id = secrets.token_urlsafe(32)
    response.set_cookie(
        settings.session_cookie_name,
        session_id,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=60 * 60 * 24,
    )
    return session_id


def session_hash(session_id: str) -> str:
    digest = hmac.new(
        settings.session_secret.encode("utf-8"),
        session_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest
