"""initial MVP tables

Revision ID: 20260514_0001
Revises:
Create Date: 2026-05-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260514_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    agent_status = sa.Enum("draft", "published", name="agentstatus")
    chat_role = sa.Enum("user", "assistant", name="chatrole")

    op.create_table(
        "agent_specs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_session_hash", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("target_language", sa.String(length=80), nullable=False),
        sa.Column("native_language", sa.String(length=80), nullable=True),
        sa.Column("custom_instructions", sa.Text(), nullable=True),
        sa.Column("status", agent_status, nullable=False),
        sa.Column("share_slug", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("share_slug"),
    )
    op.create_index("ix_agent_specs_owner_session_hash", "agent_specs", ["owner_session_hash"])
    op.create_index("ix_agent_specs_share_slug", "agent_specs", ["share_slug"])

    op.create_table(
        "lesson_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("runtime_session_hash", sa.String(length=128), nullable=False),
        sa.Column("agent_spec_id", sa.Uuid(), nullable=False),
        sa.Column("share_slug", sa.String(length=64), nullable=False),
        sa.Column("image_mime_type", sa.String(length=64), nullable=False),
        sa.Column("image_size_bytes", sa.Integer(), nullable=False),
        sa.Column("image_storage_ref", sa.String(length=255), nullable=True),
        sa.Column("lesson_markdown", sa.Text(), nullable=False),
        sa.Column("openai_initial_response_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["agent_spec_id"], ["agent_specs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lesson_sessions_runtime_session_hash", "lesson_sessions", ["runtime_session_hash"])
    op.create_index("ix_lesson_sessions_share_slug", "lesson_sessions", ["share_slug"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lesson_session_id", sa.Uuid(), nullable=False),
        sa.Column("role", chat_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("openai_response_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_session_id"], ["lesson_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_lesson_session_id", "chat_messages", ["lesson_session_id"])

    op.create_table(
        "usage_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lesson_session_id", sa.Uuid(), nullable=False),
        sa.Column("openai_response_id", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_session_id"], ["lesson_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_events_lesson_session_id", "usage_events", ["lesson_session_id"])


def downgrade() -> None:
    op.drop_index("ix_usage_events_lesson_session_id", table_name="usage_events")
    op.drop_table("usage_events")
    op.drop_index("ix_chat_messages_lesson_session_id", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_lesson_sessions_share_slug", table_name="lesson_sessions")
    op.drop_index("ix_lesson_sessions_runtime_session_hash", table_name="lesson_sessions")
    op.drop_table("lesson_sessions")
    op.drop_index("ix_agent_specs_share_slug", table_name="agent_specs")
    op.drop_index("ix_agent_specs_owner_session_hash", table_name="agent_specs")
    op.drop_table("agent_specs")
    sa.Enum(name="chatrole").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="agentstatus").drop(op.get_bind(), checkfirst=True)
