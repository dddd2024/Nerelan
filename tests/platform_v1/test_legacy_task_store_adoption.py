"""One-time adoption of the pre-host-owned checkout TaskStore (follow-up to #1117)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_service import (
    LegacyTaskStoreAdoptionError,
    adopt_legacy_task_store,
)

_DEV_UP = (Path(__file__).resolve().parents[2] / "dev-up.ps1").read_text(encoding="utf-8")


def _legacy_store_with_task(path: Path, title: str = "legacy history") -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    store = TaskStore(db_path=str(path))
    task = store.create_task(title=title, executor_kind="deterministic_fixture")
    store._conn.close()
    return task.id


def _isolate(monkeypatch, tmp_path: Path) -> None:
    for key in ("REVERSE_AGENT_TASK_DB_PATH", "REVERSE_AGENT_TASK_DB_DIR", "REVERSE_AGENT_LEGACY_TASK_DB_PATH"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "user-data"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "user-data"))


def test_absent_target_adopts_consistent_copy_and_leaves_legacy_untouched(tmp_path):
    legacy = tmp_path / "checkout" / ".platform_v1_runtime" / "tasks.sqlite3"
    task_id = _legacy_store_with_task(legacy)
    before = legacy.read_bytes()
    target = tmp_path / "user-data" / "Nerelan" / "platform-v1" / "tasks.sqlite3"

    assert adopt_legacy_task_store(str(target), str(legacy)) == "adopted"

    assert legacy.read_bytes() == before
    adopted = TaskStore(db_path=str(target))
    try:
        assert adopted.get_task(task_id).title == "legacy history"
    finally:
        adopted._conn.close()
    assert not list(target.parent.glob("*.adopting-*"))


def test_uncheckpointed_wal_content_is_included(tmp_path):
    legacy = tmp_path / "legacy.sqlite3"
    writer = sqlite3.connect(legacy)
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("PRAGMA wal_autocheckpoint=0")
    writer.execute("CREATE TABLE tasks (v TEXT)")
    writer.execute("INSERT INTO tasks VALUES ('only-in-wal')")
    writer.commit()
    assert Path(str(legacy) + "-wal").stat().st_size > 0
    target = tmp_path / "out" / "tasks.sqlite3"
    try:
        assert adopt_legacy_task_store(str(target), str(legacy)) == "adopted"
    finally:
        writer.close()
    reader = sqlite3.connect(target)
    try:
        assert reader.execute("SELECT v FROM tasks").fetchall() == [("only-in-wal",)]
    finally:
        reader.close()


def test_existing_target_is_never_overwritten(tmp_path):
    legacy = tmp_path / "legacy.sqlite3"
    _legacy_store_with_task(legacy, "old")
    target = tmp_path / "target.sqlite3"
    current_id = _legacy_store_with_task(target, "current")
    before = target.read_bytes()

    assert adopt_legacy_task_store(str(target), str(legacy)) == "target_exists"
    assert target.read_bytes() == before
    store = TaskStore(db_path=str(target))
    try:
        assert store.get_task(current_id).title == "current"
    finally:
        store._conn.close()


@pytest.mark.parametrize("legacy_name", ["", "missing.sqlite3"])
def test_unrequested_or_absent_legacy_does_nothing(tmp_path, legacy_name):
    target = tmp_path / "target.sqlite3"
    legacy = str(tmp_path / legacy_name) if legacy_name else ""
    assert adopt_legacy_task_store(str(target), legacy) in {"not_requested", "legacy_absent"}
    assert not target.exists()


def test_memory_target_and_same_store_are_not_copied(tmp_path):
    legacy = tmp_path / "same.sqlite3"
    _legacy_store_with_task(legacy)
    assert adopt_legacy_task_store(":memory:", str(legacy)) == "not_requested"
    assert adopt_legacy_task_store(str(legacy), str(legacy)) in {"target_exists", "same_store"}


def test_corrupt_legacy_fails_closed_without_creating_target(tmp_path):
    legacy = tmp_path / "corrupt.sqlite3"
    legacy.write_bytes(b"not a sqlite database" * 64)
    target = tmp_path / "out" / "tasks.sqlite3"
    with pytest.raises(LegacyTaskStoreAdoptionError) as caught:
        adopt_legacy_task_store(str(target), str(legacy))
    assert str(caught.value).startswith("legacy_task_store_")
    assert str(tmp_path) not in str(caught.value)
    assert not target.exists()
    assert not list(target.parent.glob("*.adopting-*"))


def test_host_store_factory_adopts_only_launcher_named_legacy(tmp_path, monkeypatch):
    from reverse_agent.platform_v1.trusted_host import _make_task_store

    _isolate(monkeypatch, tmp_path)
    legacy = tmp_path / "checkout" / ".platform_v1_runtime" / "tasks.sqlite3"
    task_id = _legacy_store_with_task(legacy)

    unnamed = _make_task_store(None)
    try:
        with pytest.raises(TaskStoreError, match="task_not_found"):
            unnamed.get_task(task_id)
        unnamed_path = unnamed.db_path
    finally:
        unnamed._conn.close()
    os.remove(unnamed_path)

    monkeypatch.setenv("REVERSE_AGENT_LEGACY_TASK_DB_PATH", str(legacy))
    adopted = _make_task_store(None)
    try:
        assert adopted.get_task(task_id).title == "legacy history"
        created = adopted.create_task(title="new host-owned task", executor_kind="deterministic_fixture")
    finally:
        adopted._conn.close()

    again = _make_task_store(None)
    try:
        assert again.get_task(created.id).title == "new host-owned task"
    finally:
        again._conn.close()


def test_explicit_store_overrides_skip_adoption(tmp_path, monkeypatch):
    from reverse_agent.platform_v1.trusted_host import _make_task_store

    _isolate(monkeypatch, tmp_path)
    legacy = tmp_path / "legacy.sqlite3"
    task_id = _legacy_store_with_task(legacy)
    monkeypatch.setenv("REVERSE_AGENT_LEGACY_TASK_DB_PATH", str(legacy))
    monkeypatch.setenv("REVERSE_AGENT_TASK_DB_DIR", str(tmp_path / "explicit"))
    store = _make_task_store(None)
    try:
        with pytest.raises(TaskStoreError, match="task_not_found"):
            store.get_task(task_id)
    finally:
        store._conn.close()


def test_host_store_factory_fails_closed_on_unreadable_legacy(tmp_path, monkeypatch):
    from reverse_agent.platform_v1.trusted_host import _make_task_store

    _isolate(monkeypatch, tmp_path)
    legacy = tmp_path / "corrupt.sqlite3"
    legacy.write_bytes(b"\x00" * 4096)
    monkeypatch.setenv("REVERSE_AGENT_LEGACY_TASK_DB_PATH", str(legacy))
    with pytest.raises(LegacyTaskStoreAdoptionError):
        _make_task_store(None)
    from reverse_agent.platform_v1.task_service import _default_task_db_path
    assert not Path(_default_task_db_path()).exists()


def test_launcher_names_its_checkout_store_as_adoption_source():
    assert '"REVERSE_AGENT_LEGACY_TASK_DB_PATH" = (Join-Path $runtimeDir "tasks.sqlite3")' in _DEV_UP


def test_empty_existing_target_is_set_aside_and_legacy_adopted(tmp_path):
    legacy = tmp_path / "checkout" / ".platform_v1_runtime" / "tasks.sqlite3"
    task_id = _legacy_store_with_task(legacy)
    target = tmp_path / "user-data" / "tasks.sqlite3"
    target.parent.mkdir(parents=True)
    TaskStore(db_path=str(target))._conn.close()  # schema only, no history

    assert adopt_legacy_task_store(str(target), str(legacy)) == "adopted"
    store = TaskStore(db_path=str(target))
    try:
        assert store.get_task(task_id).title == "legacy history"
    finally:
        store._conn.close()
    assert len(list(target.parent.glob("tasks.sqlite3.empty-*.bak"))) == 1


def test_model_setup_state_is_carried_once_and_never_overwritten(tmp_path):
    legacy = tmp_path / "checkout" / ".platform_v1_runtime" / "tasks.sqlite3"
    _legacy_store_with_task(legacy)
    (legacy.parent / "model_setup_state.json").write_bytes(b'{"schema_version": 1, "connections": []}')
    target = tmp_path / "user-data" / "tasks.sqlite3"

    assert adopt_legacy_task_store(str(target), str(legacy)) == "adopted"
    carried = target.parent / "model_setup_state.json"
    assert carried.read_bytes() == b'{"schema_version": 1, "connections": []}'

    carried.write_bytes(b'{"schema_version": 1, "connections": ["edited"]}')
    assert adopt_legacy_task_store(str(target), str(legacy)) == "target_exists"
    assert carried.read_bytes() == b'{"schema_version": 1, "connections": ["edited"]}'
    assert not list(target.parent.glob("*.adopting-*"))


def test_empty_legacy_is_not_adopted_and_does_not_churn_backups(tmp_path):
    legacy = tmp_path / "checkout" / "tasks.sqlite3"
    legacy.parent.mkdir(parents=True)
    TaskStore(db_path=str(legacy))._conn.close()  # schema only, no history
    target = tmp_path / "user-data" / "tasks.sqlite3"
    target.parent.mkdir(parents=True)
    TaskStore(db_path=str(target))._conn.close()
    for _ in range(3):
        assert adopt_legacy_task_store(str(target), str(legacy)) == "legacy_empty"
    assert not list(target.parent.glob("*.bak*"))


def test_model_setup_is_not_restored_after_owner_reset(tmp_path):
    legacy = tmp_path / "checkout" / "tasks.sqlite3"
    _legacy_store_with_task(legacy)
    (legacy.parent / "model_setup_state.json").write_bytes(b"{}")
    target = tmp_path / "user-data" / "tasks.sqlite3"
    assert adopt_legacy_task_store(str(target), str(legacy)) == "adopted"
    (target.parent / "model_setup_state.json").unlink()  # owner resets Model Control
    assert adopt_legacy_task_store(str(target), str(legacy)) == "target_exists"
    assert not (target.parent / "model_setup_state.json").exists()
