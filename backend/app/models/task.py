"""
分析任务模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index

from app.database import Base


class AnalysisTask(Base):
    """分析任务"""
    __tablename__ = "analysis_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, nullable=False, index=True)
    task_type = Column(String(50), nullable=False)  # health_report / index_advisor / lock_analysis / slow_query_patrol / config_tuning / capacity_prediction
    status = Column(String(20), nullable=False, default="pending")  # pending / running / success / failed / cancelled
    title = Column(String(200), nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    progress_message = Column(String(500), default="")
    result_json = Column(Text, nullable=True)  # 分析结果 JSON
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=2)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_analysis_tasks_status", "status"),
        Index("ix_analysis_tasks_type_conn", "task_type", "connection_id"),
    )
