"""Phase A: machine-generated evidence recorder authenticity tests.

Covers ``reverse_agent.control_plane.evidence_recorder`` which validates that
execution records are machine-generated, cryptographically sound, and temporally
consistent. Hand-crafted records with future timestamps, malformed digests,
fake head SHAs, or stale bootstrap authority must be rejected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reverse_agent.control_plane.evidence_recorder import (
    EvidenceRecorder,
    _read_raw_evidence,
    validate_record_authenticity,
)
from reverse_agent.control_plane.evidence_source import (
    NORMALIZED_EVIDENCE_SOURCES,
    normalize_evidence_source,
)
from reverse_agent.control_plane.models import (
    ExecutionRecord,
    TransitionCommand,
    TransitionCommandPlan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plan_with_commands(*commands: TransitionCommand) -> TransitionCommandPlan:
    return TransitionCommandPlan(
        decision_id="decision_evidence_auth",
        round_id="round_evidence_auth",
        commands=commands,
    )


def _command(
    command_id: str = "status.git_status",
    command: str = "git status --short",
) -> TransitionCommand:
    return TransitionCommand(
        command_id=command_id,
        command=command,
        phase="status",
        required=True,
        expected_exit_codes=(0,),
        execution_surface="local",
        operations=("repository_observation",),
        authority_origin="normal_plan",
    )


def _record(
    *,
    command_id: str = "status.git_status",
    command: str = "git status --short",
    started_at: str = "2026-07-21T10:00:00Z",
    observed_at: str = "2026-07-21T10:00:01Z",
    head_before: str = "a" * 40,
    head_after: str = "a" * 40,
    stdout_digest: str = "sha256:" + "0" * 64,
    stderr_digest: str = "sha256:" + "0" * 64,
    authority_origin: str = "normal_plan",
) -> ExecutionRecord:
    return ExecutionRecord(
        command_id=command_id,
        command=command,
        execution_surface="local",
        operations=("repository_observation",),
        mutated_paths=(),
        exit_code=0,
        started_at=started_at,
        observed_at=observed_at,
        head_before=head_before,
        head_after=head_after,
        stdout_digest=stdout_digest,
        stderr_digest=stderr_digest,
        authority_origin=authority_origin,
        decision_id="decision_evidence_auth",
        round_id="round_evidence_auth",
    )


# ---------------------------------------------------------------------------
# Timestamp validation
# ---------------------------------------------------------------------------


def test_future_timestamp_rejected() -> None:
    """Records with started_at in the future must be rejected."""

    record = _record(started_at="9999-01-01T00:00:00Z")
    plan = _plan_with_commands(_command())
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
    )
    assert any("future_timestamp" in e for e in errors), errors


def test_future_observed_at_rejected() -> None:
    """Records with observed_at in the future must be rejected."""

    record = _record(observed_at="9999-01-01T00:00:00Z")
    plan = _plan_with_commands(_command())
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
    )
    assert any("future_timestamp" in e for e in errors), errors


def test_non_monotonic_time_rejected() -> None:
    """started_at must not be later than observed_at."""

    record = _record(
        started_at="2026-07-21T10:00:10Z",
        observed_at="2026-07-21T10:00:05Z",
    )
    plan = _plan_with_commands(_command())
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:20Z",
    )
    assert any("non_monotonic_time" in e for e in errors), errors


def test_malformed_timestamp_rejected() -> None:
    """Timestamps must be valid RFC3339 UTC."""

    record = _record(started_at="not-a-timestamp")
    plan = _plan_with_commands(_command())
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
    )
    assert any("malformed_timestamp" in e for e in errors), errors


# ---------------------------------------------------------------------------
# Digest validation
# ---------------------------------------------------------------------------


def test_malformed_stdout_digest_rejected() -> None:
    """stdout_digest must be sha256:<64 lowercase hex>."""

    record = _record(stdout_digest="sha256:tests_passed")
    plan = _plan_with_commands(_command())
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
    )
    assert any("malformed_digest" in e for e in errors), errors


def test_malformed_stderr_digest_rejected() -> None:
    """stderr_digest must be sha256:<64 lowercase hex>."""

    record = _record(stderr_digest="sha256:empty")
    plan = _plan_with_commands(_command())
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
    )
    assert any("malformed_digest" in e for e in errors), errors


def test_uppercase_hex_digest_rejected() -> None:
    """Digest hex must be lowercase."""

    record = _record(stdout_digest="sha256:" + "A" * 64)
    plan = _plan_with_commands(_command())
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
    )
    assert any("malformed_digest" in e for e in errors), errors


def test_digest_mismatch_rejected() -> None:
    """When raw output is supplied, digest must match sha256(raw)."""

    import hashlib

    record = _record(stdout_digest="sha256:" + "0" * 64)
    plan = _plan_with_commands(_command())
    raw_stdout = b"real output"
    expected = "sha256:" + hashlib.sha256(raw_stdout).hexdigest()
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
        raw_stdout=raw_stdout,
    )
    assert any("digest_mismatch" in e for e in errors), errors
    assert expected  # sanity


# ---------------------------------------------------------------------------
# Head SHA validation
# ---------------------------------------------------------------------------


def test_fake_head_sha_rejected() -> None:
    """head_before / head_after must be 40-char lowercase hex git SHA."""

    record = _record(head_before="short")
    plan = _plan_with_commands(_command())
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
    )
    assert any("malformed_head_sha" in e for e in errors), errors


def test_uppercase_head_sha_rejected() -> None:
    """Head SHA must be lowercase hex."""

    record = _record(head_after="A" * 40)
    plan = _plan_with_commands(_command())
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
    )
    assert any("malformed_head_sha" in e for e in errors), errors


# ---------------------------------------------------------------------------
# Command ID binding
# ---------------------------------------------------------------------------


def test_manually_claimed_command_id_rejected() -> None:
    """command_id must match a plan entry with the same command string."""

    record = _record(command_id="status.git_status", command="git status --short")
    other_command = TransitionCommand(
        command_id="status.git_status",
        command="git rev-parse HEAD",  # different command string
        phase="status",
        required=True,
        expected_exit_codes=(0,),
        execution_surface="local",
        operations=("repository_observation",),
    )
    plan = _plan_with_commands(other_command)
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
    )
    assert any("command_id_mismatch" in e for e in errors), errors


def test_unknown_command_id_rejected() -> None:
    """command_id not in plan must be rejected."""

    record = _record(command_id="unknown.cmd")
    plan = _plan_with_commands(_command())
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
    )
    assert any("command_id_mismatch" in e for e in errors), errors


# ---------------------------------------------------------------------------
# Bootstrap authority
# ---------------------------------------------------------------------------


def test_bootstrap_authority_after_expiry_rejected() -> None:
    """After BOOTSTRAP_EXPIRED, records cannot claim bootstrap authority."""

    record = _record(authority_origin="bootstrap_exception")
    plan = _plan_with_commands(_command())
    from reverse_agent.control_plane.models import BootstrapState

    bootstrap = BootstrapState(
        status="BOOTSTRAP_EXPIRED",
        decision_id="decision_evidence_auth",
        round_id="round_evidence_auth",
        expired_at="2026-07-21T09:00:00Z",
    )
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
        bootstrap_state=bootstrap,
    )
    assert any("bootstrap_authority_after_expiry" in e for e in errors), errors


def test_bootstrap_record_observed_before_expiry_remains_valid() -> None:
    """Later replay uses observed_at <= expired_at, not current expiry alone."""

    record = _record(
        authority_origin="bootstrap_exception",
        observed_at="2026-07-21T08:59:59Z",
    )
    plan = _plan_with_commands(_command())
    from reverse_agent.control_plane.models import BootstrapState

    bootstrap = BootstrapState(
        status="BOOTSTRAP_EXPIRED",
        decision_id="decision_evidence_auth",
        round_id="round_evidence_auth",
        expired_at="2026-07-21T09:00:00Z",
    )
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
        bootstrap_state=bootstrap,
    )
    assert "bootstrap_authority_after_expiry" not in errors


def test_bootstrap_expiry_accepts_generator_offset_utc_format() -> None:
    record = _record(
        authority_origin="bootstrap_exception",
        observed_at="2026-07-21T08:59:59Z",
    )
    plan = _plan_with_commands(_command())
    from reverse_agent.control_plane.models import BootstrapState

    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
        bootstrap_state=BootstrapState(
            status="BOOTSTRAP_EXPIRED",
            decision_id="decision_evidence_auth",
            round_id="round_evidence_auth",
            expired_at="2026-07-21T09:00:00+00:00",
        ),
    )
    assert "bootstrap_authority_after_expiry" not in errors


def test_raw_evidence_reader_accepts_windows_style_relative_path(tmp_path: Path) -> None:
    evidence = tmp_path / "project_state" / "gates" / "evidence" / "stdout.bin"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"portable")
    ok, raw = _read_raw_evidence(
        tmp_path, "project_state\\gates\\evidence\\stdout.bin"
    )
    assert ok is True
    assert raw == b"portable"


@pytest.mark.parametrize("stored", ["../outside.bin", "/tmp/outside.bin", "C:/outside.bin"])
def test_raw_evidence_reader_rejects_repo_escape(tmp_path: Path, stored: str) -> None:
    assert _read_raw_evidence(tmp_path, stored) == (False, b"")


# ---------------------------------------------------------------------------
# EvidenceRecorder: machine-generated records
# ---------------------------------------------------------------------------


def test_recorder_produces_authentic_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """EvidenceRecorder must produce a record that passes authenticity check."""

    import hashlib
    import subprocess

    plan = _plan_with_commands(_command())

    # Stub git rev-parse to return stable SHAs.
    def fake_run(*args, **kwargs):
        if args and "rev-parse" in args[0]:
            return subprocess.CompletedProcess(args[0], 0, "abcdef0123456789abcdef0123456789abcdef01\n", "")
        if args and "status" in args[0]:
            return subprocess.CompletedProcess(args[0], 0, " M file.py\n", "")
        return subprocess.CompletedProcess(args[0], 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    # Stub datetime to a fixed time.
    from reverse_agent.control_plane import evidence_recorder as recorder_mod

    fixed_time = "2026-07-21T10:00:00Z"
    monkeypatch.setattr(recorder_mod, "_now_utc", lambda: fixed_time)

    recorder = EvidenceRecorder(repo_root=tmp_path, plan=plan)
    record = recorder.record(
        command_id="status.git_status",
        command="git status --short",
        raw_stdout=b" M file.py\n",
        raw_stderr=b"",
        exit_code=0,
    )
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at=fixed_time,
    )
    assert errors == [], errors
    # Digest must match actual output.
    expected_digest = "sha256:" + hashlib.sha256(b" M file.py\n").hexdigest()
    assert record.stdout_digest == expected_digest


def test_recorder_rejects_hand_edited_record(tmp_path: Path) -> None:
    """A hand-edited record with fake digest must fail authenticity check."""

    plan = _plan_with_commands(_command())
    record = _record(stdout_digest="sha256:" + "0" * 64)  # fake digest
    errors = validate_record_authenticity(
        record,
        plan=plan,
        recorder_observed_at="2026-07-21T10:00:05Z",
        raw_stdout=b"actual output that does not match",
    )
    assert any("digest_mismatch" in e for e in errors), errors


# ---------------------------------------------------------------------------
# Phase C: evidence source normalization
#
# The legacy ``required_evidence_source`` field uses values that mix local
# command evidence with CI attestation semantics. Phase C normalizes these
# to three explicit sources:
#
# - ``local_command_evidence`` — local focused tests, recorder-proven
# - ``repository_state_attestation`` — git ancestry / branch identity
# - ``ci_check_attestation`` — external CI check identity (CI, State Gate,
#   Decision Preflight)
#
# Local commands must not be falsely represented as CI evidence (F5).
# ---------------------------------------------------------------------------


def test_old_local_provenance_normalizes_to_local_command_evidence() -> None:
    """local_provenance → local_command_evidence."""

    assert normalize_evidence_source("local_provenance") == "local_command_evidence"


def test_old_repository_truth_normalizes_to_repository_state_attestation() -> None:
    """repository_truth → repository_state_attestation."""

    assert normalize_evidence_source("repository_truth") == "repository_state_attestation"


def test_old_exact_head_ci_normalizes_to_ci_check_attestation() -> None:
    """exact_head_ci → ci_check_attestation."""

    assert normalize_evidence_source("exact_head_ci") == "ci_check_attestation"


def test_new_sources_are_idempotent() -> None:
    """New normalized sources normalize to themselves."""

    assert normalize_evidence_source("local_command_evidence") == "local_command_evidence"
    assert normalize_evidence_source("repository_state_attestation") == "repository_state_attestation"
    assert normalize_evidence_source("ci_check_attestation") == "ci_check_attestation"


def test_empty_source_normalizes_to_local_command_evidence() -> None:
    """Empty/missing source defaults to local_command_evidence (fail-safe)."""

    assert normalize_evidence_source("") == "local_command_evidence"
    assert normalize_evidence_source(None) == "local_command_evidence"


def test_invalid_source_raises() -> None:
    """Unknown source values are rejected, not silently coerced."""

    with pytest.raises(ValueError):
        normalize_evidence_source("totally_made_up_source")


def test_normalized_source_set_contains_three_sources() -> None:
    """The normalized source set contains exactly the three Phase C sources."""

    assert NORMALIZED_EVIDENCE_SOURCES == frozenset({
        "local_command_evidence",
        "repository_state_attestation",
        "ci_check_attestation",
    })


def test_transition_command_normalizes_legacy_evidence_source() -> None:
    """TransitionCommand.from_mapping normalizes legacy evidence source values."""

    cmd = TransitionCommand.from_mapping({
        "command": "git rev-parse HEAD",
        "phase": "status",
        "required": True,
        "expected_exit_codes": [0],
        "execution_surface": "local",
        "required_evidence_source": "repository_truth",
    })
    assert cmd.required_evidence_source == "repository_state_attestation"


def test_transition_command_normalizes_exact_head_ci() -> None:
    """exact_head_ci is normalized to ci_check_attestation at parse time."""

    cmd = TransitionCommand.from_mapping({
        "command": "git push origin codex/architecture-spine-v1",
        "phase": "publication",
        "required": False,
        "expected_exit_codes": [0],
        "execution_surface": "local",
        "required_evidence_source": "exact_head_ci",
    })
    assert cmd.required_evidence_source == "ci_check_attestation"


def test_transition_command_rejects_invalid_evidence_source() -> None:
    """Invalid evidence source values are rejected at parse time."""

    with pytest.raises(ValueError):
        TransitionCommand.from_mapping({
            "command": "some-command",
            "phase": "gate",
            "required": True,
            "expected_exit_codes": [0],
            "execution_surface": "local",
            "required_evidence_source": "bogus_source",
        })
