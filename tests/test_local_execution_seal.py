"""Phase B: local execution seal tests.

Covers ``transition-reconcile-evaluate`` and ``transition-seal-local``. The
evaluator must read sealed subject records and produce a candidate result. The
sealer must validate the candidate, bind it to subject and plan digests, and
emit a ``LOCAL_RECONCILED`` seal. Neither command may include itself in its
own subject set (F4: non-self-referential reconciliation).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from reverse_agent.control_plane.local_seal import (
    LocalSeal,
    ReconciliationCandidate,
    evaluate_reconciliation,
    seal_local,
)
from reverse_agent.control_plane.models import (
    ExecutionRecord,
    TransitionCommand,
    TransitionCommandPlan,
)
from reverse_agent.control_plane.report_binding import (
    ReportSubjectBinding,
    build_report_subject_binding,
    compute_subject_diff_digest,
    compute_subject_tree_digest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _plan_with_commands(*commands: TransitionCommand) -> TransitionCommandPlan:
    return TransitionCommandPlan(
        decision_id="decision_seal",
        round_id="round_seal",
        commands=commands,
    )


def _command(
    command_id: str = "status.git_status",
    command: str = "git status --short",
    *,
    required: bool = True,
) -> TransitionCommand:
    return TransitionCommand(
        command_id=command_id,
        command=command,
        phase="status",
        required=required,
        expected_exit_codes=(0,),
        execution_surface="local",
        operations=("repository_observation",),
        authority_origin="normal_plan",
    )


def _authentic_record(
    *,
    command_id: str = "status.git_status",
    command: str = "git status --short",
    authority_origin: str = "normal_plan",
) -> ExecutionRecord:
    return ExecutionRecord(
        command_id=command_id,
        command=command,
        execution_surface="local",
        operations=("repository_observation",),
        mutated_paths=(),
        exit_code=0,
        started_at="2026-07-21T08:00:00Z",
        observed_at="2026-07-21T08:00:01Z",
        head_before="a" * 40,
        head_after="a" * 40,
        stdout_digest="sha256:" + "0" * 64,
        stderr_digest="sha256:" + "0" * 64,
        authority_origin=authority_origin,
    )


def _write_execution_log(
    state_dir: Path,
    *,
    decision_id: str = "decision_seal",
    round_id: str = "round_seal",
    records: list[ExecutionRecord],
) -> Path:
    """Write a sealed execution_log.json that the evaluator will read."""

    gates_dir = state_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    log_path = gates_dir / "execution_log.json"
    log_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": decision_id,
                "round_id": round_id,
                "commands": [r.to_dict() for r in records],
            }
        ),
        encoding="utf-8",
    )
    return log_path


# ---------------------------------------------------------------------------
# Phase B.1: ReconciliationCandidate (evaluator)
# ---------------------------------------------------------------------------


def test_evaluate_reconciliation_passes_when_all_required_covered() -> None:
    """Evaluator returns candidate with status=RECONCILED when coverage complete."""

    plan = _plan_with_commands(_command())
    records = (_authentic_record(),)
    candidate = evaluate_reconciliation(plan, records)
    assert candidate.status == "RECONCILED"
    assert candidate.missing_command_ids == ()
    assert candidate.subject_record_count == 1


def test_evaluate_reconciliation_blocks_when_required_missing() -> None:
    """Evaluator returns candidate with status=BLOCKED when required missing."""

    plan = _plan_with_commands(
        _command("status.git_status"),
        _command("test.unit", "python -m pytest tests/test_x.py -q"),
    )
    records = (_authentic_record(),)  # only 1 of 2 required
    candidate = evaluate_reconciliation(plan, records)
    assert candidate.status == "BLOCKED"
    assert "test.unit" in candidate.missing_command_ids


def test_evaluate_reconciliation_blocks_on_unknown_command_id() -> None:
    """Records with command_id not in plan must BLOCK."""

    plan = _plan_with_commands(_command())
    record = _authentic_record(command_id="unknown.cmd")
    candidate = evaluate_reconciliation(plan, (record,))
    assert candidate.status == "BLOCKED"
    assert "unknown_command_id" in " ".join(candidate.blocking_reasons)


def test_evaluate_reconciliation_blocks_on_command_string_divergence() -> None:
    """Record command string must match plan entry."""

    plan = _plan_with_commands(_command())
    record = _authentic_record(command="git rev-parse HEAD")  # diverges
    candidate = evaluate_reconciliation(plan, (record,))
    assert candidate.status == "BLOCKED"


def test_evaluate_reconciliation_blocks_on_exit_code_outside_expected() -> None:
    """Exit code must be in plan's expected_exit_codes."""

    plan = _plan_with_commands(_command())
    record = ExecutionRecord(
        command_id="status.git_status",
        command="git status --short",
        execution_surface="local",
        operations=("repository_observation",),
        mutated_paths=(),
        exit_code=2,  # not in expected [0]
        started_at="2026-07-21T08:00:00Z",
        observed_at="2026-07-21T10:00:01Z",
        head_before="a" * 40,
        head_after="a" * 40,
        stdout_digest="sha256:" + "0" * 64,
        stderr_digest="sha256:" + "0" * 64,
        authority_origin="normal_plan",
    )
    candidate = evaluate_reconciliation(plan, (record,))
    assert candidate.status == "BLOCKED"


