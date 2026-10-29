"""Provider-free opt-in Windows lifecycle preference and resume-policy tests.

Neither this fixture nor the imported module installs a scheduled task,
launches Nerelan, replays a job, or calls an external provider.
"""
from dataclasses import replace
import json
from pathlib import Path
import stat
import sys
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.boot_preferences import (
    BootEvidence, BootPreferenceError, BootPreferences,
    load_preferences, parse_preferences, plan_boot, save_preferences,
)
from reverse_agent.platform_v1.boot_preferences import MAX_PREFERENCE_BYTES


def verified():
    return BootEvidence(
        stable_release_verified=True,
        same_owner_identity=True,
        authorized_window_current=True,
        same_frozen_task_identity=True,
        task_resume_allowed=True,
        local_checkpoint_verified=True,
        external_receipts_reconciled=True,
        no_duplicate_side_effect=True,
    )


def test_default_preferences_are_off_independently(tmp_path):
    path = tmp_path / "boot.json"
    assert load_preferences(path) == BootPreferences()
    assert not path.exists()


def test_enable_both_requires_explicit_persist_and_roundtrips(tmp_path):
    path = tmp_path / "boot.json"
    preferences = BootPreferences(start_on_login=True, resume_interrupted=True)
    save_preferences(path, preferences)
    assert load_preferences(path) == preferences
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_disable_autostart_keeps_manual_resume_opt_in(tmp_path):
    path = tmp_path / "boot.json"
    save_preferences(path, BootPreferences(start_on_login=True, resume_interrupted=True))
    save_preferences(path, BootPreferences(start_on_login=False, resume_interrupted=True))
    assert load_preferences(path).resume_interrupted
    assert not load_preferences(path).start_on_login
    assert not list(tmp_path.glob(".nerelan-boot-*.tmp"))


@pytest.mark.parametrize("payload", [
    {},
    {"schema_version": 2, "start_on_login": False, "resume_interrupted": False,
     "open_ui_on_login": False},
    {"schema_version": 1, "start_on_login": "true", "resume_interrupted": False,
     "open_ui_on_login": False},
    {"schema_version": 1, "start_on_login": False, "resume_interrupted": 1,
     "open_ui_on_login": False},
    {"schema_version": True, "start_on_login": False, "resume_interrupted": False,
     "open_ui_on_login": False},
    {"schema_version": 1, "start_on_login": False, "resume_interrupted": False,
     "open_ui_on_login": False, "unknown": True},
])
def test_schema_invalid_or_ambiguous_is_refused(payload):
    with pytest.raises(BootPreferenceError):
        parse_preferences(payload)


def test_malformed_and_oversized_preferences_fail_closed(tmp_path):
    path = tmp_path / "boot.json"
    for content in (b"{bad json", b"x" * 4200, b"\xff"):
        path.write_bytes(content)
        with pytest.raises(BootPreferenceError):
            load_preferences(path)


def test_symlink_preferences_rejected(tmp_path):
    outside = tmp_path / "elsewhere.json"
    outside.write_text("{}", encoding="utf-8")
    shortcut = tmp_path / "boot.json"
    try:
        shortcut.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink privilege unavailable on test host")
    with pytest.raises(BootPreferenceError):
        load_preferences(shortcut)


def test_reject_parent_missing_instead_of_creating_unexpected_directory(tmp_path):
    with pytest.raises(BootPreferenceError):
        save_preferences(tmp_path / "uncreated" / "boot.json",
                         BootPreferences(start_on_login=True))
    assert not (tmp_path / "uncreated").exists()


def test_logon_does_not_launch_without_owner_optin():
    result = plan_boot(BootPreferences(), verified())
    assert result["action"] == "NO_AUTOSTART"
    assert not result["dispatch_permitted"]
    assert not result["scheduled_task_installed"]


def test_app_autostart_does_not_also_enable_task_resume():
    result = plan_boot(BootPreferences(start_on_login=True), verified())
    assert result["action"] == "START_APP_ONLY"
    assert not result["can_request_fenced_resume"]
    assert not result["window_auto_extended"]


def test_separate_resume_optin_can_be_used_after_manual_launch():
    preferences = BootPreferences(resume_interrupted=True)
    assert plan_boot(preferences, verified(), trigger="logon")["action"] == "NO_AUTOSTART"
    result = plan_boot(preferences, verified(), trigger="manual")
    assert result["action"] == "REQUEST_FENCED_RECONCILIATION"
    assert not result["dispatch_permitted"]


