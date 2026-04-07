"""
查询指纹后台任务
"""

import logging
from app.tasks.celery import celery_app
from app.database import get_db, SessionLocal
from app.services.query_fingerprint import QueryFingerprintService

logger = logging.getLogger(__name__)


@celery_app.task(name="generate_query_fingerprints", bind=True)
def generate_query_fingerprints(task, connection_id: int) -> dict:
    """
    为指定连接生成查询指纹

    Args:
        task: Celery任务对象
        connection_id: 连接ID

    Returns:
        任务结果
    """
    logger.info(f"Starting fingerprint generation for connection_id={connection_id}")

    try:
        db = SessionLocal()
        try:
            service = QueryFingerprintService()
            fingerprints = service.generate_fingerprints(db, connection_id)
            logger.info(
                f"Generated {len(fingerprints)} fingerprints for connection_id={connection_id}"
            )

            return {
                "status": "success",
                "fingerprint_count": len(fingerprints),
                "updated_slow_queries": len(fingerprints),
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to generate fingerprints: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
        }