# ---------------------------------------------------------------------------
# Phase B.2: subject digest binding (non-self-referential)
# ---------------------------------------------------------------------------


def test_candidate_subject_digest_is_stable() -> None:
    """Subject digest must be a deterministic function of subject records."""

    plan = _plan_with_commands(_command())
    records = (_authentic_record(),)
    c1 = evaluate_reconciliation(plan, records)
    c2 = evaluate_reconciliation(plan, records)
    assert c1.subject_digest == c2.subject_digest
    assert c1.subject_digest.startswith("sha256:")


def test_candidate_subject_digest_excludes_sealer_and_evaluator() -> None:
    """Subject digest must NOT include evaluator/sealer command records.

    F4: the post-execution gate must not include itself in its subject.
    The evaluator and sealer command_ids are never part of the subject set
    even if they appear in the execution log.
    """

    plan = _plan_with_commands(_command())
    subject_record = _authentic_record()
    # Simulate a record that claims to be the evaluator itself.
    evaluator_record = _authentic_record(
        command_id="gate.reconcile_evaluate",
        command="python -m reverse_agent.project_gate transition-reconcile-evaluate --state-dir project_state",
    )
    sealer_record = _authentic_record(
        command_id="gate.seal_local",
        command="python -m reverse_agent.project_gate transition-seal-local --state-dir project_state",
    )
    records_with_self = (subject_record, evaluator_record, sealer_record)
    records_without_self = (subject_record,)
    c_with = evaluate_reconciliation(plan, records_with_self)
    c_without = evaluate_reconciliation(plan, records_without_self)
    assert c_with.subject_digest == c_without.subject_digest, (
        "evaluator/sealer must not be part of subject digest"
    )


# ---------------------------------------------------------------------------
# Phase B.3: LocalSeal (sealer)
# ---------------------------------------------------------------------------


def test_seal_local_produces_local_reconciled() -> None:
    """Sealer emits LOCAL_RECONCILED when candidate is RECONCILED."""

    plan = _plan_with_commands(_command())
    records = (_authentic_record(),)
    candidate = evaluate_reconciliation(plan, records)
    seal = seal_local(
        candidate=candidate,
        plan=plan,
        decision_id="decision_seal",
        round_id="round_seal",
        activation_base_sha="a" * 40,
    )
    assert seal.status == "LOCAL_RECONCILED"
    assert seal.subject_digest == candidate.subject_digest
    assert seal.decision_id == "decision_seal"
    assert seal.round_id == "round_seal"


def test_seal_local_blocks_when_candidate_blocked() -> None:
    """Sealer must not emit LOCAL_RECONCILED when candidate is BLOCKED."""

    plan = _plan_with_commands(
        _command("status.git_status"),
        _command("test.unit", "python -m pytest tests/test_x.py -q"),
    )
    records = (_authentic_record(),)  # missing test.unit
    candidate = evaluate_reconciliation(plan, records)
    seal = seal_local(
        candidate=candidate,
        plan=plan,
        decision_id="decision_seal",
        round_id="round_seal",
        activation_base_sha="a" * 40,
    )
    assert seal.status == "LOCAL_RECONCILIATION_BLOCKED"


