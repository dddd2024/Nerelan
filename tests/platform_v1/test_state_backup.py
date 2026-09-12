from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import stat

import pytest

import reverse_agent.platform_v1.state_backup as state_backup
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.state_backup import BACKUP_FORMAT, StateBackupService


def _populate(store: TaskStore):
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)
    task = store.create_task(
        title="TOP-SECRET-TASK-TITLE",
        repository="dddd2024/Nerelan",
        idempotency_key="backup-task",
    )
    goal = goals.create(
        {
            "title": "Backup test",
            "objective": "TOP-SECRET-GOAL-OBJECTIVE",
            "repository": "dddd2024/Nerelan",
            "idempotency_key": "backup-goal",
        }
    )
    return task, goal


def _read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)


def _valid_backup(tmp_path: Path, *, file_backed: bool = False):
    source = tmp_path / "source-secret-location.sqlite3"
    store = TaskStore(db_path=str(source)) if file_backed else TaskStore(":memory:")
    task, goal = _populate(store)
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)
    return store, service, target, manifest, task, goal


def _manifest_path(target: Path) -> Path:
    return Path(str(target) + state_backup.MANIFEST_SUFFIX)


def _rewrite_manifest(target: Path, mutate) -> None:
    path = _manifest_path(target)
    raw = json.loads(path.read_text(encoding="utf-8"))
    mutate(raw)
    path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def test_in_memory_backup_preserves_representative_task_and_goal(tmp_path):
    store, service, target, manifest, task, goal = _valid_backup(tmp_path)
    assert manifest.format == BACKUP_FORMAT
    assert manifest.schema_sha256 == service.current_schema_sha256()
    assert manifest.raw_external_credentials_included is False

    conn = _read_only(target)
    try:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT id FROM tasks WHERE id = ?", (task.id,)).fetchone()[0] == task.id
        assert conn.execute("SELECT id FROM platform_goals WHERE id = ?", (goal.id,)).fetchone()[0] == goal.id
    finally:
        conn.close()


def test_file_backed_backup_and_verification_are_zero_write_on_source(tmp_path):
    source = tmp_path / "source.sqlite3"
    store = TaskStore(db_path=str(source))
    _populate(store)
    service = StateBackupService(store)
    before = store._conn.total_changes
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)
    assert store._conn.total_changes == before
    assert service.verify_backup(target) == manifest
    assert store._conn.total_changes == before


def test_manifest_round_trips_exact_database_and_schema_metadata(tmp_path):
    _, service, target, manifest, _, _ = _valid_backup(tmp_path)
    verified = service.verify_backup(target, expected_schema_sha256=manifest.schema_sha256)
    assert verified.database_sha256 == state_backup._sha256_file(target)
    assert verified.schema_sha256 == service.current_schema_sha256()
    conn = _read_only(target)
    try:
        assert verified.sqlite_user_version == conn.execute("PRAGMA user_version").fetchone()[0]
        assert verified.page_size == conn.execute("PRAGMA page_size").fetchone()[0]
        assert verified.page_count == conn.execute("PRAGMA page_count").fetchone()[0]
    finally:
        conn.close()


def test_manifest_contains_only_closed_metadata_and_no_state_content_or_source_path(tmp_path):
    store, _, target, _, _, _ = _valid_backup(tmp_path, file_backed=True)
    text = _manifest_path(target).read_text(encoding="utf-8")
    raw = json.loads(text)
    assert set(raw) == state_backup._MANIFEST_FIELDS
    assert "TOP-SECRET-TASK-TITLE" not in text
    assert "TOP-SECRET-GOAL-OBJECTIVE" not in text
    assert str(Path(store._path).resolve()) not in text
    assert "source-secret-location" not in text


def test_source_active_transaction_fails_closed_without_ending_caller_transaction(tmp_path):
    store = TaskStore(":memory:")
    _populate(store)
    service = StateBackupService(store)
    store._conn.execute("BEGIN")
    store._conn.execute("CREATE TABLE caller_uncommitted_probe(value TEXT)")
    try:
        with pytest.raises(TaskStoreError, match="state_backup_source_transaction_active"):
            service.create_backup(tmp_path / "backup.sqlite3")
        assert store._conn.in_transaction is True
        assert store._conn.execute(
            "SELECT name FROM sqlite_master WHERE name='caller_uncommitted_probe'"
        ).fetchone() is not None
    finally:
        store._conn.execute("ROLLBACK")
    assert store._conn.execute(
        "SELECT name FROM sqlite_master WHERE name='caller_uncommitted_probe'"
    ).fetchone() is None


def test_source_database_cannot_be_used_as_backup_target(tmp_path):
    source = tmp_path / "source.sqlite3"
    store = TaskStore(db_path=str(source))
    _populate(store)
    with pytest.raises(TaskStoreError, match="state_backup_target_is_source_database"):
        StateBackupService(store).create_backup(source)


def test_existing_target_or_sidecar_fails_closed(tmp_path):
    store = TaskStore(":memory:")
    _populate(store)
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    target.write_bytes(b"existing")
    with pytest.raises(TaskStoreError, match="state_backup_target_exists"):
        service.create_backup(target)
    target.unlink()
    _manifest_path(target).write_text("{}", encoding="utf-8")
    with pytest.raises(TaskStoreError, match="state_backup_manifest_exists"):
        service.create_backup(target)


