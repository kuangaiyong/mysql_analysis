"""Remove all foreign key constraints from all tables.

Revision ID: phase3_remove_foreign_keys
Revises: phase2_config_analysis_history
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "phase3_remove_foreign_keys"
down_revision = "phase2_config_analysis_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove all foreign key constraints."""
    
    # Drop foreign keys from alert_rules
    try:
        with op.batch_alter_table("alert_rules") as batch_op:
            batch_op.drop_constraint(
                "alert_rules_ibfk_1",
                type_="foreignkey"
            )
    except Exception:
        pass
    
    # Drop foreign keys from alert_history
    try:
        with op.batch_alter_table("alert_history") as batch_op:
            batch_op.drop_constraint(
                "alert_history_ibfk_1",
                type_="foreignkey"
            )
    except Exception:
        pass
    
    try:
        with op.batch_alter_table("alert_history") as batch_op:
            batch_op.drop_constraint(
                "alert_history_ibfk_2",
                type_="foreignkey"
            )
    except Exception:
        pass
    
    # Drop foreign keys from slow_queries
    try:
        with op.batch_alter_table("slow_queries") as batch_op:
            batch_op.drop_constraint(
                "slow_queries_ibfk_1",
                type_="foreignkey"
            )
    except Exception:
        pass
    
    # Drop foreign keys from performance_metrics
    try:
        with op.batch_alter_table("performance_metrics") as batch_op:
            batch_op.drop_constraint(
                "performance_metrics_ibfk_1",
                type_="foreignkey"
            )
    except Exception:
        pass
    
    # Drop foreign keys from reports
    try:
        with op.batch_alter_table("reports") as batch_op:
            batch_op.drop_constraint(
                "reports_ibfk_1",
                type_="foreignkey"
            )
    except Exception:
        pass
    
    # Drop foreign keys from query_fingerprints
    # query_fingerprints table has no foreign keys in current database
    # No action needed
    
    # Drop foreign keys from wait_events_cache
    try:
        with op.batch_alter_table("wait_events_cache") as batch_op:
            batch_op.drop_constraint(
                "wait_events_cache_ibfk_1",
                type_="foreignkey"
            )
    except Exception:
        pass
    
    # Drop foreign keys from index_suggestions
    try:
        with op.batch_alter_table("index_suggestions") as batch_op:
            batch_op.drop_constraint(
                "index_suggestions_ibfk_1",
                type_="foreignkey"
            )
    except Exception:
        pass
    
    # Drop foreign keys from config_analysis_history
    try:
        with op.batch_alter_table("config_analysis_history") as batch_op:
            batch_op.drop_constraint(
                "config_analysis_history_ibfk_1",
                type_="foreignkey"
            )
    except Exception:
        pass


def downgrade() -> None:
    """Add back all foreign key constraints."""
    
    # Add foreign keys to alert_rules
    with op.batch_alter_table("alert_rules") as batch_op:
        batch_op.create_foreign_key(
            "connection_id",
            "connections",
            ["id"],
            name="alert_rules_ibfk_1",
            ondelete="CASCADE"
        )
    
    # Add foreign keys to alert_history
    with op.batch_alter_table("alert_history") as batch_op:
        batch_op.create_foreign_key(
            "alert_rule_id",
            "alert_rules",
            ["id"],
            name="alert_history_ibfk_1",
            ondelete="CASCADE"
        )
        batch_op.create_foreign_key(
            "connection_id",
            "connections",
            ["id"],
            name="alert_history_ibfk_2",
            ondelete="CASCADE"
        )
    
    # Add foreign keys to slow_queries
    with op.batch_alter_table("slow_queries") as batch_op:
        batch_op.create_foreign_key(
            "connection_id",
            "connections",
            ["id"],
            name="slow_queries_ibfk_1",
            ondelete="CASCADE"
        )
    
    # Add foreign keys to performance_metrics
    with op.batch_alter_table("performance_metrics") as batch_op:
        batch_op.create_foreign_key(
            "connection_id",
            "connections",
            ["id"],
            name="performance_metrics_ibfk_1",
            ondelete="CASCADE"
        )
    
    # Add foreign keys to reports
    with op.batch_alter_table("reports") as batch_op:
        batch_op.create_foreign_key(
            "connection_id",
            "connections",
            ["id"],
            name="reports_ibfk_1",
            ondelete="CASCADE"
        )
    
    # Add foreign keys to query_fingerprints
    with op.batch_alter_table("query_fingerprints") as batch_op:
        batch_op.create_foreign_key(
            "connection_id",
            "connections",
            ["id"],
            name="query_fingerprints_ibfk_1",
            ondelete="CASCADE"
        )
    
    # Add foreign keys to wait_events_cache
    with op.batch_alter_table("wait_events_cache") as batch_op:
        batch_op.create_foreign_key(
            "connection_id",
            "connections",
            ["id"],
            name="wait_events_cache_ibfk_1",
            ondelete="CASCADE"
        )
    
    # Add foreign keys to index_suggestions
    with op.batch_alter_table("index_suggestions") as batch_op:
        batch_op.create_foreign_key(
            "connection_id",
            "connections",
            ["id"],
            name="index_suggestions_ibfk_1",
            ondelete="CASCADE"
        )
    
    # Add foreign keys to config_analysis_history
    with op.batch_alter_table("config_analysis_history") as batch_op:
        batch_op.create_foreign_key(
            "connection_id",
            "connections",
            ["id"],
            name="config_analysis_history_ibfk_1",
            ondelete="CASCADE"
        )
