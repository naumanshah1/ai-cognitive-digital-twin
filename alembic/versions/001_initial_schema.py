"""Initial schema creating users and agent execution records.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-10-21 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("api_key_hash", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_api_key_hash", "users", ["api_key_hash"], unique=False)

    # 2. Create agent_execution_records table
    op.create_table(
        "agent_execution_records",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("user_goal", sa.String(length=500), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("execution_mode", sa.String(length=32), nullable=False, server_default="llm"),
        sa.Column("execution_latency", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("tools_called", sa.JSON(), nullable=False),
        sa.Column("findings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recommendations_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("simulation_performed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verification_passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("findings_summary", sa.Text(), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index("ix_agent_execution_records_id", "agent_execution_records", ["id"], unique=False)
    op.create_index("ix_agent_execution_records_request_id", "agent_execution_records", ["request_id"], unique=True)
    op.create_index("ix_agent_execution_records_user_id", "agent_execution_records", ["user_id"], unique=False)
    op.create_index("ix_agent_execution_records_status", "agent_execution_records", ["status"], unique=False)
    op.create_index("ix_agent_execution_records_created_at", "agent_execution_records", ["created_at"], unique=False)
    op.create_index("ix_agent_exec_user_created", "agent_execution_records", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_exec_user_created", table_name="agent_execution_records")
    op.drop_index("ix_agent_execution_records_created_at", table_name="agent_execution_records")
    op.drop_index("ix_agent_execution_records_status", table_name="agent_execution_records")
    op.drop_index("ix_agent_execution_records_user_id", table_name="agent_execution_records")
    op.drop_index("ix_agent_execution_records_request_id", table_name="agent_execution_records")
    op.drop_index("ix_agent_execution_records_id", table_name="agent_execution_records")
    op.drop_table("agent_execution_records")

    op.drop_index("ix_users_api_key_hash", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
