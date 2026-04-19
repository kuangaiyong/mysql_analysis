"""task center refactor

Revision ID: 2026_04_18_task_center_refactor
Revises: phase3_remove_foreign_keys
Create Date: 2026-04-18 22:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "2026_04_18_task_center_refactor"
down_revision = "phase3_remove_foreign_keys"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    columns = inspector.get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("analysis_tasks"):
        op.create_table(
            "analysis_tasks",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("connection_id", sa.Integer(), nullable=False),
            sa.Column("task_type", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("payload_json", sa.Text(), nullable=True),
            sa.Column("payload_summary_json", sa.Text(), nullable=True),
            sa.Column("progress", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("stage_code", sa.String(length=64), nullable=True),
            sa.Column("stage_message", sa.String(length=255), nullable=True),
            sa.Column("progress_message", sa.String(length=500), nullable=True),
            sa.Column("result_json", sa.Text(), nullable=True),
            sa.Column("result_schema_version", sa.Integer(), nullable=True, server_default="1"),
            sa.Column("error_code", sa.String(length=64), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("max_retries", sa.Integer(), nullable=True, server_default="2"),
            sa.Column("worker_id", sa.String(length=128), nullable=True),
            sa.Column("heartbeat_at", sa.DateTime(), nullable=True),
            sa.Column("cancel_requested_at", sa.DateTime(), nullable=True),
            sa.Column("source_page", sa.String(length=64), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("idempotency_key", sa.String(length=128), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
    else:
        with op.batch_alter_table("analysis_tasks") as batch_op:
            additions = [
                ("payload_json", sa.Text()),
                ("payload_summary_json", sa.Text()),
                ("stage_code", sa.String(length=64)),
                ("stage_message", sa.String(length=255)),
                ("result_schema_version", sa.Integer()),
                ("error_code", sa.String(length=64)),
                ("worker_id", sa.String(length=128)),
                ("heartbeat_at", sa.DateTime()),
                ("cancel_requested_at", sa.DateTime()),
                ("source_page", sa.String(length=64)),
                ("created_by", sa.Integer()),
                ("idempotency_key", sa.String(length=128)),
            ]
            for column_name, column_type in additions:
                if not _has_column(inspector, "analysis_tasks", column_name):
                    batch_op.add_column(sa.Column(column_name, column_type, nullable=True))

    existing_indexes = {index["name"] for index in inspector.get_indexes("analysis_tasks")}
    if "ix_analysis_tasks_status" not in existing_indexes:
        op.create_index("ix_analysis_tasks_status", "analysis_tasks", ["status"], unique=False)
    if "ix_analysis_tasks_type_conn" not in existing_indexes:
        op.create_index("ix_analysis_tasks_type_conn", "analysis_tasks", ["task_type", "connection_id"], unique=False)
    if "ix_analysis_tasks_heartbeat" not in existing_indexes:
        op.create_index("ix_analysis_tasks_heartbeat", "analysis_tasks", ["heartbeat_at"], unique=False)
    if "ix_analysis_tasks_idempotency" not in existing_indexes:
        op.create_index("ix_analysis_tasks_idempotency", "analysis_tasks", ["idempotency_key"], unique=False)

    if not inspector.has_table("analysis_task_events"):
        op.create_table(
            "analysis_task_events",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("task_id", sa.Integer(), nullable=False),
            sa.Column("seq", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("progress", sa.Integer(), nullable=True),
            sa.Column("stage_code", sa.String(length=64), nullable=True),
            sa.Column("event_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_analysis_task_events_task_seq", "analysis_task_events", ["task_id", "seq"], unique=True)
        op.create_index("ix_analysis_task_events_task_created", "analysis_task_events", ["task_id", "created_at"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("analysis_task_events"):
        op.drop_index("ix_analysis_task_events_task_created", table_name="analysis_task_events")
        op.drop_index("ix_analysis_task_events_task_seq", table_name="analysis_task_events")
        op.drop_table("analysis_task_events")

    if inspector.has_table("analysis_tasks"):
        existing_indexes = {index["name"] for index in inspector.get_indexes("analysis_tasks")}
        if "ix_analysis_tasks_idempotency" in existing_indexes:
            op.drop_index("ix_analysis_tasks_idempotency", table_name="analysis_tasks")
        if "ix_analysis_tasks_heartbeat" in existing_indexes:
            op.drop_index("ix_analysis_tasks_heartbeat", table_name="analysis_tasks")

        existing_columns = {column["name"] for column in inspector.get_columns("analysis_tasks")}
        removable_columns = [
            "payload_json",
            "payload_summary_json",
            "stage_code",
            "stage_message",
            "result_schema_version",
            "error_code",
            "worker_id",
            "heartbeat_at",
            "cancel_requested_at",
            "source_page",
            "created_by",
            "idempotency_key",
        ]
        with op.batch_alter_table("analysis_tasks") as batch_op:
            for column_name in removable_columns:
                if column_name in existing_columns:
                    batch_op.drop_column(column_name)
