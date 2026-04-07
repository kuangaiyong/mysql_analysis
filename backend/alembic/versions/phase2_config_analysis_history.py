"""Add config_analysis_history table.

Revision ID: phase2_config_analysis_history
Revises: phase1_core_enhancements
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "phase2_config_analysis_history"
down_revision = "phase1_core_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema to include config_analysis_history table."""
    metadata = sa.MetaData()
    metadata.reflect(bind=op.get_bind())
    inspector = sa.inspect(op.get_bind())

    # Create config_analysis_history table
    if "config_analysis_history" not in metadata.tables:
        op.create_table(
            "config_analysis_history",
            sa.Column(
                "id",
                sa.BigInteger(),
                primary_key=True,
                autoincrement=True,
                comment="主键ID",
            ),
            sa.Column(
                "connection_id",
                sa.BigInteger(),
                sa.ForeignKey("connections.id", ondelete="CASCADE"),
                nullable=False,
                comment="连接ID",
            ),
            sa.Column(
                "analysis_timestamp",
                sa.DateTime(),
                nullable=False,
                comment="分析时间戳",
            ),
            sa.Column("health_score", sa.Integer(), comment="健康评分(0-100)"),
            sa.Column(
                "critical_count", sa.Integer(), default=0, comment="严重问题数量"
            ),
            sa.Column("warning_count", sa.Integer(), default=0, comment="警告问题数量"),
            sa.Column("info_count", sa.Integer(), default=0, comment="信息问题数量"),
            sa.Column("violations", sa.JSON(), comment="违规列表"),
            sa.Column("config_summary", sa.JSON(), comment="配置摘要"),
            sa.Column("mysql_version", sa.String(20), comment="MySQL版本"),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                default=sa.func.now(),
                comment="创建时间",
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                default=sa.func.now(),
                onupdate=sa.func.now(),
                comment="更新时间",
            ),
        )

    # Create indexes for config_analysis_history (idempotent - check if they exist first)
    if "config_analysis_history" in metadata.tables:
        existing_indexes = [
            idx["name"] for idx in inspector.get_indexes("config_analysis_history")
        ]
        with op.batch_alter_table("config_analysis_history") as batch_op:
            if "idx_connection_id" not in existing_indexes:
                batch_op.create_index("idx_connection_id", ["connection_id"])
            if "idx_analysis_timestamp" not in existing_indexes:
                batch_op.create_index("idx_analysis_timestamp", ["analysis_timestamp"])
            if "idx_connection_time" not in existing_indexes:
                batch_op.create_index(
                    "idx_connection_time", ["connection_id", "analysis_timestamp"]
                )


def downgrade() -> None:
    """Downgrade schema to remove config_analysis_history table."""
    # Drop indexes from config_analysis_history
    op.drop_index("idx_connection_time", table_name="config_analysis_history")
    op.drop_index("idx_analysis_timestamp", table_name="config_analysis_history")
    op.drop_index("idx_connection_id", table_name="config_analysis_history")

    # Drop config_analysis_history table
    op.drop_table("config_analysis_history")