@pytest.mark.parametrize("missing,reason", [
    ("stable_release_verified", "stable_release_or_owner_unverified"),
    ("same_owner_identity", "stable_release_or_owner_unverified"),
    ("authorized_window_current", "owner_window_not_current"),
    ("same_frozen_task_identity", "task_identity_not_verified"),
    ("task_resume_allowed", "task_resume_not_authorized"),
    ("local_checkpoint_verified", "checkpoint_not_verified"),
    ("external_receipts_reconciled", "external_jobs_unreconciled"),
    ("no_duplicate_side_effect", "idempotency_not_verified"),
])
def test_missing_one_verified_condition_holds_resume(missing, reason):
    result = plan_boot(
        BootPreferences(start_on_login=True, resume_interrupted=True),
        replace(verified(), **{missing: False}),
    )
    assert result["action"] == ("HOLD" if missing in (
        "stable_release_verified", "same_owner_identity",
    ) else "START_APP_WITH_RESUME_HELD")
    assert result["reason"] == reason
    assert not result["can_request_fenced_resume"]
    assert not result["dispatch_permitted"]


def test_even_all_positive_evidence_only_requests_fenced_reconciliation():
    result = plan_boot(BootPreferences(
        start_on_login=True, resume_interrupted=True, open_ui_on_login=False), verified())
    assert result["action"] == "REQUEST_FENCED_RECONCILIATION"
    assert result["can_request_fenced_resume"]
    assert result["dispatch_permitted"] is False
    assert result["window_auto_extended"] is False
    assert result["scheduled_task_installed"] is False


def test_unsupported_boot_trigger_is_not_authorized():
    result = plan_boot(BootPreferences(start_on_login=True), verified(), trigger="on_power_on")
    assert result["action"] == "HOLD"
    assert not result["dispatch_permitted"]


def test_booleans_cannot_be_written_as_numeric_ints():
    with pytest.raises(BootPreferenceError):
        BootPreferences(start_on_login=1)
    with pytest.raises(BootPreferenceError):
        BootEvidence(external_receipts_reconciled=1)


# --- Bounded preference reads -------------------------------------------------

READ_LIMIT = MAX_PREFERENCE_BYTES + 1
BOM = b"\xef\xbb\xbf"


class _RecordingReader:
    """Wraps the actual binary handle; records every read request and result."""

    def __init__(self, handle, reads, chunk_limit=None):
        self._handle = handle
        self._reads = reads
        self._chunk_limit = chunk_limit

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self._handle.close()
        return False

    def read(self, size=-1):
        request = size
        if self._chunk_limit is not None and isinstance(size, int) and size > 0:
            request = min(size, self._chunk_limit)
        data = self._handle.read(request)
        self._reads.append((size, len(data)))
        return data

    def __getattr__(self, name):
        raise AssertionError(f"unrecorded handle access: {name}")


def _record_reads(monkeypatch, *, grow_by=0, chunk_limit=None):
    reads = []
    original_open = Path.open

    def recording_open(self, mode="r", *args, **kwargs):
        if mode != "rb":
            return original_open(self, mode, *args, **kwargs)
        if grow_by:
            with original_open(self, "ab") as fp:
                fp.write(b" " * grow_by)
        return _RecordingReader(original_open(self, mode, *args, **kwargs),
                                reads, chunk_limit)

    monkeypatch.setattr(Path, "open", recording_open)
    return reads


def _assert_bounded(reads):
    assert reads, "load_preferences must read through the instrumented handle"
    for request, returned in reads:
        assert type(request) is int and 0 < request <= READ_LIMIT
        assert returned <= request
    assert sum(returned for _, returned in reads) <= READ_LIMIT


def _padded(size, prefix=b""):
    body = prefix + json.dumps(BootPreferences(start_on_login=True).to_mapping()).encode()
    assert len(body) <= size
    return body + b" " * (size - len(body))


def test_actual_1mib_file_is_rejected_after_bounded_read(tmp_path, monkeypatch):
    path = tmp_path / "boot.json"
    path.write_bytes(b" " * (1 << 20))
    reads = _record_reads(monkeypatch)
    with pytest.raises(BootPreferenceError, match="boot_preferences_oversized"):
        load_preferences(path)
    _assert_bounded(reads)
    assert sum(returned for _, returned in reads) == READ_LIMIT


