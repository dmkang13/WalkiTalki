from dataclasses import dataclass
from typing import Dict, Optional
from uuid import uuid4

from app.schemas.openclaw import ExampleAgent


@dataclass
class RuntimeSessionResult:
    openclaw_session_id: str
    runtime_status: str
    provider_status: str
    login_url: Optional[str]
    model: Optional[str]
    provider: Optional[str]


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


class MockOpenClawClient:
    """Mock adapter preserving the seam for the real OpenClaw integration."""

    def __init__(self) -> None:
        self._provider_status: Dict[str, str] = {}

    def create_session(
        self,
        agent: ExampleAgent,
        custom_instructions: Optional[str],
    ) -> RuntimeSessionResult:
        session_id = "oc_" + uuid4().hex[:16]
        self._provider_status[session_id] = "login_required"
        return RuntimeSessionResult(
            openclaw_session_id=session_id,
            runtime_status="login_required",
            provider_status="login_required",
            login_url="https://chatgpt.com/?mock_openclaw_login=1",
            model=None,
            provider="ChatGPT/OpenAI",
        )

    def confirm_login(self, session_id: str) -> RuntimeSessionResult:
        self._provider_status[session_id] = "connected"
        return RuntimeSessionResult(
            openclaw_session_id=session_id,
            runtime_status="ready",
            provider_status="connected",
            login_url=None,
            model="target-llm-vision",
            provider="ChatGPT/OpenAI",
        )

    def send_text(self, session_id: str, message: str) -> AssistantResult:
        self._require_connected(session_id)
        return AssistantResult(
            message=(
                "I am still in the same OpenClaw runtime session. "
                f"You asked: **{message}**\n\n"
                "Ask me about the uploaded image, request simpler examples, or "
                "ask for a quick practice question."
            ),
            usage={"input_tokens": 42, "output_tokens": 64},
        )

    def send_image_lesson(
        self,
        session_id: str,
        filename: str,
        content_type: str,
        byte_count: int,
        prompt: Optional[str],
    ) -> AssistantResult:
        self._require_connected(session_id)
        prompt_line = f"\n\nSession note: {prompt}" if prompt else ""
        return AssistantResult(
            message=(
                "## Photo Language Lesson\n\n"
                f"I received `{filename}` (`{content_type}`, {byte_count} bytes) "
                "through the OpenClaw image route and treated it as input to the "
                "target vision-capable LLM.\n\n"
                "### Useful Vocabulary\n\n"
                "1. **la mesa** - the table\n"
                "2. **la silla** - the chair\n"
                "3. **la ventana** - the window\n\n"
                "### Practical Phrases\n\n"
                "- **La mesa está cerca de la ventana.** - The table is near the window.\n"
                "- **Veo una silla.** - I see a chair.\n\n"
                "### Practice\n\n"
                "Try answering: **¿Qué ves en la foto?**"
                f"{prompt_line}"
            ),
            usage={"input_tokens": 312, "output_tokens": 186},
        )

    def invoke_validation_skill(self, session_id: str) -> SkillResult:
        self._require_connected(session_id)
        return SkillResult(
            skill_name="Lesson Formatting Skill",
            skill_source="Reviewed instruction-only public SKILL.md-style demo",
            evidence="The response uses the required Vocabulary, Phrases, and Practice sections.",
            message=(
                "## Skill Validation\n\n"
                "The allowlisted **Lesson Formatting Skill** is available in this "
                "runtime session.\n\n"
                "- **Evidence:** lesson responses are organized into Vocabulary, "
                "Practical Phrases, and Practice sections.\n"
                "- **Boundary:** this skill is instruction-only and does not use "
                "credentials, shell execution, browser control, or external writes."
            ),
        )

    def _require_connected(self, session_id: str) -> None:
        if self._provider_status.get(session_id) != "connected":
            raise RuntimeError("login_required")
