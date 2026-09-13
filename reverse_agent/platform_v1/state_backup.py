"""Tamper-bound local backup and verification for the Platform V1 TaskStore.

SQLite owns consistent database-copy mechanics. This module owns Nerelan's
accepted local backup artifact boundary: closed manifest semantics, atomic
no-replace installation, externally bound backup identity, stable-inode
verification, owner-only local permissions, and read-only compatibility checks.

The backup is a FULL TaskStore SQLite snapshot and can therefore contain any
content already stored in TaskStore rows, including logs. It does not discover
or copy any external credential vault, configuration, environment, repository
worktree, provider cache, or adjacent file.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import tempfile
from typing import Any, Mapping

from .run_store import TaskStore, TaskStoreError


BACKUP_FORMAT = "NERELAN_TASKSTORE_BACKUP_V2"
CONTENT_SCOPE = "FULL_TASKSTORE_SQLITE"
MANIFEST_SUFFIX = ".manifest.json"
MAX_MANIFEST_BYTES = 64 * 1024
INTEGRITY_OK = "ok"

_MANIFEST_FIELDS = frozenset(
    {
        "format",
        "backup_id",
        "database_filename",
        "database_sha256",
        "schema_sha256",
        "sqlite_user_version",
        "page_size",
        "page_count",
        "created_at_utc",
        "integrity",
        "content_scope",
        "external_credential_vault_included",
    }
)


@dataclass(frozen=True)
class StateBackupManifest:
    format: str
    backup_id: str
    database_filename: str
    database_sha256: str
    schema_sha256: str
    sqlite_user_version: int
    page_size: int
    page_count: int
    created_at_utc: str
    integrity: str
    content_scope: str
    external_credential_vault_included: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _DatabaseInspection:
    schema_sha256: str
    sqlite_user_version: int
    page_size: int
    page_count: int


@dataclass(frozen=True)
class _FileIdentity:
    device: int
    inode: int


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _schema_sha256(conn: sqlite3.Connection) -> tuple[str, int]:
    user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    rows = conn.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_master
        WHERE name NOT LIKE 'sqlite_%'
        ORDER BY type ASC, name ASC, tbl_name ASC, sql ASC
        """
    ).fetchall()
    objects = [
        [
            "" if row[0] is None else str(row[0]),
            "" if row[1] is None else str(row[1]),
            "" if row[2] is None else str(row[2]),
            "" if row[3] is None else str(row[3]),
        ]
        for row in rows
    ]
    payload = {"user_version": user_version, "objects": objects}
    return hashlib.sha256(_canonical_json(payload)).hexdigest(), user_version


def _inspect_database(conn: sqlite3.Connection) -> _DatabaseInspection:
    integrity_rows = conn.execute("PRAGMA integrity_check").fetchall()
    if len(integrity_rows) != 1 or str(integrity_rows[0][0]) != INTEGRITY_OK:
        raise TaskStoreError("state_backup_integrity_check_failed")
    schema_sha256, user_version = _schema_sha256(conn)
    page_size = int(conn.execute("PRAGMA page_size").fetchone()[0])
    page_count = int(conn.execute("PRAGMA page_count").fetchone()[0])
    if page_size <= 0 or page_count <= 0:
        raise TaskStoreError("state_backup_page_metadata_invalid")
    return _DatabaseInspection(
        schema_sha256=schema_sha256,
        sqlite_user_version=user_version,
        page_size=page_size,
        page_count=page_count,
    )


def _backup_id(database_sha256: str, schema_sha256: str) -> str:
    material = (
        b"nerelan.taskstore-backup.v2\0"
        + CONTENT_SCOPE.encode("ascii")
        + b"\0"
        + database_sha256.encode("ascii")
        + b"\0"
        + schema_sha256.encode("ascii")
    )
    return hashlib.sha256(material).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _manifest_path(database_path: Path) -> Path:
    return Path(str(database_path) + MANIFEST_SUFFIX)


