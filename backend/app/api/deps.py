from typing import Tuple

from fastapi import Request, Response

from app.core.session import ensure_session, session_hash


def current_session(request: Request, response: Response) -> Tuple[str, str]:
    session_id = ensure_session(request, response)
    return session_id, session_hash(session_id)