def test_seal_local_includes_plan_digest() -> None:
    """Seal must bind the plan digest to prevent plan tampering."""

    plan = _plan_with_commands(_command())
    records = (_authentic_record(),)
    candidate = evaluate_reconciliation(plan, records)
    seal = seal_local(
        candidate=candidate,
        plan=plan,
        decision_id="decision_seal",
        round_id="round_seal",
        activation_base_sha="a" * 40,
    )
    assert seal.plan_digest.startswith("sha256:")
    # Plan digest must be deterministic.
    other_seal = seal_local(
        candidate=candidate,
        plan=plan,
        decision_id="decision_seal",
        round_id="round_seal",
        activation_base_sha="a" * 40,
    )
    assert seal.plan_digest == other_seal.plan_digest


def test_seal_local_includes_result_digest() -> None:
    """Seal must bind the candidate result digest."""

    plan = _plan_with_commands(_command())
    records = (_authentic_record(),)
    candidate = evaluate_reconciliation(plan, records)
    seal = seal_local(
        candidate=candidate,
        plan=plan,
        decision_id="decision_seal",
        round_id="round_seal",
        activation_base_sha="a" * 40,
    )
    assert seal.result_digest.startswith("sha256:")


def test_seal_local_does_not_claim_remote_success() -> None:
    """Local seal must not claim REMOTE_PASSED or ACCEPTED."""

    plan = _plan_with_commands(_command())
    records = (_authentic_record(),)
    candidate = evaluate_reconciliation(plan, records)
    seal = seal_local(
        candidate=candidate,
        plan=plan,
        decision_id="decision_seal",
        round_id="round_seal",
        activation_base_sha="a" * 40,
    )
    assert "REMOTE_PASSED" not in seal.status
    assert seal.status != "ACCEPTED"


# ---------------------------------------------------------------------------
# Phase F: local report subject binding
#
# The local report must bind to the implementation subject via:
#
# - ``activation_base_sha`` — the Decision's activation base
# - ``subject_tree_digest`` — SHA-256 of the subject file tree (sorted)
# - ``subject_diff_digest`` — SHA-256 of the unified diff at report time
# - ``observed_worktree_paths`` — sorted list of dirty paths
# - ``local_seal_digest`` — digest from the LOCAL_RECONCILED seal
#
# The report must not claim final remote HEAD. Final commit/head binding is
# external (publication seal). (F4, Phase F 9.1)
# ---------------------------------------------------------------------------


def test_subject_tree_digest_is_stable_sha256(tmp_path: Path) -> None:
    """subject_tree_digest is a 64-char SHA-256 hex string and is stable."""

    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("print('b')\n", encoding="utf-8")

    digest1 = compute_subject_tree_digest(tmp_path, paths=("a.py", "b.py"))
    digest2 = compute_subject_tree_digest(tmp_path, paths=("b.py", "a.py"))

    assert len(digest1) == 64
    assert all(c in "0123456789abcdef" for c in digest1)
    # Order-independent: sorting paths before hashing.
    assert digest1 == digest2


def test_subject_tree_digest_changes_when_content_changes(tmp_path: Path) -> None:
    """Different file content produces a different tree digest."""

    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    digest_a = compute_subject_tree_digest(tmp_path, paths=("a.py",))

    (tmp_path / "a.py").write_text("print('b')\n", encoding="utf-8")
    digest_b = compute_subject_tree_digest(tmp_path, paths=("a.py",))

    assert digest_a != digest_b


def test_subject_diff_digest_is_stable_sha256(tmp_path: Path) -> None:
    """subject_diff_digest is a 64-char SHA-256 hex string."""

    diff_text = "diff --git a/file.py b/file.py\n+print('hello')\n"
    digest = compute_subject_diff_digest(diff_text)

    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)
    assert hashlib.sha256(diff_text.encode("utf-8")).hexdigest() == digest


# ---------------------------------------------------------------------------
# Phase C (final rework): Authenticity gate is a hard prerequisite to
# reconciliation. The evaluator must call validate_record_authenticity for
# each record BEFORE treating it as a match. Any authenticity error blocks
# the candidate (F3).
# ---------------------------------------------------------------------------