def _path_is_same(left: Path, right: Path) -> bool:
    try:
        return left.resolve(strict=True) == right.resolve(strict=False)
    except OSError:
        return False


def _source_database_path(store: TaskStore) -> Path | None:
    with store._lock:
        rows = store._conn.execute("PRAGMA database_list").fetchall()
    for row in rows:
        if str(row[1]) != "main":
            continue
        raw = str(row[2] or "")
        if not raw:
            return None
        try:
            return Path(raw).resolve(strict=True)
        except OSError:
            return Path(raw).resolve(strict=False)
    return None


def _validate_target(
    store: TaskStore,
    target: str | os.PathLike[str],
) -> tuple[Path, Path]:
    raw = Path(target)
    if raw.suffix != ".sqlite3":
        raise TaskStoreError("state_backup_target_must_be_sqlite3")
    if raw.name in {"", ".", ".."}:
        raise TaskStoreError("state_backup_target_invalid")

    parent = raw.parent if str(raw.parent) else Path(".")
    try:
        resolved_parent = parent.resolve(strict=True)
    except OSError as exc:
        raise TaskStoreError("state_backup_parent_missing") from exc
    if not resolved_parent.is_dir():
        raise TaskStoreError("state_backup_parent_not_directory")

    database_path = resolved_parent / raw.name
    manifest_path = _manifest_path(database_path)

    source_path = _source_database_path(store)
    if source_path is not None and _path_is_same(source_path, database_path):
        raise TaskStoreError("state_backup_target_is_source_database")

    for path, error in (
        (database_path, "state_backup_target_exists"),
        (manifest_path, "state_backup_manifest_exists"),
    ):
        if path.is_symlink():
            raise TaskStoreError("state_backup_symlink_target_forbidden")
        if path.exists():
            raise TaskStoreError(error)

    return database_path, manifest_path


def _regular_identity(path: Path, *, error_code: str) -> _FileIdentity:
    try:
        info = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise TaskStoreError(error_code) from exc
    if not stat.S_ISREG(info.st_mode):
        raise TaskStoreError(error_code)
    inode = int(info.st_ino)
    if inode <= 0:
        # Identity-safe cleanup/verification is impossible without a stable
        # filesystem object identity. Fail closed rather than approximate.
        raise TaskStoreError("state_backup_file_identity_unavailable")
    return _FileIdentity(device=int(info.st_dev), inode=inode)


def _same_identity(path: Path, identity: _FileIdentity) -> bool:
    try:
        info = path.stat(follow_symlinks=False)
    except OSError:
        return False
    return (
        stat.S_ISREG(info.st_mode)
        and int(info.st_dev) == identity.device
        and int(info.st_ino) == identity.inode
    )


def _unlink_if_identity(
    path: Path,
    identity: _FileIdentity | None,
    *,
    operation_private: bool = False,
) -> None:
    """Clean only operation-private names; published destinations are fail-safe no-op.

    A `(st_dev, st_ino)` tuple identifies the currently observed object but is not
    a durable generation token after unlink/recreate.  Consequently a stale
    identity must never authorize deletion of a published destination.  Private,
    operation-owned temporary names may still use the identity check for bounded
    cleanup.
    """
    if not operation_private:
        return
    if identity is None or not _same_identity(path, identity):
        return
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _harden_owner_only(path: Path) -> None:
    if os.name != "posix":
        return
    try:
        os.chmod(path, 0o600, follow_symlinks=False)
    except (OSError, NotImplementedError) as exc:
        raise TaskStoreError("state_backup_permission_hardening_failed") from exc


def _require_owner_only(path: Path, *, kind: str) -> None:
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise TaskStoreError(f"state_backup_{kind}_invalid")
    if os.name != "posix":
        return
    getuid = getattr(os, "geteuid", None)
    if callable(getuid) and int(info.st_uid) != int(getuid()):
        raise TaskStoreError(f"state_backup_{kind}_owner_invalid")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise TaskStoreError(f"state_backup_{kind}_permissions_invalid")


