import json
from types import SimpleNamespace

from app.crud import task as task_crud
from app.models.task import AnalysisTask, AnalysisTaskEvent


def test_task_creation_and_event(db_session):
    task = task_crud.create_task(
        db=db_session,
        connection_id=1,
        task_type='index_advisor',
        payload={'connection_id': 1},
        payload_summary={'connection_id': 1},
    )

    assert task.id is not None
    assert task.status == 'pending'

    events = task_crud.list_task_events(db_session, task.id)
    assert len(events) == 1
    assert events[0].event_type == 'task_created'


def test_cancel_request_does_not_immediately_complete_running_task(db_session):
    task = task_crud.create_task(db_session, 1, 'lock_analysis')
    task = task_crud.update_task_status(
        db_session,
        task.id,
        'running',
        progress=20,
        stage_code='analysis',
        stage_message='执行中',
        force=True,
    )

    updated = task_crud.request_cancel(db_session, task.id)
    assert updated is not None
    assert updated.status == 'cancel_requested'
    assert updated.cancel_requested_at is not None


def test_update_task_result_builds_success_state(db_session):
    task = task_crud.create_task(db_session, 1, 'slow_query_patrol')
    task_crud.update_task_result(
        db_session,
        task.id,
        {'task_type': 'slow_query_patrol', 'renderer_key': 'slow_query_patrol', 'structured': {'issues': []}},
    )
    saved = task_crud.get_task(db_session, task.id)
    assert saved is not None
    assert saved.status == 'success'
    assert saved.progress == 100


def test_task_progress_persisted_in_db(db_session):
    task = task_crud.create_task(db_session, 1, 'config_tuning')
    task_crud.update_task_progress(
        db_session,
        task.id,
        0,
        '准备开始',
        stage_code='queued',
        event_payload={'message': '准备开始'},
    )
    saved = task_crud.get_task(db_session, task.id)
    assert saved is not None
    assert saved.progress == 0
    assert saved.progress_message == '准备开始'


def test_task_counts_by_status(db_session):
    task1 = task_crud.create_task(db_session, 1, 'index_advisor')
    task2 = task_crud.create_task(db_session, 1, 'lock_analysis')
    task_crud.update_task_status(db_session, task1.id, 'running', stage_code='running', stage_message='执行中', force=True)
    task_crud.update_task_status(db_session, task2.id, 'failed', error_message='失败', stage_code='failed', stage_message='失败', force=True)

    counts = task_crud.get_task_counts_by_status(db_session, connection_id=1)
    assert counts['running'] == 1
    assert counts['failed'] == 1


def test_task_models_registered():
    assert AnalysisTask.__tablename__ == 'analysis_tasks'
    assert AnalysisTaskEvent.__tablename__ == 'analysis_task_events'