def test_evaluate_reconciliation_blocks_on_future_timestamp() -> None:
    """A record with a future timestamp must block the candidate (F3)."""

    plan = _plan_with_commands(_command())
    record = ExecutionRecord(
        command_id="status.git_status",
        command="git status --short",
        execution_surface="local",
        operations=("repository_observation",),
        mutated_paths=(),
        exit_code=0,
        started_at="2099-12-31T23:59:59Z",  # future
        observed_at="2099-12-31T23:59:59Z",  # future
        head_before="a" * 40,
        head_after="a" * 40,
        stdout_digest="sha256:" + "0" * 64,
        stderr_digest="sha256:" + "0" * 64,
        authority_origin="normal_plan",
    )
    candidate = evaluate_reconciliation(
        plan, (record,), evaluation_time="2026-07-21T08:00:00Z"
    )
    assert candidate.status == "BLOCKED"
    assert any("future_timestamp" in r for r in candidate.blocking_reasons)


def test_evaluate_reconciliation_blocks_on_nonexistent_git_sha(tmp_path: Path) -> None:
    """A record with a git SHA that doesn't exist in the repo must block (F3)."""

    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@e.com"], cwd=str(tmp_path), check=True
    )
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), check=True)
    (tmp_path / "f.txt").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=str(tmp_path), check=True)

    plan = _plan_with_commands(_command())
    record = ExecutionRecord(
        command_id="status.git_status",
        command="git status --short",
        execution_surface="local",
        operations=("repository_observation",),
        mutated_paths=(),
        exit_code=0,
        started_at="2026-07-21T08:00:00Z",
        observed_at="2026-07-21T10:00:01Z",
        head_before="b" * 40,  # doesn't exist in repo
        head_after="b" * 40,
        stdout_digest="sha256:" + "0" * 64,
        stderr_digest="sha256:" + "0" * 64,
        authority_origin="normal_plan",
    )
    candidate = evaluate_reconciliation(plan, (record,), repo_root=tmp_path)
    assert candidate.status == "BLOCKED"
    assert any("git_object_not_found" in r for r in candidate.blocking_reasons)


def test_evaluate_reconciliation_blocks_on_missing_raw_evidence(tmp_path: Path) -> None:
    """A record pointing to non-existent raw evidence must block (F3)."""

    plan = _plan_with_commands(_command())
    record = ExecutionRecord(
        command_id="status.git_status",
        command="git status --short",
        execution_surface="local",
        operations=("repository_observation",),
        mutated_paths=(),
        exit_code=0,
        started_at="2026-07-21T08:00:00Z",
        observed_at="2026-07-21T10:00:01Z",
        head_before="a" * 40,
        head_after="a" * 40,
        stdout_digest="sha256:" + "0" * 64,
        stderr_digest="sha256:" + "0" * 64,
        authority_origin="normal_plan",
        raw_stdout_path="evidence/missing/stdout.bin",  # doesn't exist
        raw_stderr_path="evidence/missing/stderr.bin",
    )
    candidate = evaluate_reconciliation(plan, (record,), repo_root=tmp_path)
    assert candidate.status == "BLOCKED"
    assert any("raw_evidence_missing" in r for r in candidate.blocking_reasons)


def test_evaluate_reconciliation_blocks_on_bootstrap_after_expiry() -> None:
    """A bootstrap record after expiry must block the candidate (F4)."""

    from reverse_agent.control_plane.models import BootstrapState

    plan = _plan_with_commands(_command())
    record = ExecutionRecord(
        command_id="status.git_status",
        command="git status --short",
        execution_surface="local",
        operations=("repository_observation",),
        mutated_paths=(),
        exit_code=0,
        started_at="2026-07-21T08:00:00Z",
        observed_at="2026-07-21T10:00:01Z",
        head_before="a" * 40,
        head_after="a" * 40,
        stdout_digest="sha256:" + "0" * 64,
        stderr_digest="sha256:" + "0" * 64,
        authority_origin="bootstrap_exception",
    )
    bootstrap = BootstrapState(
        status="BOOTSTRAP_EXPIRED",
        expired_at="2026-07-21T09:00:00Z",
    )
    candidate = evaluate_reconciliation(
        plan, (record,), bootstrap_state=bootstrap
    )
    assert candidate.status == "BLOCKED"
    assert any("bootstrap_authority_after_expiry" in r for r in candidate.blocking_reasons)


