"""
诊断会话与报告模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class DiagnosisSession(Base):
    """诊断会话"""
    __tablename__ = "diagnosis_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, nullable=False, index=True)
    session_type = Column(String(50), default="chat")  # chat / quick
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship(
        "DiagnosisMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DiagnosisMessage.created_at",
    )


class DiagnosisMessage(Base):
    """诊断消息"""
    __tablename__ = "diagnosis_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("diagnosis_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    context_snapshot = Column(Text, nullable=True)  # JSON 字符串
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("DiagnosisSession", back_populates="messages")


class DiagnosisReport(Base):
    """诊断报告"""
    __tablename__ = "diagnosis_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, nullable=False, index=True)
    report_type = Column(String(50), default="health_check")
    health_score = Column(Integer, default=0)  # 0-100
    content_json = Column(Text, nullable=False)  # 各维度分析文本 JSON
    dimensions_json = Column(Text, nullable=False)  # 维度评分 JSON
    created_at = Column(DateTime, default=datetime.utcnow)