@pytest.mark.parametrize("prefix", [b"", BOM])
def test_exact_cap_loads_and_one_over_is_oversized(tmp_path, monkeypatch, prefix):
    path = tmp_path / "boot.json"
    reads = _record_reads(monkeypatch)
    path.write_bytes(_padded(MAX_PREFERENCE_BYTES, prefix))
    assert load_preferences(path) == BootPreferences(start_on_login=True)
    _assert_bounded(reads)
    reads.clear()
    path.write_bytes(_padded(MAX_PREFERENCE_BYTES + 1, prefix))
    with pytest.raises(BootPreferenceError, match="boot_preferences_oversized"):
        load_preferences(path)
    _assert_bounded(reads)


def test_short_reads_are_accumulated_within_bound(tmp_path, monkeypatch):
    path = tmp_path / "boot.json"
    path.write_bytes(_padded(MAX_PREFERENCE_BYTES))
    reads = _record_reads(monkeypatch, chunk_limit=1000)
    assert load_preferences(path) == BootPreferences(start_on_login=True)
    _assert_bounded(reads)
    reads.clear()
    path.write_bytes(_padded(MAX_PREFERENCE_BYTES * 3))
    with pytest.raises(BootPreferenceError, match="boot_preferences_oversized"):
        load_preferences(path)
    _assert_bounded(reads)


def test_file_growth_after_validation_is_still_bounded(tmp_path, monkeypatch):
    path = tmp_path / "boot.json"
    save_preferences(path, BootPreferences(start_on_login=True))
    reads = _record_reads(monkeypatch, grow_by=1 << 20)
    with pytest.raises(BootPreferenceError, match="boot_preferences_oversized"):
        load_preferences(path)
    _assert_bounded(reads)
    assert path.stat().st_size > (1 << 20)


def test_bom_small_file_and_missing_default_unchanged_by_bounded_read(tmp_path, monkeypatch):
    path = tmp_path / "boot.json"
    reads = _record_reads(monkeypatch)
    assert load_preferences(path) == BootPreferences()
    assert not path.exists()
    path.write_bytes(BOM + json.dumps(
        BootPreferences(resume_interrupted=True).to_mapping()).encode())
    assert load_preferences(path) == BootPreferences(resume_interrupted=True)
    _assert_bounded(reads)


def test_open_and_read_failures_remain_typed(tmp_path, monkeypatch):
    path = tmp_path / "boot.json"
    save_preferences(path, BootPreferences())

    class FailingHandle:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def read(self, size=-1):
            raise OSError("simulated read failure")

    monkeypatch.setattr(Path, "open", lambda self, mode="r", *a, **k: FailingHandle())
    with pytest.raises(BootPreferenceError, match="boot_preferences_read_failed"):
        load_preferences(path)

    def denied(self, mode="r", *a, **k):
        raise PermissionError("simulated open denial")

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(BootPreferenceError, match="boot_preferences_read_failed"):
        load_preferences(path)


# --- Redirected ancestor refusal ----------------------------------------------

def _fake_lstat(monkeypatch, flagged, info=None, error=None):
    original_lstat = Path.lstat

    def lstat(self, *args, **kwargs):
        if self == flagged:
            if error is not None:
                raise error
            return info
        return original_lstat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", lstat)


