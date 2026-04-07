"""
诊断会话与报告 CRUD 操作
"""

import json
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.diagnosis import DiagnosisSession, DiagnosisMessage, DiagnosisReport


# ==================== 会话 CRUD ====================

def create_session(
    db: Session,
    connection_id: int,
    session_type: str = "chat",
    title: str = "新对话"
) -> DiagnosisSession:
    """创建诊断会话"""
    session = DiagnosisSession(
        connection_id=connection_id,
        session_type=session_type,
        title=title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: int) -> Optional[DiagnosisSession]:
    """获取单个会话"""
    return db.execute(
        select(DiagnosisSession).where(DiagnosisSession.id == session_id)
    ).scalar_one_or_none()


def get_sessions(
    db: Session,
    connection_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[DiagnosisSession]:
    """获取会话列表（按更新时间倒序）"""
    return list(
        db.execute(
            select(DiagnosisSession)
            .where(DiagnosisSession.connection_id == connection_id)
            .order_by(DiagnosisSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        ).scalars().all()
    )


def count_sessions(db: Session, connection_id: int) -> int:
    """统计会话数量"""
    result = db.execute(
        select(func.count(DiagnosisSession.id))
        .where(DiagnosisSession.connection_id == connection_id)
    ).scalar()
    return result or 0


def update_session_title(
    db: Session, session_id: int, title: str
) -> Optional[DiagnosisSession]:
    """更新会话标题"""
    session = get_session(db, session_id)
    if not session:
        return None
    session.title = title
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, session_id: int) -> bool:
    """删除会话（级联删除消息）"""
    session = get_session(db, session_id)
    if not session:
        return False
    db.delete(session)
    db.commit()
    return True


# ==================== 消息 CRUD ====================

def add_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    context_snapshot: Optional[str] = None
) -> DiagnosisMessage:
    """添加消息到会话"""
    message = DiagnosisMessage(
        session_id=session_id,
        role=role,
        content=content,
        context_snapshot=context_snapshot,
    )
    db.add(message)
    # 更新会话的 updated_at
    session = get_session(db, session_id)
    if session:
        from datetime import datetime
        session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    return message


def get_session_messages(
    db: Session, session_id: int, limit: int = 100
) -> List[DiagnosisMessage]:
    """获取会话消息列表"""
    return list(
        db.execute(
            select(DiagnosisMessage)
            .where(DiagnosisMessage.session_id == session_id)
            .order_by(DiagnosisMessage.created_at.asc())
            .limit(limit)
        ).scalars().all()
    )


def count_messages(db: Session, session_id: int) -> int:
    """统计会话消息数"""
    result = db.execute(
        select(func.count(DiagnosisMessage.id))
        .where(DiagnosisMessage.session_id == session_id)
    ).scalar()
    return result or 0


# ==================== 报告 CRUD ====================

def create_report(
    db: Session,
    connection_id: int,
    health_score: int,
    content_json: str,
    dimensions_json: str,
    report_type: str = "health_check"
) -> DiagnosisReport:
    """创建诊断报告"""
    report = DiagnosisReport(
        connection_id=connection_id,
        report_type=report_type,
        health_score=health_score,
        content_json=content_json,
        dimensions_json=dimensions_json,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: int) -> Optional[DiagnosisReport]:
    """获取单个报告"""
    return db.execute(
        select(DiagnosisReport).where(DiagnosisReport.id == report_id)
    ).scalar_one_or_none()


def get_reports(
    db: Session, connection_id: int, limit: int = 20
) -> List[DiagnosisReport]:
    """获取报告列表"""
    return list(
        db.execute(
            select(DiagnosisReport)
            .where(DiagnosisReport.connection_id == connection_id)
            .order_by(DiagnosisReport.created_at.desc())
            .limit(limit)
        ).scalars().all()
    )


def delete_report(db: Session, report_id: int) -> bool:
    """删除报告"""
    report = get_report(db, report_id)
    if not report:
        return False
    db.delete(report)
    db.commit()
    return True
