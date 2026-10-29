"""Owner-controlled Windows boot preferences and resume preflight policy.

This module intentionally does NOT install a Windows scheduled task, start a
host, extend autonomy, or execute a model/GPU job.  The stable desktop
installer and the fenced remote-job reconciler remain separate authority
boundaries. A persisted preference is never itself execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Mapping

SCHEMA_VERSION = 1
MAX_PREFERENCE_BYTES = 4096


class BootPreferenceError(ValueError):
    """Invalid or untrusted boot preference state."""


@dataclass(frozen=True)
class BootPreferences:
    start_on_login: bool = False
    resume_interrupted: bool = False
    open_ui_on_login: bool = False

    def __post_init__(self) -> None:
        if any(type(value) is not bool for value in (
            self.start_on_login, self.resume_interrupted, self.open_ui_on_login
        )):
            raise BootPreferenceError("boot_preferences_require_booleans")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "start_on_login": self.start_on_login,
            "resume_interrupted": self.resume_interrupted,
            "open_ui_on_login": self.open_ui_on_login,
        }


_KEYS = frozenset(BootPreferences().to_mapping())


def parse_preferences(data: Any) -> BootPreferences:
    if not isinstance(data, dict) or set(data) != _KEYS:
        raise BootPreferenceError("boot_preferences_schema_invalid")
    if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
        raise BootPreferenceError("boot_preferences_version_unsupported")
    return BootPreferences(
        start_on_login=data["start_on_login"],
        resume_interrupted=data["resume_interrupted"],
        open_ui_on_login=data["open_ui_on_login"],
    )


def _is_redirect(candidate: Path, info: Any) -> bool:
    if stat.S_ISLNK(info.st_mode):
        return True
    if getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        return True
    is_junction = getattr(candidate, "is_junction", None)
    return bool(is_junction is not None and is_junction())


def _validate_location(path: Path) -> None:
    """Refuse existing symlink/junction/reparse redirects on the lexical path.

    Every existing component of the unresolved absolute path is inspected with
    lstat; missing components cannot redirect and are skipped. Any other
    inspection failure is treated as untrusted. This is a deterministic
    preflight, not a race-proof guard against a concurrent path swap.
    """
    if path.suffix.lower() != ".json":
        raise BootPreferenceError("boot_preferences_path_untrusted")
    try:
        absolute = path.absolute()
    except OSError as exc:
        raise BootPreferenceError("boot_preferences_path_untrusted") from exc
    for candidate in (absolute, *absolute.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise BootPreferenceError("boot_preferences_path_untrusted") from exc
        if _is_redirect(candidate, info):
            raise BootPreferenceError("boot_preferences_path_untrusted")


def _read_bounded(target: Path) -> bytes:
    """Read at most one byte past the cap so overflow is detected, not loaded."""
    limit = MAX_PREFERENCE_BYTES + 1
    chunks: list[bytes] = []
    received = 0
    with target.open("rb") as fp:
        while received < limit:
            chunk = fp.read(limit - received)
            if not chunk:
                break
            chunks.append(chunk)
            received += len(chunk)
    return b"".join(chunks)


def load_preferences(path: str | Path) -> BootPreferences:
    """Missing config means OFF/OFF, not automatic owner consent.

    Malformed content is a hard error; never treat it as enabled defaults.
    """
    target = Path(path)
    _validate_location(target)
    try:
        payload = _read_bounded(target)
    except FileNotFoundError:
        return BootPreferences()
    except OSError as exc:
        raise BootPreferenceError("boot_preferences_read_failed") from exc
    if len(payload) > MAX_PREFERENCE_BYTES:
        raise BootPreferenceError("boot_preferences_oversized")
    try:
        return parse_preferences(json.loads(payload.decode("utf-8-sig")))
    except (ValueError, UnicodeError) as exc:
        raise BootPreferenceError("boot_preferences_invalid_json") from exc


def save_preferences(path: str | Path, preferences: BootPreferences) -> None:
    """Atomic owner-initiated preference write; no OS registration side effect."""
    if not isinstance(preferences, BootPreferences):
        raise BootPreferenceError("boot_preferences_type_invalid")
    target = Path(path)
    _validate_location(target)
    if not target.parent.is_dir():
        raise BootPreferenceError("boot_preferences_parent_missing")
    content = (json.dumps(preferences.to_mapping(), sort_keys=True) + "\n").encode("utf-8")
    fd, temp_name = tempfile.mkstemp(prefix=".nerelan-boot-", suffix=".tmp", dir=target.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as fp:
            fp.write(content)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()


@dataclass(frozen=True)
class BootEvidence:
    """Explicit external attestations; never inferred from a RUNNING Task row."""

    stable_release_verified: bool = False
    same_owner_identity: bool = False
    authorized_window_current: bool = False
    same_frozen_task_identity: bool = False
    task_resume_allowed: bool = False
    local_checkpoint_verified: bool = False
    external_receipts_reconciled: bool = False
    no_duplicate_side_effect: bool = False

    def __post_init__(self) -> None:
        if any(type(value) is not bool for value in vars(self).values()):
            raise BootPreferenceError("boot_evidence_require_booleans")


def plan_boot(preferences: BootPreferences, evidence: BootEvidence, *,
              trigger: str = "logon") -> dict[str, Any]:
    """Advice only. Never grants actual provider dispatch or extends a window.

    The trusted host must separately revalidate all receipt/lease identities at
    resume time, even after this plan says it may REQUEST reconciliation.
    """
    result: dict[str, Any] = {
        "action": "HOLD",
        "reason": "unverified_boot",
        "dispatch_permitted": False,
        "window_auto_extended": False,
        "scheduled_task_installed": False,
        "can_request_fenced_resume": False,
        "autostart_enabled": preferences.start_on_login,
        "resume_enabled": preferences.resume_interrupted,
    }
    if trigger not in {"logon", "manual"}:
        return result | {"reason": "unsupported_boot_trigger"}
    if trigger == "logon" and not preferences.start_on_login:
        return result | {"action": "NO_AUTOSTART", "reason": "owner_opted_out"}
    if not evidence.stable_release_verified or not evidence.same_owner_identity:
        return result | {"reason": "stable_release_or_owner_unverified"}
    if not preferences.resume_interrupted:
        return result | {"action": "START_APP_ONLY", "reason": "resume_disabled"}
    requirements = (
        ("authorized_window_current", "owner_window_not_current"),
        ("same_frozen_task_identity", "task_identity_not_verified"),
        ("task_resume_allowed", "task_resume_not_authorized"),
        ("local_checkpoint_verified", "checkpoint_not_verified"),
        ("external_receipts_reconciled", "external_jobs_unreconciled"),
        ("no_duplicate_side_effect", "idempotency_not_verified"),
    )
    for key, reason in requirements:
        if not getattr(evidence, key):
            return result | {"action": "START_APP_WITH_RESUME_HELD", "reason": reason}
    return result | {
        "action": "REQUEST_FENCED_RECONCILIATION",
        "reason": "all_boot_preconditions_attested",
        "can_request_fenced_resume": True,
    }