def test_symlink_destination_is_rejected(tmp_path):
    store = TaskStore(":memory:")
    _populate(store)
    target = tmp_path / "backup.sqlite3"
    real = tmp_path / "real.sqlite3"
    real.write_bytes(b"x")
    try:
        target.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(TaskStoreError, match="state_backup_symlink_target_forbidden"):
        StateBackupService(store).create_backup(target)


def test_verify_rejects_symlink_database(tmp_path):
    _, service, target, _, _, _ = _valid_backup(tmp_path)
    real = tmp_path / "real-backup.sqlite3"
    target.replace(real)
    try:
        target.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(TaskStoreError, match="state_backup_symlink_database_forbidden"):
        service.verify_backup(target)


def test_missing_manifest_is_never_accepted(tmp_path):
    _, service, target, _, _, _ = _valid_backup(tmp_path)
    _manifest_path(target).unlink()
    with pytest.raises(TaskStoreError, match="state_backup_manifest_missing"):
        service.verify_backup(target)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda raw: raw.__setitem__("unexpected", "x"), "state_backup_manifest_fields_invalid"),
        (lambda raw: raw.__setitem__("database_sha256", "0" * 64), "state_backup_database_digest_mismatch"),
        (lambda raw: raw.__setitem__("schema_sha256", "0" * 64), "state_backup_schema_digest_mismatch"),
        (lambda raw: raw.__setitem__("page_count", raw["page_count"] + 1), "state_backup_page_metadata_mismatch"),
        (lambda raw: raw.__setitem__("raw_external_credentials_included", True), "state_backup_manifest_credentials_invalid"),
    ],
)
def test_manifest_tampering_fails_closed(tmp_path, mutation, message):
    _, service, target, _, _, _ = _valid_backup(tmp_path)
    _rewrite_manifest(target, mutation)
    with pytest.raises(TaskStoreError, match=message):
        service.verify_backup(target)


def test_duplicate_manifest_field_fails_closed(tmp_path):
    _, service, target, _, _, _ = _valid_backup(tmp_path)
    path = _manifest_path(target)
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace('"format":', '"format":"duplicate","format":', 1), encoding="utf-8")
    with pytest.raises(TaskStoreError, match="state_backup_manifest_duplicate_field"):
        service.verify_backup(target)


def test_malformed_or_oversized_manifest_fails_closed(tmp_path):
    _, service, target, _, _, _ = _valid_backup(tmp_path)
    path = _manifest_path(target)
    path.write_text("{", encoding="utf-8")
    with pytest.raises(TaskStoreError, match="state_backup_manifest_invalid"):
        service.verify_backup(target)
    path.write_bytes(b"x" * (state_backup.MAX_MANIFEST_BYTES + 1))
    with pytest.raises(TaskStoreError, match="state_backup_manifest_size_invalid"):
        service.verify_backup(target)


def test_database_tampering_or_truncation_fails_digest_before_acceptance(tmp_path):
    _, service, target, _, _, _ = _valid_backup(tmp_path)
    with target.open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(TaskStoreError, match="state_backup_database_digest_mismatch"):
        service.verify_backup(target)

    # A fresh artifact that is physically truncated must also be rejected.
    root2 = tmp_path / "second"
    root2.mkdir()
    _, service2, target2, _, _, _ = _valid_backup(root2)
    data = target2.read_bytes()
    target2.write_bytes(data[: max(1, len(data) // 2)])
    with pytest.raises(TaskStoreError, match="state_backup_database_digest_mismatch"):
        service2.verify_backup(target2)


def test_expected_schema_mismatch_fails_closed(tmp_path):
    _, service, target, _, _, _ = _valid_backup(tmp_path)
    with pytest.raises(TaskStoreError, match="state_backup_schema_incompatible"):
        service.verify_backup(target, expected_schema_sha256="0" * 64)
    with pytest.raises(TaskStoreError, match="state_backup_expected_schema_invalid"):
        service.verify_backup(target, expected_schema_sha256="not-a-digest")


def test_handled_pre_manifest_failure_leaves_no_accepted_or_partial_artifact(tmp_path, monkeypatch):
    store = TaskStore(":memory:")
    _populate(store)
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"

    def fail_inspection(conn):
        raise TaskStoreError("injected_backup_inspection_failure")

    monkeypatch.setattr(state_backup, "_inspect_database", fail_inspection)
    with pytest.raises(TaskStoreError, match="injected_backup_inspection_failure"):
        service.create_backup(target)
    assert not target.exists()
    assert not _manifest_path(target).exists()
    assert not list(tmp_path.glob(".nerelan-state-backup-*"))


def test_backup_and_manifest_are_owner_only_on_posix(tmp_path):
    if os.name == "nt":
        pytest.skip("POSIX mode bits unavailable")
    _, _, target, _, _, _ = _valid_backup(tmp_path)
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert stat.S_IMODE(_manifest_path(target).stat().st_mode) == 0o600