def _atomic_link_install(temp_path: Path, final_path: Path) -> _FileIdentity:
    """Install a completed same-filesystem temp inode without replacement.

    Once the hard-link publication succeeds, `final_path` is externally visible.
    A later failure therefore never unlinks that published pathname; callers may
    clean only the still-private temp name.
    """
    _harden_owner_only(temp_path)
    source_identity = _regular_identity(
        temp_path, error_code="state_backup_temp_artifact_invalid"
    )
    try:
        os.link(temp_path, final_path)
    except FileExistsError as exc:
        raise TaskStoreError("state_backup_destination_raced") from exc
    except OSError as exc:
        raise TaskStoreError("state_backup_atomic_link_install_failed") from exc

    if not _same_identity(final_path, source_identity):
        raise TaskStoreError("state_backup_install_identity_mismatch")
    _require_owner_only(final_path, kind="installed_artifact")
    temp_path.unlink()
    return source_identity


def _new_unoccupied_path(parent: Path, *, prefix: str, suffix: str) -> Path:
    fd, name = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=parent)
    os.close(fd)
    path = Path(name)
    path.unlink()
    return path


def _stable_hardlink(path: Path, *, prefix: str) -> tuple[Path, _FileIdentity]:
    """Create a temporary no-follow hard link to the currently named inode."""
    stable_path = _new_unoccupied_path(
        path.parent,
        prefix=prefix,
        suffix=".stable",
    )
    try:
        try:
            os.link(path, stable_path, follow_symlinks=False)
        except TypeError as exc:
            raise TaskStoreError("state_backup_stable_link_unsupported") from exc
        except NotImplementedError as exc:
            raise TaskStoreError("state_backup_stable_link_unsupported") from exc
        except FileExistsError as exc:
            raise TaskStoreError("state_backup_stable_link_raced") from exc
        except OSError as exc:
            raise TaskStoreError("state_backup_stable_link_failed") from exc

        if stable_path.is_symlink():
            raise TaskStoreError("state_backup_symlink_database_forbidden")
        identity = _regular_identity(
            stable_path,
            error_code="state_backup_stable_link_invalid",
        )
        return stable_path, identity
    except BaseException:
        try:
            stable_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _open_read_only(path: Path) -> sqlite3.Connection:
    uri = path.resolve(strict=True).as_uri() + "?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def _inspect_database_path(path: Path) -> _DatabaseInspection:
    conn: sqlite3.Connection | None = None
    try:
        conn = _open_read_only(path)
        return _inspect_database(conn)
    except TaskStoreError:
        raise
    except sqlite3.DatabaseError as exc:
        raise TaskStoreError("state_backup_database_sqlite_invalid") from exc
    finally:
        if conn is not None:
            conn.close()


def _inspect_bound_database(
    database_path: Path,
) -> tuple[str, _DatabaseInspection]:
    """Hash and inspect one stable inode and prove it still occupies target."""
    stable_path, identity = _stable_hardlink(
        database_path,
        prefix=".nerelan-state-backup-verify-db-",
    )
    try:
        _require_owner_only(stable_path, kind="database")
        digest_before = _sha256_file(stable_path)
        if not _same_identity(stable_path, identity):
            raise TaskStoreError("state_backup_database_changed_during_verify")

        inspection = _inspect_database_path(stable_path)

        digest_after = _sha256_file(stable_path)
        if digest_after != digest_before or not _same_identity(stable_path, identity):
            raise TaskStoreError("state_backup_database_changed_during_verify")

        try:
            if not os.path.samefile(database_path, stable_path):
                raise TaskStoreError("state_backup_database_path_replaced")
        except (FileNotFoundError, OSError) as exc:
            raise TaskStoreError("state_backup_database_path_replaced") from exc

        if database_path.is_symlink():
            raise TaskStoreError("state_backup_symlink_database_forbidden")
        _require_owner_only(database_path, kind="database")
        return digest_before, inspection
    finally:
        _unlink_if_identity(stable_path, identity, operation_private=True)