def test_evaluate_reconciliation_blocks_on_digest_mismatch_with_raw_evidence(
    tmp_path: Path,
) -> None:
    """A record whose digest doesn't match the raw evidence must block (F3)."""

    evidence_dir = tmp_path / "evidence" / "rec1"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "stdout.bin").write_bytes(b"real output")
    (evidence_dir / "stderr.bin").write_bytes(b"")

    plan = _plan_with_commands(_command())
    record = ExecutionRecord(
        command_id="status.git_status",
        command="git status --short",
        execution_surface="local",
        operations=("repository_observation",),
        mutated_paths=(),
        exit_code=0,
        started_at="2026-07-21T08:00:00Z",
        observed_at="2026-07-21T10:00:01Z",
        head_before="a" * 40,
        head_after="a" * 40,
        stdout_digest="sha256:" + "0" * 64,  # doesn't match "real output"
        stderr_digest="sha256:" + "0" * 64,  # doesn't match ""
        authority_origin="normal_plan",
        raw_stdout_path="evidence/rec1/stdout.bin",
        raw_stderr_path="evidence/rec1/stderr.bin",
    )
    candidate = evaluate_reconciliation(plan, (record,), repo_root=tmp_path)
    assert candidate.status == "BLOCKED"
    assert any("digest_mismatch" in r for r in candidate.blocking_reasons)


def test_evaluate_reconciliation_blocks_on_generated_at_before_records() -> None:
    """generated_at must be >= max(observed_at) (F3)."""

    plan = _plan_with_commands(_command())
    record = _authentic_record()
    candidate = evaluate_reconciliation(
        plan, (record,),
        log_generated_at="2026-07-21T07:00:00Z",  # before observed_at
    )
    assert candidate.status == "BLOCKED"
    assert any("generated_at_before_records" in r for r in candidate.blocking_reasons)


def test_report_subject_binding_captures_required_fields(tmp_path: Path) -> None:
    """ReportSubjectBinding captures all Phase F binding fields."""

    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    binding = build_report_subject_binding(
        repo_root=tmp_path,
        activation_base_sha="e" * 40,
        subject_paths=("a.py",),
        diff_text="diff --git a/a.py b/a.py\n+print('a')\n",
        observed_worktree_paths=("a.py",),
        local_seal_digest="s" * 64,
    )

    assert isinstance(binding, ReportSubjectBinding)
    assert binding.activation_base_sha == "e" * 40
    assert len(binding.subject_tree_digest) == 64
    assert len(binding.subject_diff_digest) == 64
    assert binding.observed_worktree_paths == ("a.py",)
    assert binding.local_seal_digest == "s" * 64


def test_report_subject_binding_does_not_claim_remote_head(tmp_path: Path) -> None:
    """The binding must not expose a 'final_head' or 'remote_head' field."""

    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    binding = build_report_subject_binding(
        repo_root=tmp_path,
        activation_base_sha="e" * 40,
        subject_paths=("a.py",),
        diff_text="",
        observed_worktree_paths=(),
        local_seal_digest="",
    )

    payload = binding.to_dict()
    assert "final_head" not in payload
    assert "remote_head" not in payload
    assert "final_commit" not in payload
    assert "activation_base_sha" in payload
    assert "subject_tree_digest" in payload
    assert "subject_diff_digest" in payload
    assert "observed_worktree_paths" in payload
    assert "local_seal_digest" in payload


def test_report_subject_binding_is_deterministic(tmp_path: Path) -> None:
    """Same inputs produce the same binding digests."""

    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    binding1 = build_report_subject_binding(
        repo_root=tmp_path,
        activation_base_sha="e" * 40,
        subject_paths=("a.py",),
        diff_text="diff",
        observed_worktree_paths=("a.py",),
        local_seal_digest="s" * 64,
    )
    binding2 = build_report_subject_binding(
        repo_root=tmp_path,
        activation_base_sha="e" * 40,
        subject_paths=("a.py",),
        diff_text="diff",
        observed_worktree_paths=("a.py",),
        local_seal_digest="s" * 64,
    )

    assert binding1.subject_tree_digest == binding2.subject_tree_digest
    assert binding1.subject_diff_digest == binding2.subject_diff_digest


def test_report_subject_binding_observed_paths_sorted(tmp_path: Path) -> None:
    """observed_worktree_paths are sorted in the binding."""

    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    binding = build_report_subject_binding(
        repo_root=tmp_path,
        activation_base_sha="e" * 40,
        subject_paths=("a.py",),
        diff_text="",
        observed_worktree_paths=("z.py", "a.py", "m.py"),
        local_seal_digest="",
    )

    assert binding.observed_worktree_paths == ("a.py", "m.py", "z.py")
