"""Consistent local backup and verification for the Platform V1 TaskStore.

SQLite owns the database-copy mechanics.  This module owns only Nerelan's
accepted backup artifact boundary: manifest shape, integrity/schema identity,
local path safety, and read-only verification.  It deliberately does not
restore or replace live state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Any, Mapping

from .run_store import TaskStore, TaskStoreError


BACKUP_FORMAT = "NERELAN_TASKSTORE_BACKUP_V1"
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
        "raw_external_credentials_included",
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
    raw_external_credentials_included: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _DatabaseInspection:
    schema_sha256: str
    sqlite_user_version: int
    page_size: int
    page_count: int


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


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
        b"nerelan.taskstore-backup.v1\0"
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
        if str(row[1]) == "main":
            raw = str(row[2] or "")
            if not raw:
                return None
            try:
                return Path(raw).resolve(strict=True)
            except OSError:
                return Path(raw).resolve(strict=False)
    return None


def _validate_target(store: TaskStore, target: str | os.PathLike[str]) -> tuple[Path, Path]:
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


def _exclusive_install(temp_path: Path, final_path: Path) -> None:
    fd: int | None = None
    try:
        fd = os.open(final_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise TaskStoreError("state_backup_destination_raced") from exc
    finally:
        if fd is not None:
            os.close(fd)
    try:
        os.replace(temp_path, final_path)
        try:
            os.chmod(final_path, 0o600)
        except OSError:
            # Permission hardening is best-effort on platforms without POSIX mode bits.
            pass
    except BaseException:
        try:
            final_path.unlink(missing_ok=True)
        finally:
            raise


def _write_manifest_temp(parent: Path, manifest: StateBackupManifest) -> Path:
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
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return path
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _read_manifest(path: Path) -> StateBackupManifest:
    try:
        size = path.stat().st_size
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
        raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=closed_object)
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
    )
    if any(not isinstance(raw[field], str) for field in string_fields):
        raise TaskStoreError("state_backup_manifest_types_invalid")
    if type(raw["sqlite_user_version"]) is not int or type(raw["page_size"]) is not int or type(raw["page_count"]) is not int:
        raise TaskStoreError("state_backup_manifest_types_invalid")
    if type(raw["raw_external_credentials_included"]) is not bool:
        raise TaskStoreError("state_backup_manifest_types_invalid")

    if raw["format"] != BACKUP_FORMAT or raw["integrity"] != INTEGRITY_OK:
        raise TaskStoreError("state_backup_manifest_contract_invalid")
    if raw["raw_external_credentials_included"] is not False:
        raise TaskStoreError("state_backup_manifest_credentials_invalid")
    if not _is_sha256(raw["backup_id"]) or not _is_sha256(raw["database_sha256"]) or not _is_sha256(raw["schema_sha256"]):
        raise TaskStoreError("state_backup_manifest_digest_invalid")
    if raw["sqlite_user_version"] < 0 or raw["page_size"] <= 0 or raw["page_count"] <= 0:
        raise TaskStoreError("state_backup_manifest_page_metadata_invalid")

    created = raw["created_at_utc"]
    if not created.endswith("Z"):
        raise TaskStoreError("state_backup_manifest_created_at_invalid")
    try:
        datetime.fromisoformat(created[:-1] + "+00:00")
    except ValueError as exc:
        raise TaskStoreError("state_backup_manifest_created_at_invalid") from exc

    return StateBackupManifest(**raw)


def _open_read_only(path: Path) -> sqlite3.Connection:
    # ``Path.as_uri`` percent-encodes unsafe URI characters and works on both
    # POSIX and Windows for absolute paths.
    uri = path.resolve(strict=True).as_uri() + "?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


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

    def create_backup(self, target_sqlite_path: str | os.PathLike[str]) -> StateBackupManifest:
        database_path, manifest_path = _validate_target(self.store, target_sqlite_path)
        temp_database: Path | None = None
        temp_manifest: Path | None = None
        database_installed = False
        manifest_installed = False

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
                try:
                    os.chmod(temp_database, 0o600)
                except OSError:
                    pass
                destination = sqlite3.connect(str(temp_database), isolation_level=None)
                try:
                    self._conn.backup(destination)
                finally:
                    destination.close()

                if self._conn.total_changes != source_changes:
                    raise TaskStoreError("state_backup_source_mutated")

                inspected_conn = _open_read_only(temp_database)
                try:
                    inspection = _inspect_database(inspected_conn)
                finally:
                    inspected_conn.close()
                database_sha256 = _sha256_file(temp_database)
                manifest = StateBackupManifest(
                    format=BACKUP_FORMAT,
                    backup_id=_backup_id(database_sha256, inspection.schema_sha256),
                    database_filename=database_path.name,
                    database_sha256=database_sha256,
                    schema_sha256=inspection.schema_sha256,
                    sqlite_user_version=inspection.sqlite_user_version,
                    page_size=inspection.page_size,
                    page_count=inspection.page_count,
                    created_at_utc=_utc_now(),
                    integrity=INTEGRITY_OK,
                    raw_external_credentials_included=False,
                )
                temp_manifest = _write_manifest_temp(database_path.parent, manifest)

                _exclusive_install(temp_database, database_path)
                database_installed = True
                temp_database = None
                _exclusive_install(temp_manifest, manifest_path)
                manifest_installed = True
                temp_manifest = None
                return self.verify_backup(
                    database_path,
                    expected_schema_sha256=inspection.schema_sha256,
                )
            except BaseException:
                if manifest_installed:
                    manifest_path.unlink(missing_ok=True)
                if database_installed:
                    database_path.unlink(missing_ok=True)
                raise
            finally:
                if temp_manifest is not None:
                    temp_manifest.unlink(missing_ok=True)
                if temp_database is not None:
                    temp_database.unlink(missing_ok=True)

    def verify_backup(
        self,
        target_sqlite_path: str | os.PathLike[str],
        *,
        expected_schema_sha256: str | None = None,
    ) -> StateBackupManifest:
        with self._lock:
            return self._verify_backup_locked(
                target_sqlite_path,
                expected_schema_sha256=expected_schema_sha256,
            )

    def _verify_backup_locked(
        self,
        target_sqlite_path: str | os.PathLike[str],
        *,
        expected_schema_sha256: str | None = None,
    ) -> StateBackupManifest:
        database_path = Path(target_sqlite_path)
        if database_path.is_symlink():
            raise TaskStoreError("state_backup_symlink_database_forbidden")
        try:
            database_path = database_path.resolve(strict=True)
        except OSError as exc:
            raise TaskStoreError("state_backup_database_missing") from exc
        if not database_path.is_file() or database_path.suffix != ".sqlite3":
            raise TaskStoreError("state_backup_database_invalid")

        manifest_path = _manifest_path(database_path)
        if manifest_path.is_symlink():
            raise TaskStoreError("state_backup_symlink_manifest_forbidden")
        if not manifest_path.is_file():
            raise TaskStoreError("state_backup_manifest_missing")

        source_changes = self._conn.total_changes
        manifest = _read_manifest(manifest_path)
        if manifest.database_filename != database_path.name:
            raise TaskStoreError("state_backup_manifest_filename_mismatch")
        if _sha256_file(database_path) != manifest.database_sha256:
            raise TaskStoreError("state_backup_database_digest_mismatch")

        conn = _open_read_only(database_path)
        try:
            inspection = _inspect_database(conn)
        finally:
            conn.close()
        if inspection.schema_sha256 != manifest.schema_sha256:
            raise TaskStoreError("state_backup_schema_digest_mismatch")
        if inspection.sqlite_user_version != manifest.sqlite_user_version:
            raise TaskStoreError("state_backup_user_version_mismatch")
        if inspection.page_size != manifest.page_size or inspection.page_count != manifest.page_count:
            raise TaskStoreError("state_backup_page_metadata_mismatch")
        expected_id = _backup_id(manifest.database_sha256, manifest.schema_sha256)
        if manifest.backup_id != expected_id:
            raise TaskStoreError("state_backup_id_mismatch")
        if expected_schema_sha256 is not None:
            if not _is_sha256(expected_schema_sha256):
                raise TaskStoreError("state_backup_expected_schema_invalid")
            if inspection.schema_sha256 != expected_schema_sha256:
                raise TaskStoreError("state_backup_schema_incompatible")
        if self._conn.total_changes != source_changes:
            raise TaskStoreError("state_backup_source_mutated")
        return manifest