def _write_manifest_temp(
    parent: Path,
    manifest: StateBackupManifest,
) -> Path:
    payload = _canonical_json(manifest.to_dict()) + b"\n"
    if len(payload) > MAX_MANIFEST_BYTES:
        raise TaskStoreError("state_backup_manifest_too_large")
    fd, name = tempfile.mkstemp(
        prefix=".nerelan-state-backup-manifest-",
        suffix=".partial",
        dir=parent,
    )
    path = Path(name)
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _harden_owner_only(path)
        return path
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _read_manifest(path: Path) -> StateBackupManifest:
    try:
        size = path.stat(follow_symlinks=False).st_size
    except OSError as exc:
        raise TaskStoreError("state_backup_manifest_missing") from exc
    if size <= 0 or size > MAX_MANIFEST_BYTES:
        raise TaskStoreError("state_backup_manifest_size_invalid")

    def closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise TaskStoreError("state_backup_manifest_duplicate_field")
            result[key] = value
        return result

    try:
        raw = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=closed_object,
        )
    except TaskStoreError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TaskStoreError("state_backup_manifest_invalid") from exc

    if not isinstance(raw, dict) or set(raw) != _MANIFEST_FIELDS:
        raise TaskStoreError("state_backup_manifest_fields_invalid")

    string_fields = (
        "format",
        "backup_id",
        "database_filename",
        "database_sha256",
        "schema_sha256",
        "created_at_utc",
        "integrity",
        "content_scope",
    )
    if any(not isinstance(raw[field], str) for field in string_fields):
        raise TaskStoreError("state_backup_manifest_types_invalid")
    if (
        type(raw["sqlite_user_version"]) is not int
        or type(raw["page_size"]) is not int
        or type(raw["page_count"]) is not int
        or type(raw["external_credential_vault_included"]) is not bool
    ):
        raise TaskStoreError("state_backup_manifest_types_invalid")

    if (
        raw["format"] != BACKUP_FORMAT
        or raw["integrity"] != INTEGRITY_OK
        or raw["content_scope"] != CONTENT_SCOPE
        or raw["external_credential_vault_included"] is not False
    ):
        raise TaskStoreError("state_backup_manifest_contract_invalid")
    if (
        not _is_sha256(raw["backup_id"])
        or not _is_sha256(raw["database_sha256"])
        or not _is_sha256(raw["schema_sha256"])
    ):
        raise TaskStoreError("state_backup_manifest_digest_invalid")
    if (
        raw["sqlite_user_version"] < 0
        or raw["page_size"] <= 0
        or raw["page_count"] <= 0
    ):
        raise TaskStoreError("state_backup_manifest_page_metadata_invalid")

    created = raw["created_at_utc"]
    if not created.endswith("Z"):
        raise TaskStoreError("state_backup_manifest_created_at_invalid")
    try:
        parsed = datetime.fromisoformat(created[:-1] + "+00:00")
    except ValueError as exc:
        raise TaskStoreError("state_backup_manifest_created_at_invalid") from exc
    if parsed.tzinfo is None:
        raise TaskStoreError("state_backup_manifest_created_at_invalid")

    return StateBackupManifest(**raw)


def _read_bound_manifest(
    manifest_path: Path,
) -> tuple[StateBackupManifest, _FileIdentity, Path]:
    if manifest_path.is_symlink():
        raise TaskStoreError("state_backup_symlink_manifest_forbidden")
    stable_path, identity = _stable_hardlink(
        manifest_path,
        prefix=".nerelan-state-backup-verify-manifest-",
    )
    try:
        _require_owner_only(stable_path, kind="manifest")
        manifest = _read_manifest(stable_path)
        try:
            if not os.path.samefile(manifest_path, stable_path):
                raise TaskStoreError("state_backup_manifest_path_replaced")
        except (FileNotFoundError, OSError) as exc:
            raise TaskStoreError("state_backup_manifest_path_replaced") from exc
        _require_owner_only(manifest_path, kind="manifest")
        return manifest, identity, stable_path
    except BaseException:
        _unlink_if_identity(stable_path, identity, operation_private=True)
        raise


