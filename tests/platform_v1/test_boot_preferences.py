"""Provider-free opt-in Windows lifecycle preference and resume-policy tests.

Neither this fixture nor the imported module installs a scheduled task,
launches Nerelan, replays a job, or calls an external provider.
"""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from reverse_agent.platform_v1.boot_preferences import (
    BootEvidence, BootPreferenceError, BootPreferences,
    load_preferences, parse_preferences, plan_boot, save_preferences,
)


def verified():
    return BootEvidence(
        stable_release_verified=True,
        same_owner_identity=True,
        authorized_window_current=True,
        same_frozen_task_identity=True,
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
