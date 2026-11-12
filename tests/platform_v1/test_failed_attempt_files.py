"""A failed attempt keeps the files it changed, so the run page does not say "0 files"."""
from reverse_agent.platform_v1.durable_execution import DurableExecutionService, reset_crash_seam

from test_durable_execution_v5 import FakeSingleExecutor, _init_git_worktree, _matching_source_dir, _make_router, _make_store


def _run(tmp_path, fake):
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(title="edit product", executor_kind="opencode", orchestration_mode="single")
    service = DurableExecutionService(store=store, router=_make_router(fake),
                                      execution_authority_sha="test_authority", planning_sha="test_planning")
    outcome = service.execute_durable_single(task_id=task.id, workspace_root=str(_init_git_worktree(tmp_path)),
                                             lease_owner="test")
    return outcome, store.get_task(task.id)


def test_failed_attempt_records_its_changed_files(tmp_path, _matching_source_dir):
    outcome, task = _run(tmp_path, FakeSingleExecutor(success=False, validation_exit_code=-1))
    assert outcome.success is False
    assert task.status == "FAILED"
    assert [f["path"] for f in task.changed_files] == ["product.py"]


def test_failed_attempt_without_readable_files_stays_empty(tmp_path, _matching_source_dir):
    fake = FakeSingleExecutor(success=False, validation_exit_code=-1)
    original = fake.execute_role_prepared

    def unreadable(*args, **kwargs):
        result = original(*args, **kwargs)
        result.changed_files = []  # e.g. cleanup unconfirmed: the tree was not read
        return result

    fake.execute_role_prepared = unreadable
    outcome, task = _run(tmp_path, fake)
    assert outcome.success is False
    assert list(task.changed_files) == []
