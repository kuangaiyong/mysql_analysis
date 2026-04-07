"""Add query_fingerprints, wait_events_cache, and index_suggestions tables. Extend slow_queries table.

Revision ID: phase1_core_enhancements
Revises: phase1_core_enhancements
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "phase1_core_enhancements"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema to include new Phase 1 tables and extend slow_queries."""
    metadata = sa.MetaData()
    metadata.reflect(bind=op.get_bind())

    # Create query_fingerprints table
    if "query_fingerprints" not in metadata.tables:
        op.create_table(
            "query_fingerprints",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column(
                "fingerprint_hash",
                sa.String(64),
                unique=True,
                nullable=False,
                index=True,
                comment="MD5 fingerprint hash",
            ),
            sa.Column(
                "normalized_sql", sa.Text(), nullable=False, comment="Normalized SQL"
            ),
            sa.Column(
                "table_name",
                sa.String(100),
                nullable=True,
                comment="Table name involved",
            ),
            sa.Column(
                "execution_count", sa.Integer(), default=1, comment="Execution count"
            ),
            sa.Column(
                "avg_query_time",
                sa.Numeric(10, 6),
                comment="Average query time (seconds)",
            ),
            sa.Column(
                "max_query_time",
                sa.Numeric(10, 6),
                comment="Maximum query time (seconds)",
            ),
            sa.Column(
                "min_query_time",
                sa.Numeric(10, 6),
                comment="Minimum query time (seconds)",
            ),
            sa.Column(
                "total_rows_examined", sa.Integer(), comment="Total rows scanned"
            ),
            sa.Column("last_seen", sa.DateTime(), comment="Last execution time"),
            sa.Column("first_seen", sa.DateTime(), comment="First execution time"),
            sa.Column(
                "created_at",
                sa.DateTime(),
                default=sa.func.now(),
                comment="Record creation time",
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                default=sa.func.now(),
                onupdate=sa.func.now(),
                comment="Record update time",
            ),
        )

    # Create wait_events_cache table
    if "wait_events_cache" not in metadata.tables:
        op.create_table(
            "wait_events_cache",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column(
                "connection_id",
                sa.BigInteger(),
                sa.ForeignKey("connections.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "event_name", sa.String(100), nullable=False, comment="Event name"
            ),
            sa.Column(
                "event_class", sa.String(50), nullable=False, comment="Event class"
            ),
            sa.Column("wait_time", sa.Numeric(10, 6), comment="Wait time (seconds)"),
            sa.Column("wait_count", sa.Integer(), comment="Wait count"),
            sa.Column(
                "timestamp",
                sa.DateTime(),
                default=sa.func.now(),
                comment="Event timestamp",
            ),
            sa.Column(
                "details", sa.Text(), nullable=True, comment="Event details (JSON)"
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                default=sa.func.now(),
                comment="Record creation time",
            ),
        )

    # Create index_suggestions table
    if "index_suggestions" not in metadata.tables:
        op.create_table(
            "index_suggestions",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column(
                "connection_id",
                sa.BigInteger(),
                sa.ForeignKey("connections.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "table_name", sa.String(100), nullable=False, comment="Table name"
            ),
            sa.Column(
                "column_names",
                sa.Text(),
                nullable=False,
                comment="Index columns (comma-separated)",
            ),
            sa.Column(
                "index_type",
                sa.String(50),
                nullable=False,
                comment="Index type (BTREE, HASH, FULLTEXT)",
            ),
            sa.Column(
                "suggestion_type",
                sa.String(50),
                nullable=False,
                comment="Suggestion type (single, composite)",
            ),
            sa.Column(
                "estimated_rows_reduction",
                sa.Numeric(5, 2),
                comment="Estimated rows reduction %",
            ),
            sa.Column(
                "estimated_time_improvement",
                sa.Numeric(5, 2),
                comment="Estimated time improvement %",
            ),
            sa.Column(
                "confidence_level",
                sa.String(20),
                nullable=False,
                comment="Confidence level (high, medium, low)",
            ),
            sa.Column("status", sa.String(20), default="pending", comment="Status"),
            sa.Column("reason", sa.Text(), nullable=True, comment="Reason"),
            sa.Column(
                "sql_statement", sa.Text(), nullable=False, comment="CREATE INDEX SQL"
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                default=sa.func.now(),
                comment="Creation time",
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                default=sa.func.now(),
                onupdate=sa.func.now(),
                comment="Update time",
            ),
        )

    # Extend slow_queries table with new columns
    if "slow_queries" in metadata.tables:
        # Add fingerprint_id column
        with op.batch_alter_table("slow_queries") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "fingerprint_id",
                    sa.BigInteger(),
                    sa.ForeignKey("query_fingerprints.id"),
                    nullable=True,
                )
            )

        # Add resource_snapshot column
        with op.batch_alter_table("slow_queries") as batch_op:
            batch_op.add_column(
                sa.Column("resource_snapshot", sa.Text(), nullable=True)
            )

        # Create indexes for slow_queries
        with op.batch_alter_table("slow_queries") as batch_op:
            batch_op.create_index("idx_fingerprint_id", ["fingerprint_id"])


def downgrade() -> None:
    """Downgrade schema to remove Phase 1 tables and columns."""
    # Remove indexes from query_fingerprints
    if "query_fingerprints" in metadata.tables:
        op.drop_index("idx_fingerprint_hash", table_name="query_fingerprints")

    # Remove indexes from slow_queries
    op.drop_index("idx_fingerprint_id", table_name="slow_queries")

    # Drop columns from slow_queries
    if "slow_queries" in metadata.tables:
        with op.batch_alter_table("slow_queries") as batch_op:
            batch_op.drop_column("fingerprint_id")

        with op.batch_alter_table("slow_queries") as batch_op:
            batch_op.drop_column("resource_snapshot")

    # Drop new tables
    op.drop_table("index_suggestions")
    op.drop_table("wait_events_cache")
    op.drop_table("query_fingerprints")