class StateBackupService:
    """Create and verify local TaskStore backups without restore authority."""

    def __init__(self, store: TaskStore) -> None:
        self.store = store
        self._conn = store._conn
        self._lock = store._lock

    def current_schema_sha256(self) -> str:
        with self._lock:
            schema_sha256, _ = _schema_sha256(self._conn)
            return schema_sha256

    def create_backup(
        self,
        target_sqlite_path: str | os.PathLike[str],
    ) -> StateBackupManifest:
        database_path, manifest_path = _validate_target(
            self.store,
            target_sqlite_path,
        )
        temp_database: Path | None = None
        temp_manifest: Path | None = None

        with self._lock:
            if self._conn.in_transaction:
                raise TaskStoreError("state_backup_source_transaction_active")
            source_changes = self._conn.total_changes
            fd, temp_name = tempfile.mkstemp(
                prefix=".nerelan-state-backup-",
                suffix=".sqlite3.partial",
                dir=database_path.parent,
            )
            os.close(fd)
            temp_database = Path(temp_name)
            try:
                _harden_owner_only(temp_database)
                destination = sqlite3.connect(
                    str(temp_database),
                    isolation_level=None,
                )
                try:
                    self._conn.backup(destination)
                finally:
                    destination.close()

                if self._conn.total_changes != source_changes:
                    raise TaskStoreError("state_backup_source_mutated")

                _require_owner_only(temp_database, kind="database")
                inspection = _inspect_database_path(temp_database)
                database_sha256 = _sha256_file(temp_database)
                if _sha256_file(temp_database) != database_sha256:
                    raise TaskStoreError("state_backup_database_changed_during_create")

                manifest = StateBackupManifest(
                    format=BACKUP_FORMAT,
                    backup_id=_backup_id(
                        database_sha256,
                        inspection.schema_sha256,
                    ),
                    database_filename=database_path.name,
                    database_sha256=database_sha256,
                    schema_sha256=inspection.schema_sha256,
                    sqlite_user_version=inspection.sqlite_user_version,
                    page_size=inspection.page_size,
                    page_count=inspection.page_count,
                    created_at_utc=_utc_now(),
                    integrity=INTEGRITY_OK,
                    content_scope=CONTENT_SCOPE,
                    external_credential_vault_included=False,
                )
                temp_manifest = _write_manifest_temp(
                    database_path.parent,
                    manifest,
                )

                _atomic_link_install(
                    temp_database,
                    database_path,
                )
                temp_database = None
                _atomic_link_install(
                    temp_manifest,
                    manifest_path,
                )
                temp_manifest = None

                return self._verify_backup_locked(
                    database_path,
                    expected_backup_id=manifest.backup_id,
                    expected_schema_sha256=inspection.schema_sha256,
                )
            finally:
                # Final destination names become externally visible when the
                # hard-link publication succeeds. Never unlink those names on
                # a later failure: a delete/recreate race can reuse `(dev, ino)`
                # and make stale identity-based rollback delete a replacement.
                # Only still-private temp names are operation-owned cleanup.
                if temp_manifest is not None:
                    temp_manifest.unlink(missing_ok=True)
                if temp_database is not None:
                    temp_database.unlink(missing_ok=True)

    def verify_backup(
        self,
        target_sqlite_path: str | os.PathLike[str],
        *,
        expected_backup_id: str | None,
        expected_schema_sha256: str | None = None,
    ) -> StateBackupManifest:
        with self._lock:
            return self._verify_backup_locked(
                target_sqlite_path,
                expected_backup_id=expected_backup_id,
                expected_schema_sha256=expected_schema_sha256,
            )

    def _verify_backup_locked(
        self,
        target_sqlite_path: str | os.PathLike[str],
        *,
        expected_backup_id: str | None,
        expected_schema_sha256: str | None = None,
    ) -> StateBackupManifest:
        if expected_backup_id is None:
            raise TaskStoreError("state_backup_expected_identity_required")
        if not _is_sha256(expected_backup_id):
            raise TaskStoreError("state_backup_expected_identity_invalid")

        raw_database_path = Path(target_sqlite_path)
        if raw_database_path.suffix != ".sqlite3":
            raise TaskStoreError("state_backup_database_invalid")
        parent = raw_database_path.parent if str(raw_database_path.parent) else Path(".")
        try:
            resolved_parent = parent.resolve(strict=True)
        except OSError as exc:
            raise TaskStoreError("state_backup_database_missing") from exc
        database_path = resolved_parent / raw_database_path.name
        if database_path.is_symlink():
            raise TaskStoreError("state_backup_symlink_database_forbidden")
        _regular_identity(
            database_path,
            error_code="state_backup_database_invalid",
        )

        manifest_path = _manifest_path(database_path)
        if manifest_path.is_symlink():
            raise TaskStoreError("state_backup_symlink_manifest_forbidden")
        if not manifest_path.is_file():
            raise TaskStoreError("state_backup_manifest_missing")

        source_changes = self._conn.total_changes
        manifest: StateBackupManifest | None = None
        manifest_identity: _FileIdentity | None = None
        stable_manifest: Path | None = None
        try:
            manifest, manifest_identity, stable_manifest = _read_bound_manifest(
                manifest_path
            )
            if manifest.backup_id != expected_backup_id:
                raise TaskStoreError("state_backup_expected_identity_mismatch")
            if manifest.database_filename != database_path.name:
                raise TaskStoreError("state_backup_manifest_filename_mismatch")

            database_sha256, inspection = _inspect_bound_database(database_path)
            if database_sha256 != manifest.database_sha256:
                raise TaskStoreError("state_backup_database_digest_mismatch")
            if inspection.schema_sha256 != manifest.schema_sha256:
                raise TaskStoreError("state_backup_schema_digest_mismatch")
            if inspection.sqlite_user_version != manifest.sqlite_user_version:
                raise TaskStoreError("state_backup_user_version_mismatch")
            if (
                inspection.page_size != manifest.page_size
                or inspection.page_count != manifest.page_count
            ):
                raise TaskStoreError("state_backup_page_metadata_mismatch")

            expected_id = _backup_id(
                manifest.database_sha256,
                manifest.schema_sha256,
            )
            if manifest.backup_id != expected_id:
                raise TaskStoreError("state_backup_id_mismatch")

            if expected_schema_sha256 is not None:
                if not _is_sha256(expected_schema_sha256):
                    raise TaskStoreError("state_backup_expected_schema_invalid")
                if inspection.schema_sha256 != expected_schema_sha256:
                    raise TaskStoreError("state_backup_schema_incompatible")

            # Reconfirm sidecar path identity after database verification.
            if stable_manifest is None or manifest_identity is None:
                raise TaskStoreError("state_backup_manifest_identity_missing")
            try:
                if not os.path.samefile(manifest_path, stable_manifest):
                    raise TaskStoreError("state_backup_manifest_path_replaced")
            except (FileNotFoundError, OSError) as exc:
                raise TaskStoreError("state_backup_manifest_path_replaced") from exc

            if self._conn.total_changes != source_changes:
                raise TaskStoreError("state_backup_source_mutated")
            return manifest
        finally:
            if stable_manifest is not None:
                _unlink_if_identity(
                    stable_manifest,
                    manifest_identity,
                    operation_private=True,
                )
