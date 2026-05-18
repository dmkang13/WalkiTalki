from app.schemas.openclaw import ExampleAgent


def get_example_agent() -> ExampleAgent:
    return ExampleAgent(
        agent_id="photo-language-openclaw-demo",
        name="Photo Language Tutor",
        description=(
            "A prebuilt OpenClaw validation agent that turns an uploaded photo "
            "into a short language lesson and supports follow-up chat."
        ),
        target_language="Spanish",
        native_language="English",
        instructions=(
            "Identify visible objects in the user's image. Teach the most useful "
            "target-language words and phrases. Keep explanations concise, "
            "practical, and grounded in the image."
        ),
        required_capabilities=[
            "chatgpt_provider_login",
            "target_llm_image_upload",
            "session_custom_instructions",
            "allowlisted_instruction_skill",
        ],
        validation_skill_id="lesson-formatting-skill",
        validation_skill_name="Lesson Formatting Skill",
        validation_skill_source=(
            "Reviewed instruction-only demo skill based on public SKILL.md-style "
            "agent skill conventions."
        ),
    )
