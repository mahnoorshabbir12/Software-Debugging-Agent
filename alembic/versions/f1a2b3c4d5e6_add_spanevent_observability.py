"""Add spanevent observability trace store (Module 21)

Revision ID: f1a2b3c4d5e6
Revises: 0b91bf26c85d
Create Date: 2026-08-24 11:05:00.000000

Note: this migration is intentionally additive and declares no ForeignKey to
debugsession. The pre-existing initial migration creates the older `investigation`
table rather than `debugsession`, and the running app materializes the current
models via SQLModel.metadata.create_all(). Keeping this migration FK-less lets
`alembic upgrade head` succeed regardless of that drift; the ORM model still
declares the relationship for runtime create_all.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "0b91bf26c85d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "spanevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("debug_session_id", sa.Integer(), nullable=True),
        sa.Column("trace_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("span_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("parent_span_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("kind", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("node", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("start_ts", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("end_ts", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("model", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("tool_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("input", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("output", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_spanevent_debug_session_id"), "spanevent", ["debug_session_id"], unique=False)
    op.create_index(op.f("ix_spanevent_trace_id"), "spanevent", ["trace_id"], unique=False)
    op.create_index(op.f("ix_spanevent_span_id"), "spanevent", ["span_id"], unique=False)
    op.create_index(op.f("ix_spanevent_created_at"), "spanevent", ["created_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_spanevent_created_at"), table_name="spanevent")
    op.drop_index(op.f("ix_spanevent_span_id"), table_name="spanevent")
    op.drop_index(op.f("ix_spanevent_trace_id"), table_name="spanevent")
    op.drop_index(op.f("ix_spanevent_debug_session_id"), table_name="spanevent")
    op.drop_table("spanevent")
