"""
配置分析后台任务
"""

import logging
from datetime import datetime, timedelta, timezone
from app.tasks.celery import celery_app
from app.database import SessionLocal
from app.models.config_analysis import ConfigAnalysisHistory

logger = logging.getLogger(__name__)


@celery_app.task(name="cleanup_old_config_analyses", bind=True)
def cleanup_old_config_analyses(task) -> dict:
    """
    清理7天前的配置分析历史数据

    Args:
        task: Celery任务对象

    Returns:
        任务结果
    """
    logger.info("Starting cleanup of old config analysis history")

    try:
        db = SessionLocal()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

            # 使用批量删除避免 N+1 问题
            result = db.query(ConfigAnalysisHistory).filter(
                ConfigAnalysisHistory.analysis_timestamp < cutoff_date
            ).delete()
            
            db.commit()
            
            record_count = result

            if record_count > 0:
                logger.info(
                    f"Cleaned up {record_count} old config analysis records "
                    f"(older than {cutoff_date.isoformat()})"
                )

                return {
                    "status": "success",
                    "cleaned_records": record_count,
                    "cutoff_date": cutoff_date.isoformat(),
                }
            else:
                logger.info("No old config analysis records to clean up")
                return {
                    "status": "success",
                    "cleaned_records": 0,
                    "message": "No records older than 7 days",
                }

        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to cleanup old config analyses: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
        }
