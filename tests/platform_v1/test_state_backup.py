from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat

import pytest

import reverse_agent.platform_v1.state_backup as sb
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.state_backup import StateBackupService


def seeded_store(path=":memory:"):
    store = TaskStore(path)
    store.create_task(
        title="TOP-SECRET task title must stay inside the database",
        repository="owner/repo",
    )
    return store


def manifest_path(path: Path) -> Path:
    return Path(str(path) + ".manifest.json")


def rewrite_manifest(path: Path, payload: object) -> None:
    target = manifest_path(path)
    target.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    if os.name == "posix":
        os.chmod(target, 0o600)


def test_in_memory_backup_round_trip_and_real_rows(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    before = store._conn.total_changes
    target = tmp_path / "backup.sqlite3"

    manifest = service.create_backup(target)
    verified = service.verify_backup(
        target,
        expected_backup_id=manifest.backup_id,
        expected_schema_sha256=manifest.schema_sha256,
    )

    assert verified == manifest
    assert store._conn.total_changes == before
    assert manifest.format == sb.BACKUP_FORMAT
    assert manifest.content_scope == "FULL_TASKSTORE_SQLITE"
    assert manifest.external_credential_vault_included is False
    assert "raw_external_credentials_included" not in manifest.to_dict()

    conn = sqlite3.connect(target)
    try:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1
    finally:
        conn.close()


def test_file_backed_source_remains_unchanged(tmp_path):
    source = tmp_path / "source.sqlite3"
    store = seeded_store(source)
    service = StateBackupService(store)
    before_changes = store._conn.total_changes
    before_bytes = source.read_bytes()

    manifest = service.create_backup(tmp_path / "backup.sqlite3")

    assert store._conn.total_changes == before_changes
    assert source.read_bytes() == before_bytes
    assert service.verify_backup(
        tmp_path / "backup.sqlite3",
        expected_backup_id=manifest.backup_id,
    ) == manifest


def test_active_source_transaction_fails_closed_and_remains_active(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    store._conn.execute("BEGIN")
    store._conn.execute("UPDATE tasks SET title=title WHERE 1=0")
    try:
        with pytest.raises(TaskStoreError, match="state_backup_source_transaction_active"):
            service.create_backup(tmp_path / "backup.sqlite3")
        assert store._conn.in_transaction is True
        assert not (tmp_path / "backup.sqlite3").exists()
    finally:
        store._conn.execute("ROLLBACK")


def test_source_database_alias_fails_closed(tmp_path):
    source = tmp_path / "source.sqlite3"
    store = seeded_store(source)
    with pytest.raises(TaskStoreError, match="state_backup_target_is_source_database"):
        StateBackupService(store).create_backup(source)


@pytest.mark.parametrize("which", ["database", "manifest"])
def test_existing_destination_fails_closed(tmp_path, which):
    store = seeded_store()
    target = tmp_path / "backup.sqlite3"
    path = target if which == "database" else manifest_path(target)
    path.write_text("occupied", encoding="utf-8")
    expected = "state_backup_target_exists" if which == "database" else "state_backup_manifest_exists"
    with pytest.raises(TaskStoreError, match=expected):
        StateBackupService(store).create_backup(target)
    assert path.read_text(encoding="utf-8") == "occupied"


def test_symlink_destination_fails_closed(tmp_path):
    if not hasattr(os, "symlink"):
        pytest.skip("symlink unavailable")
    store = seeded_store()
    target = tmp_path / "backup.sqlite3"
    backing = tmp_path / "other.sqlite3"
    backing.write_bytes(b"x")
    try:
        target.symlink_to(backing)
    except OSError:
        pytest.skip("symlink not permitted")
    with pytest.raises(TaskStoreError, match="state_backup_symlink_target_forbidden"):
        StateBackupService(store).create_backup(target)


def test_atomic_no_replace_install_does_not_overwrite_raced_file(tmp_path, monkeypatch):
    temp = tmp_path / "temp"
    final = tmp_path / "final"
    temp.write_bytes(b"ours")
    real_link = sb.os.link

    def raced_link(src, dst, *args, **kwargs):
        if Path(src) == temp and Path(dst) == final:
            final.write_bytes(b"racer")
            raise FileExistsError(str(final))
        return real_link(src, dst, *args, **kwargs)

    monkeypatch.setattr(sb.os, "link", raced_link)
    with pytest.raises(TaskStoreError, match="state_backup_destination_raced"):
        sb._atomic_link_install(temp, final)
    assert final.read_bytes() == b"racer"
    assert temp.read_bytes() == b"ours"


def test_identity_safe_cleanup_never_unlinks_replacement(tmp_path):
    path = tmp_path / "artifact"
    path.write_bytes(b"ours")
    identity = sb._regular_identity(path, error_code="bad")
    path.unlink()
    path.write_bytes(b"replacement")
    sb._unlink_if_identity(path, identity)
    assert path.read_bytes() == b"replacement"


def test_private_identity_cleanup_remains_bounded(tmp_path):
    path = tmp_path / "private-temp"
    path.write_bytes(b"ours")
    identity = sb._regular_identity(path, error_code="bad")
    sb._unlink_if_identity(path, identity, operation_private=True)
    assert not path.exists()


def test_atomic_install_failure_after_publication_keeps_final_path(
    tmp_path, monkeypatch
):
    temp = tmp_path / "temp"
    final = tmp_path / "final"
    temp.write_bytes(b"ours")
    real_require = sb._require_owner_only

    def fail_installed(path, *, kind):
        if Path(path) == final and kind == "installed_artifact":
            raise TaskStoreError("injected_post_publication_failure")
        return real_require(path, kind=kind)

    monkeypatch.setattr(sb, "_require_owner_only", fail_installed)
    with pytest.raises(TaskStoreError, match="injected_post_publication_failure"):
        sb._atomic_link_install(temp, final)
    assert final.read_bytes() == b"ours"
    assert temp.read_bytes() == b"ours"


def test_stable_inode_verification_detects_target_path_replacement(
    tmp_path, monkeypatch
):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)

    replacement = tmp_path / "replacement.sqlite3"
    shutil.copy2(target, replacement)
    real_inspect = sb._inspect_database
    switched = False

    def replace_target_during_inspection(conn):
        nonlocal switched
        if not switched:
            switched = True
            target.unlink()
            os.link(replacement, target)
        return real_inspect(conn)

    monkeypatch.setattr(sb, "_inspect_database", replace_target_during_inspection)
    with pytest.raises(TaskStoreError, match="state_backup_database_path_replaced"):
        service.verify_backup(
            target,
            expected_backup_id=manifest.backup_id,
        )


def test_expected_backup_identity_is_required_and_validated(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)

    with pytest.raises(TaskStoreError, match="state_backup_expected_identity_required"):
        service.verify_backup(target, expected_backup_id=None)
    with pytest.raises(TaskStoreError, match="state_backup_expected_identity_invalid"):
        service.verify_backup(target, expected_backup_id="not-a-digest")
    assert service.verify_backup(
        target, expected_backup_id=manifest.backup_id
    ) == manifest


def test_coordinated_database_and_manifest_replacement_cannot_change_trusted_identity(
    tmp_path,
):
    store = seeded_store()
    service = StateBackupService(store)
    first_path = tmp_path / "first.sqlite3"
    first = service.create_backup(first_path)

    store.create_task(title="second state", repository="owner/repo")
    second_path = tmp_path / "second.sqlite3"
    second = service.create_backup(second_path)
    assert second.backup_id != first.backup_id

    shutil.copy2(second_path, first_path)
    shutil.copy2(manifest_path(second_path), manifest_path(first_path))
    if os.name == "posix":
        os.chmod(first_path, 0o600)
        os.chmod(manifest_path(first_path), 0o600)

    with pytest.raises(TaskStoreError, match="state_backup_expected_identity_mismatch"):
        service.verify_backup(
            first_path,
            expected_backup_id=first.backup_id,
        )


def test_database_tamper_fails_digest_check(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)

    data = bytearray(target.read_bytes())
    data[-1] ^= 0x01
    target.write_bytes(data)
    if os.name == "posix":
        os.chmod(target, 0o600)

    with pytest.raises(
        TaskStoreError,
        match="state_backup_database_(digest_mismatch|integrity_check_failed|sqlite_invalid)",
    ):
        service.verify_backup(
            target,
            expected_backup_id=manifest.backup_id,
        )


def test_truncated_database_fails_closed(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)
    target.write_bytes(target.read_bytes()[:128])
    if os.name == "posix":
        os.chmod(target, 0o600)

    with pytest.raises(TaskStoreError):
        service.verify_backup(
            target,
            expected_backup_id=manifest.backup_id,
        )


def test_manifest_unknown_field_fails_closed(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)
    payload = manifest.to_dict()
    payload["extra"] = "forbidden"
    rewrite_manifest(target, payload)

    with pytest.raises(TaskStoreError, match="state_backup_manifest_fields_invalid"):
        service.verify_backup(target, expected_backup_id=manifest.backup_id)


def test_manifest_duplicate_field_fails_closed(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)
    sidecar = manifest_path(target)
    original = sidecar.read_text(encoding="utf-8").strip()
    sidecar.write_text('{"format":"duplicate",' + original[1:] + "\n", encoding="utf-8")
    if os.name == "posix":
        os.chmod(sidecar, 0o600)

    with pytest.raises(TaskStoreError, match="state_backup_manifest_duplicate_field"):
        service.verify_backup(target, expected_backup_id=manifest.backup_id)


def test_malformed_and_oversized_manifest_fail_closed(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    first = tmp_path / "first.sqlite3"
    m1 = service.create_backup(first)
    sidecar = manifest_path(first)
    sidecar.write_text("{", encoding="utf-8")
    if os.name == "posix":
        os.chmod(sidecar, 0o600)
    with pytest.raises(TaskStoreError, match="state_backup_manifest_invalid"):
        service.verify_backup(first, expected_backup_id=m1.backup_id)

    second = tmp_path / "second.sqlite3"
    m2 = service.create_backup(second)
    sidecar2 = manifest_path(second)
    sidecar2.write_bytes(b"x" * (sb.MAX_MANIFEST_BYTES + 1))
    if os.name == "posix":
        os.chmod(sidecar2, 0o600)
    with pytest.raises(TaskStoreError, match="state_backup_manifest_size_invalid"):
        service.verify_backup(second, expected_backup_id=m2.backup_id)


def test_expected_schema_mismatch_fails_closed(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)

    with pytest.raises(TaskStoreError, match="state_backup_schema_incompatible"):
        service.verify_backup(
            target,
            expected_backup_id=manifest.backup_id,
            expected_schema_sha256="0" * 64,
        )


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode contract")
@pytest.mark.parametrize("which", ["database", "manifest"])
def test_verification_rejects_group_or_other_permissions(tmp_path, which):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)
    path = target if which == "database" else manifest_path(target)
    os.chmod(path, 0o644)

    pattern = (
        "state_backup_database_permissions_invalid"
        if which == "database"
        else "state_backup_manifest_permissions_invalid"
    )
    with pytest.raises(TaskStoreError, match=pattern):
        service.verify_backup(target, expected_backup_id=manifest.backup_id)


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode contract")
def test_created_artifacts_are_owner_only(tmp_path):
    store = seeded_store()
    target = tmp_path / "backup.sqlite3"
    manifest = StateBackupService(store).create_backup(target)
    assert stat.S_IMODE(target.stat().st_mode) & 0o077 == 0
    assert stat.S_IMODE(manifest_path(target).stat().st_mode) & 0o077 == 0
    assert manifest.external_credential_vault_included is False


def test_manifest_content_scope_is_explicit_and_contains_no_source_path(tmp_path):
    source = tmp_path / "source.sqlite3"
    store = seeded_store(source)
    target = tmp_path / "backup.sqlite3"
    manifest = StateBackupService(store).create_backup(target)
    payload = manifest.to_dict()
    rendered = json.dumps(payload, sort_keys=True)

    assert payload["content_scope"] == "FULL_TASKSTORE_SQLITE"
    assert payload["external_credential_vault_included"] is False
    assert "raw_external_credentials_included" not in payload
    assert str(source) not in rendered
    assert "TOP-SECRET task title" not in rendered


def test_missing_manifest_is_unaccepted(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)
    manifest_path(target).unlink()
    with pytest.raises(TaskStoreError, match="state_backup_manifest_missing"):
        service.verify_backup(target, expected_backup_id=manifest.backup_id)


def test_manifest_install_failure_leaves_published_database_unaccepted(
    tmp_path, monkeypatch
):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    real_install = sb._atomic_link_install
    calls = 0

    def fail_second_install(temp_path, final_path):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise TaskStoreError("injected_manifest_install_failure")
        return real_install(temp_path, final_path)

    monkeypatch.setattr(sb, "_atomic_link_install", fail_second_install)
    with pytest.raises(TaskStoreError, match="injected_manifest_install_failure"):
        service.create_backup(target)

    assert target.exists()
    assert not manifest_path(target).exists()
    with pytest.raises(TaskStoreError, match="state_backup_manifest_missing"):
        service.verify_backup(target, expected_backup_id="0" * 64)
    with pytest.raises(TaskStoreError, match="state_backup_target_exists"):
        service.create_backup(target)
    assert not list(tmp_path.glob(".nerelan-state-backup-*.partial"))
    assert not list(tmp_path.glob(".nerelan-state-backup-manifest-*.partial"))


def test_final_acceptance_failure_never_unlinks_published_pair(
    tmp_path, monkeypatch
):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"

    def fail_final_acceptance(
        target_sqlite_path,
        *,
        expected_backup_id,
        expected_schema_sha256=None,
    ):
        raise TaskStoreError("injected_final_acceptance_failure")

    monkeypatch.setattr(service, "_verify_backup_locked", fail_final_acceptance)
    with pytest.raises(TaskStoreError, match="injected_final_acceptance_failure"):
        service.create_backup(target)

    assert target.exists()
    assert manifest_path(target).exists()
    with pytest.raises(TaskStoreError, match="state_backup_target_exists"):
        service.create_backup(target)


def test_source_total_changes_unchanged_by_verification(tmp_path):
    store = seeded_store()
    service = StateBackupService(store)
    target = tmp_path / "backup.sqlite3"
    manifest = service.create_backup(target)
    before = store._conn.total_changes
    service.verify_backup(target, expected_backup_id=manifest.backup_id)
    assert store._conn.total_changes == before