REPARSE_DIR = SimpleNamespace(st_mode=stat.S_IFDIR | 0o755,
                              st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
SYMLINK = SimpleNamespace(st_mode=stat.S_IFLNK | 0o777, st_file_attributes=0)


def _assert_load_and_save_refused(path, original):
    with pytest.raises(BootPreferenceError, match="boot_preferences_path_untrusted"):
        load_preferences(path)
    with pytest.raises(BootPreferenceError, match="boot_preferences_path_untrusted"):
        save_preferences(path, BootPreferences(start_on_login=False, resume_interrupted=True))
    assert path.read_bytes() == original
    assert not list(path.parent.glob(".nerelan-boot-*.tmp"))


@pytest.mark.parametrize("info", [REPARSE_DIR, SYMLINK], ids=["reparse", "symlink"])
@pytest.mark.parametrize("depth", ["parent", "ancestor"])
def test_redirect_attribute_anywhere_on_chain_refuses_load_and_save(
        tmp_path, monkeypatch, info, depth):
    alias = tmp_path / "alias"
    parent = alias if depth == "parent" else alias / "sub"
    parent.mkdir(parents=True)
    path = parent / "boot.json"
    save_preferences(path, BootPreferences(start_on_login=True, resume_interrupted=True))
    original = path.read_bytes()
    _fake_lstat(monkeypatch, alias, info=info)
    _assert_load_and_save_refused(path, original)


def test_reparse_attribute_on_target_file_is_refused(tmp_path, monkeypatch):
    path = tmp_path / "boot.json"
    save_preferences(path, BootPreferences(start_on_login=True))
    original = path.read_bytes()
    _fake_lstat(monkeypatch, path, info=SimpleNamespace(
        st_mode=stat.S_IFREG | 0o644, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT))
    _assert_load_and_save_refused(path, original)


def test_ancestor_inspection_failure_does_not_authorize_write(tmp_path, monkeypatch):
    parent = tmp_path / "owner"
    parent.mkdir()
    path = parent / "boot.json"
    _fake_lstat(monkeypatch, parent, error=PermissionError("simulated lstat denial"))
    with pytest.raises(BootPreferenceError, match="boot_preferences_path_untrusted"):
        save_preferences(path, BootPreferences(start_on_login=True))
    with pytest.raises(BootPreferenceError, match="boot_preferences_path_untrusted"):
        load_preferences(path)
    assert not path.exists()
    assert not list(parent.glob(".nerelan-boot-*.tmp"))


def test_symlinked_ancestor_directory_rejected(tmp_path):
    real = tmp_path / "real" / "sub"
    real.mkdir(parents=True)
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(tmp_path / "real", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink privilege unavailable on test host")
    target = real / "boot.json"
    save_preferences(target, BootPreferences(start_on_login=True))
    original = target.read_bytes()
    _assert_load_and_save_refused(alias / "sub" / "boot.json", original)


def _create_junction_or_skip(link, target):
    if sys.platform != "win32":
        pytest.skip("Windows directory junctions unavailable")
    try:
        import _winapi
        create_junction = _winapi.CreateJunction
    except (ImportError, AttributeError):
        pytest.skip("junction creation API unavailable")
    try:
        create_junction(str(target), str(link))
    except OSError:
        pytest.skip("junction creation refused on test host")
    if hasattr(link, "is_junction"):
        assert link.is_junction()
    assert not link.is_symlink()


@pytest.mark.parametrize("depth", ["parent", "ancestor"])
def test_actual_windows_junction_parent_or_ancestor_refused(tmp_path, depth):
    real = tmp_path / "junction-target"
    (real / "sub").mkdir(parents=True)
    alias = tmp_path / "junction-alias"
    _create_junction_or_skip(alias, real)
    relative = Path("boot.json") if depth == "parent" else Path("sub", "boot.json")
    target = real / relative
    save_preferences(target, BootPreferences(start_on_login=True, resume_interrupted=True))
    original = target.read_bytes()
    redirected = alias / relative
    assert redirected.read_bytes() == original
    _assert_load_and_save_refused(redirected, original)
    assert load_preferences(target) == BootPreferences(
        start_on_login=True, resume_interrupted=True)


def test_ordinary_nested_relative_and_missing_paths_still_trusted(tmp_path, monkeypatch):
    nested = tmp_path / "owner" / "profile"
    nested.mkdir(parents=True)
    path = nested / "boot.json"
    save_preferences(path, BootPreferences(open_ui_on_login=True))
    assert load_preferences(path) == BootPreferences(open_ui_on_login=True)
    assert load_preferences(tmp_path / "absent" / "deeper" / "boot.json") == BootPreferences()
    monkeypatch.chdir(nested)
    assert load_preferences("boot.json") == BootPreferences(open_ui_on_login=True)
    save_preferences(Path("boot.json"), BootPreferences(resume_interrupted=True))
    assert load_preferences(path) == BootPreferences(resume_interrupted=True)


def test_drive_root_level_missing_file_defaults_off():
    root_level = Path(Path.cwd().anchor) / "nerelan-boot-preferences-absent-fixture.json"
    if root_level.exists():
        pytest.skip("unexpected fixture name present at drive root")
    assert load_preferences(root_level) == BootPreferences()
    assert not root_level.exists()


def test_suffix_rule_still_enforced_before_inspection(tmp_path):
    with pytest.raises(BootPreferenceError, match="boot_preferences_path_untrusted"):
        load_preferences(tmp_path / "boot.txt")
    with pytest.raises(BootPreferenceError, match="boot_preferences_path_untrusted"):
        save_preferences(tmp_path / "boot", BootPreferences())
    assert load_preferences(tmp_path / "BOOT.JSON") == BootPreferences()
