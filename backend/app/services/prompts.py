from typing import Iterable, Sequence

from app.models.agent import AgentSpec
from app.models.lesson import ChatMessage


PRODUCT_GUARDRAILS = (
    "You are running inside WalkiTalki's MVP Photo Language Agent. "
    "Do not claim to save flashcards, vocabulary, memory, progress, audio, or external data. "
    "Do not use external APIs or tools. Keep the response focused on language learning."
)


def build_agent_instructions(agent: AgentSpec) -> str:
    native = agent.native_language or "the learner's native language"
    custom = agent.custom_instructions or "No extra creator preferences."
    return "\n".join(
        [
            PRODUCT_GUARDRAILS,
            f"Agent name: {agent.name}",
            f"Target language: {agent.target_language}",
            f"Native language for explanations: {native}",
            f"Creator preferences: {custom}",
        ]
    )


def build_initial_lesson_prompt(agent: AgentSpec) -> str:
    return "\n\n".join(
        [
            build_agent_instructions(agent),
            (
                "Create a short markdown language lesson from the uploaded image. "
                "Identify important visible objects, name them in the target language, define them plainly, "
                "include text-only pronunciation guidance when useful, provide practical phrases, "
                "and ask one or two follow-up practice questions."
            ),
        ]
    )


def build_followup_prompt(agent: AgentSpec, lesson_markdown: str, messages: Sequence[ChatMessage], new_question: str) -> str:
    recent_messages = list(messages)[-12:]
    chat_lines = [f"{message.role.value}: {message.content}" for message in recent_messages]
    context = "\n".join(chat_lines) if chat_lines else "No prior follow-up messages."
    return "\n\n".join(
        [
            build_agent_instructions(agent),
            f"Original lesson:\n{lesson_markdown}",
            f"Recent visible chat messages:\n{context}",
            f"User's new question:\n{new_question}",
            (
                "Answer within the lesson and chat context unless the user asks for a general language explanation. "
                "Keep the answer useful, concise, and honest about what the app does not persist."
            ),
        ]
    )
