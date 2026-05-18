import base64
import fcntl
import json
import os
import pty
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from app.schemas.openclaw import ExampleAgent


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
        session_id = "oc_" + uuid4().hex[:16]
        self._sessions[session_id] = {
            "agent_id": agent.agent_id,
            "custom_instructions": custom_instructions,
        }

        self._ensure_cli_available()
        self._ensure_workspace()
        self._ensure_gateway_running()

        login_result = self._start_provider_login()
        return RuntimeSessionResult(
            openclaw_session_id=session_id,
            runtime_status="login_required",
            provider_status="login_required",
            login_url=login_result.get("login_url"),
            model=None,
            provider=f"ChatGPT/OpenAI via {self.provider}",
            diagnostic=login_result.get("diagnostic"),
        )

    def confirm_login(self, session_id: str) -> RuntimeSessionResult:
        self._require_session(session_id)
        self._ensure_cli_available()
        self._ensure_gateway_running()

        auth_status = self._probe_provider_auth()
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
        self._require_session(session_id)
        return self._responses_call(
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Continue the photo-language tutoring session. "
                                f"User message: {message}"
                            ),
                        }
                    ],
                }
            ]
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

        encoded = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:{content_type};base64,{encoded}"
        return self._responses_call(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt_text},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ]
        )

    def invoke_validation_skill(self, session_id: str) -> SkillResult:
        self._require_session(session_id)
        result = self._responses_call(
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Use the allowlisted lesson-formatting skill for this agent. "
                                "Return a response with exactly these sections: Vocabulary, "
                                "Practical Phrases, Practice. Mention that the formatting "
                                "came from the validation skill."
                            ),
                        }
                    ],
                }
            ]
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

    def _gateway_responds(self) -> bool:
        try:
            request = Request(self.gateway_url.rstrip("/") + "/", method="GET")
            with urlopen(request, timeout=2):
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

    def _probe_provider_auth(self) -> Dict[str, Optional[str]]:
        if self._login_process and self._login_process.poll() is None:
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
            timeout=30,
            check=False,
        )
        output = result.stdout or ""
        connected = result.returncode == 0 and self.provider in output
        return {
            "connected": connected,
            "login_url": self._extract_url(output),
            "diagnostic": output,
        }

    def _responses_call(self, input_items: list) -> AssistantResult:
        payload = {
            "model": self.model,
            "input": input_items,
        }
        data = self._request_json("POST", "/v1/responses", payload, timeout=120)
        return AssistantResult(
            message=self._extract_response_text(data),
            usage=self._extract_usage(data),
        )

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Optional[dict],
        timeout: int,
    ) -> dict:
        url = self.gateway_url.rstrip("/") + path
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"}
        if self.gateway_token:
            headers["Authorization"] = f"Bearer {self.gateway_token}"
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                response_body = response.read().decode("utf-8")
                try:
                    return json.loads(response_body) if response_body else {}
                except json.JSONDecodeError as exc:
                    raise OpenClawError(
                        "openclaw_non_json_response",
                        (
                            f"OpenClaw gateway returned non-JSON for {path}. "
                            "This usually means the gateway served Control UI HTML "
                            "instead of the OpenAI-compatible endpoint."
                        ),
                    ) from exc
        except HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise OpenClawError(
                f"openclaw_http_{exc.code}",
                f"OpenClaw gateway returned HTTP {exc.code}: {body_text}",
            ) from exc
        except URLError as exc:
            raise OpenClawError(
                "openclaw_gateway_unavailable",
                f"OpenClaw gateway is unavailable at {url}: {exc.reason}",
            ) from exc
        except TimeoutError as exc:
            raise OpenClawError(
                "openclaw_gateway_timeout",
                f"OpenClaw gateway timed out while calling {path}.",
            ) from exc

    def _require_session(self, session_id: str) -> Dict[str, Optional[str]]:
        session = self._sessions.get(session_id)
        if session is None:
            raise OpenClawError("openclaw_session_missing", "Unknown OpenClaw session.")
        return session

    def _extract_response_text(self, data: dict) -> str:
        if isinstance(data.get("output_text"), str):
            return data["output_text"]
        chunks = []
        for output in data.get("output", []) or []:
            for content in output.get("content", []) or []:
                text = content.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        if chunks:
            return "\n".join(chunks)
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
