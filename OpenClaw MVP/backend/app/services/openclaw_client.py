import fcntl
import json
import logging
import os
import pty
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from app.schemas.openclaw import ExampleAgent


logger = logging.getLogger("openclaw.backend.debug")


def debug_requests_enabled() -> bool:
    return os.getenv("OPENCLAW_DEBUG_REQUESTS", "").lower() in {"1", "true", "yes", "on"}


def _format_body(body: bytes) -> str:
    if not body:
        return "<empty>"
    return body.decode("utf-8", errors="replace")


class OpenClawError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class RuntimeSessionResult:
    openclaw_session_id: str
    runtime_status: str
    provider_status: str
    login_url: Optional[str]
    model: Optional[str]
    provider: Optional[str]
    diagnostic: Optional[str] = None


@dataclass
class AssistantResult:
    message: str
    usage: Dict[str, int]


@dataclass
class SkillResult:
    message: str
    skill_name: str
    skill_source: str
    evidence: str


class OpenClawClient:
    """Real OpenClaw CLI/gateway adapter.

    This class intentionally fails loudly when OpenClaw is unavailable. The MVP
    exists to validate the real runtime, so there is no mock fallback here.
    """

    def __init__(self) -> None:
        self.cli = os.getenv("OPENCLAW_CLI", "openclaw")
        self.gateway_url = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
        self.model = os.getenv("OPENCLAW_MODEL", "openai-codex/gpt-5.4")
        self.provider = os.getenv("OPENCLAW_PROVIDER", "openai-codex")
        self.gateway_token = os.getenv("OPENCLAW_GATEWAY_TOKEN")
        self.workspace = Path(os.getenv("OPENCLAW_WORKSPACE", Path.cwd() / "openclaw_workspace"))
        self.log_dir = self.workspace / "logs"
        self._gateway_process: Optional[subprocess.Popen[str]] = None
        self._login_process: Optional[subprocess.Popen[str]] = None
        self._login_master_fd: Optional[int] = None
        self._sessions: Dict[str, Dict[str, Optional[str]]] = {}

    def create_session(
        self,
        agent: ExampleAgent,
        custom_instructions: Optional[str],
    ) -> RuntimeSessionResult:
        self._ensure_cli_available()
        self._ensure_workspace()
        self._ensure_gateway_running()

        auth_status = self._probe_provider_auth(ignore_running_login=True)
        if not auth_status["connected"]:
            raise OpenClawError(
                "provider_login_required",
                "Sign in to ChatGPT through OpenClaw before starting an agent chat session.",
            )

        session_id = "oc_" + uuid4().hex[:16]
        self._sessions[session_id] = {
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "agent_instructions": agent.instructions,
            "target_language": agent.target_language,
            "native_language": agent.native_language,
            "custom_instructions": custom_instructions,
        }
        return RuntimeSessionResult(
            openclaw_session_id=session_id,
            runtime_status="ready",
            provider_status="connected",
            login_url=None,
            model=self.model,
            provider=f"ChatGPT/OpenAI via {self.provider}",
            diagnostic=auth_status.get("diagnostic"),
        )

    def confirm_login(self, session_id: str) -> RuntimeSessionResult:
        self._require_session(session_id)
        self._ensure_cli_available()
        self._ensure_gateway_running()

        auth_status = self._probe_provider_auth(ignore_running_login=True)
        if not auth_status["connected"]:
            return RuntimeSessionResult(
                openclaw_session_id=session_id,
                runtime_status="login_required",
                provider_status="login_required",
                login_url=auth_status.get("login_url"),
                model=None,
                provider=f"ChatGPT/OpenAI via {self.provider}",
                diagnostic=auth_status.get("diagnostic"),
            )

        return RuntimeSessionResult(
            openclaw_session_id=session_id,
            runtime_status="ready",
            provider_status="connected",
            login_url=None,
            model=self.model,
            provider=f"ChatGPT/OpenAI via {self.provider}",
        )

    def send_text(self, session_id: str, message: str) -> AssistantResult:
        session = self._require_session(session_id)
        return self._infer_model_run(
            prompt=self._build_text_prompt(session, message)
        )

    def stream_text(self, session_id: str, message: str) -> Iterator[Dict[str, object]]:
        session = self._require_session(session_id)
        self._ensure_gateway_running()
        prompt = self._build_text_prompt(session, message)
        if not self._use_gateway_streams():
            result = self._infer_model_run(prompt=prompt)
            yield {"type": "delta", "text": result.message}
            yield {"type": "done", "usage": result.usage}
            return

        try:
            yield from self._stream_gateway_response(prompt)
        except OpenClawError:
            raise
        except Exception as exc:
            raise OpenClawError("openclaw_stream_failed", str(exc)) from exc

    def begin_provider_login(self) -> RuntimeSessionResult:
        self._ensure_cli_available()
        self._ensure_workspace()
        login_result = self._start_provider_login()
        return RuntimeSessionResult(
            openclaw_session_id="",
            runtime_status="login_required",
            provider_status="login_required",
            login_url=login_result.get("login_url"),
            model=None,
            provider=f"ChatGPT/OpenAI via {self.provider}",
            diagnostic=login_result.get("diagnostic"),
        )

    def provider_auth_status(self) -> RuntimeSessionResult:
        self._ensure_cli_available()
        self._ensure_workspace()
        auth_status = self._probe_provider_auth(ignore_running_login=False)
        connected = bool(auth_status["connected"])
        return RuntimeSessionResult(
            openclaw_session_id="",
            runtime_status="ready" if connected else "login_required",
            provider_status="connected" if connected else "login_required",
            login_url=None if connected else auth_status.get("login_url"),
            model=self.model if connected else None,
            provider=f"ChatGPT/OpenAI via {self.provider}",
            diagnostic=auth_status.get("diagnostic"),
        )

    def send_image_lesson(
        self,
        session_id: str,
        filename: str,
        content_type: str,
        image_bytes: bytes,
        prompt: Optional[str],
    ) -> AssistantResult:
        session = self._require_session(session_id)
        custom = session.get("custom_instructions")
        custom_text = f"\nSession-only custom instructions: {custom}" if custom else ""
        prompt_text = (
            "You are the prebuilt WalkiTalki Photo Language Tutor. Inspect the uploaded "
            "image. Name visible objects in Spanish, define them in English, provide "
            "practical phrases, and ask one practice question."
            f"{custom_text}"
        )
        if prompt:
            prompt_text += f"\nAdditional user prompt: {prompt}"

        upload_dir = self.workspace / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(filename).suffix or ".image"
        image_path = upload_dir / f"{uuid4().hex}{suffix}"
        image_path.write_bytes(image_bytes)
        return self._infer_model_run(prompt=prompt_text, image_path=image_path)

    def invoke_validation_skill(self, session_id: str) -> SkillResult:
        self._require_session(session_id)
        result = self._infer_model_run(
            prompt=(
                "Use the allowlisted lesson-formatting skill for this agent. "
                "Return a response with exactly these sections: Vocabulary, "
                "Practical Phrases, Practice. Mention that the formatting "
                "came from the validation skill."
            )
        )
        return SkillResult(
            skill_name="Lesson Formatting Skill",
            skill_source=str(self.workspace / "skills" / "lesson-formatting" / "SKILL.md"),
            evidence="The response should contain the skill-defined lesson sections.",
            message=result.message,
        )

    def _ensure_cli_available(self) -> None:
        if shutil.which(self.cli) is None:
            raise OpenClawError(
                "openclaw_cli_missing",
                (
                    "OpenClaw CLI is not installed or not on PATH. Install OpenClaw, "
                    "then restart the backend so it can run the real gateway and "
                    "ChatGPT login flow."
                ),
            )

    def _ensure_workspace(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        skill_dir = self.workspace / "skills" / "lesson-formatting"
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            skill_file.write_text(
                "# Lesson Formatting Skill\n\n"
                "When creating a language lesson from an image, always organize the "
                "answer into these sections:\n\n"
                "1. Vocabulary\n"
                "2. Practical Phrases\n"
                "3. Practice\n\n"
                "Keep the lesson concise and grounded in visible objects.\n",
                encoding="utf-8",
            )

    def _ensure_gateway_running(self) -> None:
        if self._gateway_responds():
            return

        cmd = [
            self.cli,
            "gateway",
            "--port",
            self.gateway_url.rsplit(":", 1)[-1],
            "--allow-unconfigured",
            "--auth",
            "none",
        ]
        gateway_log = (self.log_dir / "gateway.log").open("a", encoding="utf-8")
        self._gateway_process = subprocess.Popen(
            cmd,
            cwd=str(self.workspace),
            stdout=gateway_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        deadline = time.time() + 12
        while time.time() < deadline:
            if self._gateway_responds():
                return
            if self._gateway_process.poll() is not None:
                output = self._read_log_tail("gateway.log")
                raise OpenClawError(
                    "openclaw_gateway_failed",
                    f"OpenClaw gateway exited before becoming ready. {output}",
                )
            time.sleep(0.5)

        raise OpenClawError(
            "openclaw_gateway_timeout",
            "OpenClaw gateway did not become ready within 12 seconds.",
        )

    def _use_gateway_streams(self) -> bool:
        return os.getenv("OPENCLAW_USE_GATEWAY_STREAMS", "").lower() in {"1", "true", "yes", "on"}

    def _gateway_responds(self) -> bool:
        try:
            url = self.gateway_url.rstrip("/") + "/"
            if debug_requests_enabled():
                logger.info("GATEWAY OUT GET %s", url)
            request = Request(url, method="GET")
            with urlopen(request, timeout=2) as response:
                if debug_requests_enabled():
                    logger.info("GATEWAY IN  GET / -> %s", response.status)
                return True
        except Exception:
            return False

    def _start_provider_login(self) -> Dict[str, Optional[str]]:
        if self._login_process and self._login_process.poll() is None:
            output = self._read_login_output()
            return {
                "login_url": self._extract_url(output),
                "diagnostic": output or "Provider login is already running.",
            }

        cmd = [self.cli, "models", "auth", "login", "--provider", self.provider]
        master_fd, slave_fd = pty.openpty()
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self._login_process = subprocess.Popen(
            cmd,
            cwd=str(self.workspace),
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            text=True,
        )
        os.close(slave_fd)
        self._login_master_fd = master_fd
        time.sleep(1)
        output = self._read_login_output()
        return {
            "login_url": self._extract_url(output),
            "diagnostic": output or "OpenClaw provider login process started.",
        }

    def _probe_provider_auth(self, ignore_running_login: bool = False) -> Dict[str, Optional[str]]:
        if self._login_process and self._login_process.poll() is None and not ignore_running_login:
            output = self._read_login_output()
            return {
                "connected": False,
                "login_url": self._extract_url(output),
                "diagnostic": output or "OpenClaw provider login is still running.",
            }

        result = subprocess.run(
            [self.cli, "models", "status", "--probe"],
            cwd=str(self.workspace),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=45,
            check=False,
        )
        output = result.stdout or ""
        connected = (
            result.returncode == 0
            and self.provider in output
            and "ok expires" in output
        )
        return {
            "connected": connected,
            "login_url": self._extract_url(output),
            "diagnostic": output,
        }

    def _infer_model_run(
        self,
        prompt: str,
        image_path: Optional[Path] = None,
    ) -> AssistantResult:
        cmd = [
            self.cli,
            "infer",
            "model",
            "run",
            "--gateway",
            "--model",
            self.model,
            "--prompt",
            prompt,
            "--json",
        ]
        if image_path is not None:
            cmd.extend(["--file", str(image_path)])
        result = subprocess.run(
            cmd,
            cwd=str(self.workspace),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
            check=False,
        )
        if result.returncode != 0:
            raise OpenClawError(
                "openclaw_inference_failed",
                result.stdout or "OpenClaw inference command failed.",
            )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise OpenClawError(
                "openclaw_non_json_response",
                f"OpenClaw inference returned non-JSON output: {result.stdout}",
            ) from exc
        return AssistantResult(
            message=self._extract_infer_text(data),
            usage=self._extract_usage(data),
        )

    def _stream_gateway_response(self, prompt: str) -> Iterator[Dict[str, object]]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        if self.gateway_token:
            headers["Authorization"] = f"Bearer {self.gateway_token}"

        body = json.dumps(
            {
                "model": self.model,
                "input": prompt,
                "stream": True,
            }
        ).encode("utf-8")
        url = self.gateway_url.rstrip("/") + "/v1/responses"
        if debug_requests_enabled():
            logger.info("GATEWAY OUT POST %s", url)
            logger.info("GATEWAY OUT body=%s", _format_body(body))

        request = Request(
            url,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=180) as response:
                if debug_requests_enabled():
                    logger.info("GATEWAY IN  POST /v1/responses -> %s", response.status)
                yield from self._iter_response_stream(response)
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if debug_requests_enabled():
                logger.info("GATEWAY IN  POST /v1/responses -> %s body=%s", exc.code, body)
            raise OpenClawError(
                "openclaw_stream_failed",
                body or f"OpenClaw stream failed with HTTP {exc.code}.",
            ) from exc
        except URLError as exc:
            raise OpenClawError("openclaw_stream_failed", str(exc.reason)) from exc

    def _iter_response_stream(self, response: object) -> Iterator[Dict[str, object]]:
        usage: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or line.startswith(":"):
                continue
            if not line.startswith("data:"):
                continue

            if debug_requests_enabled():
                logger.info("GATEWAY IN  stream=%s", line)

            data_text = line.removeprefix("data:").strip()
            if data_text == "[DONE]":
                break

            try:
                data = json.loads(data_text)
            except json.JSONDecodeError:
                continue

            delta = self._extract_stream_delta(data)
            if delta:
                yield {"type": "delta", "text": delta}

            next_usage = self._extract_usage(data)
            if next_usage["input_tokens"] or next_usage["output_tokens"]:
                usage = next_usage

        yield {"type": "done", "usage": usage}

    def _extract_stream_delta(self, data: dict) -> str:
        delta = data.get("delta")
        if isinstance(delta, str):
            return delta

        if data.get("type") in {
            "response.output_text.delta",
            "response.refusal.delta",
        }:
            text = data.get("delta")
            return text if isinstance(text, str) else ""

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            choice = choices[0]
            if isinstance(choice, dict):
                choice_delta = choice.get("delta")
                if isinstance(choice_delta, dict):
                    content = choice_delta.get("content")
                    return content if isinstance(content, str) else ""

        return ""

    def _require_session(self, session_id: str) -> Dict[str, Optional[str]]:
        session = self._sessions.get(session_id)
        if session is None:
            raise OpenClawError("openclaw_session_missing", "Unknown OpenClaw session.")
        return session

    def _build_text_prompt(self, session: Dict[str, Optional[str]], message: str) -> str:
        agent_instructions = session.get("agent_instructions") or (
            "You are a WalkiTalki language tutor. Help the user practice language "
            "through concise explanations and examples."
        )
        session_custom = session.get("custom_instructions")
        custom_text = f"\nSession-only custom instructions: {session_custom}" if session_custom else ""
        return (
            f"{agent_instructions}"
            f"{custom_text}\n\n"
            "Product guardrails: do not claim to save flashcards, memory, progress, "
            "vocabulary, images, or lesson history. Do not refer to image upload "
            "features unless the user explicitly asks about future capabilities.\n\n"
            f"User message: {message}"
        )

    def _extract_infer_text(self, data: dict) -> str:
        outputs = data.get("outputs") or []
        texts = [item.get("text") for item in outputs if isinstance(item.get("text"), str)]
        if texts:
            return "\n".join(texts)
        return json.dumps(data, indent=2)

    def _extract_usage(self, data: dict) -> Dict[str, int]:
        usage = data.get("usage") or {}
        return {
            "input_tokens": int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or usage.get("completion_tokens") or 0),
        }

    def _extract_url(self, text: str) -> Optional[str]:
        match = re.search(r"https?://[^\s)]+", text or "")
        return match.group(0) if match else None

    def _read_log_tail(self, filename: str) -> str:
        path = self.log_dir / filename
        if not path.exists():
            return ""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            return text[-4000:]
        except OSError:
            return ""

    def _read_login_output(self) -> str:
        if self._login_master_fd is None:
            return self._read_log_tail("login.log")
        chunks = []
        while True:
            try:
                chunk = os.read(self._login_master_fd, 4096)
                if not chunk:
                    break
                chunks.append(chunk.decode("utf-8", errors="replace"))
            except BlockingIOError:
                break
            except OSError:
                break
        text = "".join(chunks)
        if text:
            path = self.log_dir / "login.log"
            with path.open("a", encoding="utf-8") as log_file:
                log_file.write(text)
        return text or self._read_log_tail("login.log")
