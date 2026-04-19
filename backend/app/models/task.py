"""
统一任务中心模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from app.database import Base


class AnalysisTask(Base):
    """分析任务主表"""

    __tablename__ = "analysis_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, nullable=False, index=True)
    task_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    title = Column(String(200), nullable=False)
    payload_json = Column(Text, nullable=True)
    payload_summary_json = Column(Text, nullable=True)
    progress = Column(Integer, default=0)
    stage_code = Column(String(64), nullable=True)
    stage_message = Column(String(255), default="")
    progress_message = Column(String(500), default="")
    result_json = Column(Text, nullable=True)
    result_schema_version = Column(Integer, default=1)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=2)
    worker_id = Column(String(128), nullable=True)
    heartbeat_at = Column(DateTime, nullable=True)
    cancel_requested_at = Column(DateTime, nullable=True)
    source_page = Column(String(64), nullable=True)
    created_by = Column(Integer, nullable=True)
    idempotency_key = Column(String(128), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_analysis_tasks_status", "status"),
        Index("ix_analysis_tasks_type_conn", "task_type", "connection_id"),
        Index("ix_analysis_tasks_heartbeat", "heartbeat_at"),
        Index("ix_analysis_tasks_idempotency", "idempotency_key"),
    )


class AnalysisTaskEvent(Base):
    """分析任务事件流表"""

    __tablename__ = "analysis_task_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, nullable=False, index=True)
    seq = Column(Integer, nullable=False)
    event_type = Column(String(64), nullable=False)
    progress = Column(Integer, nullable=True)
    stage_code = Column(String(64), nullable=True)
    event_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_analysis_task_events_task_seq", "task_id", "seq", unique=True),
        Index("ix_analysis_task_events_task_created", "task_id", "created_at"),
    )
