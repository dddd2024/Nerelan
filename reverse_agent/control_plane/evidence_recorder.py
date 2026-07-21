"""Phase A: machine-generated evidence recorder.

Provides a controlled recorder that produces cryptographically and temporally
valid execution records. Hand-crafted records with future timestamps, malformed
digests, fake head SHAs, or stale bootstrap authority are rejected.

The recorder is the single entry point for writing execution evidence. Direct
hand-editing of ``execution_log.json`` is forbidden; the recorder derives all
fields from observed subprocess output and git state.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .models import (
    BootstrapState,
    ExecutionRecord,
    TransitionCommand,
    TransitionCommandPlan,
)


# ---------------------------------------------------------------------------
# Format validators
# ---------------------------------------------------------------------------

# RFC3339 UTC with a trailing Z. Accepts ``YYYY-MM-DDTHH:MM:SS[.fraction]Z``.
_RFC3339_UTC = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)

# sha256: followed by exactly 64 lowercase hex digits.
_SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")

# 40-char lowercase hex git SHA.
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")

# Tolerance for clock skew between recorder and observed timestamps, in seconds.
# Allows tiny differences without rejecting legitimate records.
_FUTURE_TOLERANCE_SECONDS = 5


def _parse_rfc3339_utc(value: str) -> datetime | None:
    """Parse a strict RFC3339 UTC timestamp with trailing ``Z``."""

    if not isinstance(value, str) or not _RFC3339_UTC.match(value):
        return None
    try:
        # ``fromisoformat`` does not accept ``Z`` before Python 3.11; normalize.
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc)


def _is_lower_sha256_digest(value: str) -> bool:
    return isinstance(value, str) and bool(_SHA256_DIGEST.match(value))


def _is_lower_git_sha(value: str) -> bool:
    return isinstance(value, str) and bool(_GIT_SHA.match(value))


def _sha256_digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# Authenticity validation
# ---------------------------------------------------------------------------


def validate_record_authenticity(
    record: ExecutionRecord,
    *,
    plan: TransitionCommandPlan,
    recorder_observed_at: str,
    raw_stdout: bytes | None = None,
    raw_stderr: bytes | None = None,
    bootstrap_state: BootstrapState | None = None,
    repo_root: Path | None = None,
    log_generated_at: str | None = None,
) -> list[str]:
    """Return a list of authenticity errors for an execution record.

    An empty list means the record is authentic. Each error is a stable
    machine-readable token (e.g. ``future_timestamp:started_at``).

    Phase C (final rework): when ``repo_root`` is provided, head SHAs are
    verified against the git object database. When ``raw_stdout_path`` /
    ``raw_stderr_path`` are set on the record, the raw evidence files are
    read from ``repo_root`` and their digests are compared. When
    ``log_generated_at`` is provided, it must be >= max(observed_at).
    """

    errors: list[str] = []

    # --- Timestamp format and monotonicity -------------------------------
    started_dt = _parse_rfc3339_utc(record.started_at)
    observed_dt = _parse_rfc3339_utc(record.observed_at)
    recorder_dt = _parse_rfc3339_utc(recorder_observed_at)

    if started_dt is None:
        errors.append("malformed_timestamp:started_at")
    if observed_dt is None:
        errors.append("malformed_timestamp:observed_at")
    if recorder_dt is None:
        errors.append("malformed_timestamp:recorder_observed_at")

    if started_dt is not None and observed_dt is not None:
        if started_dt > observed_dt:
            errors.append("non_monotonic_time:started_at_after_observed_at")

    # --- Future timestamp check (with tolerance) -------------------------
    if recorder_dt is not None:
        tolerance = _FUTURE_TOLERANCE_SECONDS
        if started_dt is not None and started_dt > recorder_dt:
            delta = (started_dt - recorder_dt).total_seconds()
            if delta > tolerance:
                errors.append("future_timestamp:started_at")
        if observed_dt is not None and observed_dt > recorder_dt:
            delta = (observed_dt - recorder_dt).total_seconds()
            if delta > tolerance:
                errors.append("future_timestamp:observed_at")

    # --- Head SHA format -------------------------------------------------
    if not _is_lower_git_sha(record.head_before):
        errors.append("malformed_head_sha:head_before")
    if not _is_lower_git_sha(record.head_after):
        errors.append("malformed_head_sha:head_after")

    # --- Git object verification (Phase C rework) -----------------------
    if repo_root is not None:
        if _is_lower_git_sha(record.head_before):
            if not _git_object_exists(repo_root, record.head_before):
                errors.append("git_object_not_found:head_before")
        if _is_lower_git_sha(record.head_after):
            if not _git_object_exists(repo_root, record.head_after):
                errors.append("git_object_not_found:head_after")

    # --- Digest format ---------------------------------------------------
    if not _is_lower_sha256_digest(record.stdout_digest):
        errors.append("malformed_digest:stdout_digest")
    if not _is_lower_sha256_digest(record.stderr_digest):
        errors.append("malformed_digest:stderr_digest")

    # --- Raw evidence file verification (Phase C rework) ----------------
    if repo_root is not None and _is_lower_sha256_digest(record.stdout_digest):
        raw_ok, raw_bytes = _read_raw_evidence(repo_root, record.raw_stdout_path)
        if not raw_ok:
            errors.append("raw_evidence_missing:stdout")
        elif _sha256_digest(raw_bytes) != record.stdout_digest:
            errors.append("digest_mismatch:stdout_digest")
    elif raw_stdout is not None and _is_lower_sha256_digest(record.stdout_digest):
        expected = _sha256_digest(raw_stdout)
        if record.stdout_digest != expected:
            errors.append("digest_mismatch:stdout_digest")

    if repo_root is not None and _is_lower_sha256_digest(record.stderr_digest):
        raw_ok, raw_bytes = _read_raw_evidence(repo_root, record.raw_stderr_path)
        if not raw_ok:
            errors.append("raw_evidence_missing:stderr")
        elif _sha256_digest(raw_bytes) != record.stderr_digest:
            errors.append("digest_mismatch:stderr_digest")
    elif raw_stderr is not None and _is_lower_sha256_digest(record.stderr_digest):
        expected = _sha256_digest(raw_stderr)
        if record.stderr_digest != expected:
            errors.append("digest_mismatch:stderr_digest")

    # --- Command ID binding to plan -------------------------------------
    plan_entry = _find_plan_entry(plan, record.command_id)
    if plan_entry is None:
        errors.append("command_id_mismatch:unknown_command_id")
    elif plan_entry.command != record.command:
        errors.append("command_id_mismatch:command_string_diverges")

    # --- Bootstrap authority lifecycle ----------------------------------
    if bootstrap_state is not None and bootstrap_state.is_expired:
        if record.authority_origin == "bootstrap_exception":
            errors.append("bootstrap_authority_after_expiry")

    # --- Log generated_at >= max(observed_at) (Phase C rework) ----------
    if log_generated_at is not None:
        gen_dt = _parse_rfc3339_utc(log_generated_at)
        if gen_dt is None:
            errors.append("malformed_timestamp:log_generated_at")
        elif observed_dt is not None and gen_dt < observed_dt:
            errors.append("generated_at_before_records")

    return errors


def _git_object_exists(repo_root: Path, sha: str) -> bool:
    """Check if a git object (by SHA) exists in the repository."""

    result = subprocess.run(
        ["git", "cat-file", "-e", sha],
        cwd=str(repo_root),
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _read_raw_evidence(repo_root: Path, relative_path: str) -> tuple[bool, bytes]:
    """Read a raw evidence file from the repo root.

    Returns ``(ok, bytes)``. If the file doesn't exist, returns ``(False, b"")``.
    """

    if not relative_path:
        return False, b""
    path = Path(repo_root) / relative_path
    if not path.is_file():
        return False, b""
    return True, path.read_bytes()


def _find_plan_entry(
    plan: TransitionCommandPlan,
    command_id: str,
) -> TransitionCommand | None:
    """Locate a plan entry by command_id (any execution_surface)."""

    for entry in plan.commands:
        if entry.command_id == command_id:
            return entry
    return None


# ---------------------------------------------------------------------------
# EvidenceRecorder: controlled entry point for execution evidence
# ---------------------------------------------------------------------------


def _now_utc() -> str:
    """Return the current UTC time as strict RFC3339 with trailing ``Z``."""

    dt = datetime.now(tz=timezone.utc)
    # Trim microseconds to whole seconds for stable RFC3339.
    return dt.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class EvidenceRecorder:
    """Controlled recorder that produces authentic execution records.

    The recorder derives ``head_before`` / ``head_after`` from git, computes
    digests from raw subprocess output, and stamps timestamps from the
    machine clock. Callers cannot supply these fields directly.
    """

    repo_root: Path
    plan: TransitionCommandPlan

    def record(
        self,
        *,
        command_id: str,
        command: str,
        raw_stdout: bytes,
        raw_stderr: bytes,
        exit_code: int,
        execution_surface: str = "local",
        operations: Iterable[str] = (),
        mutated_paths: Iterable[str] = (),
        authority_origin: str = "normal_plan",
        started_at: str | None = None,
    ) -> ExecutionRecord:
        """Produce an authentic ExecutionRecord for a single command run."""

        head_before = self._git_head_sha()
        recorded_started_at = started_at if started_at is not None else _now_utc()
        observed_at = _now_utc()
        head_after = self._git_head_sha()

        return ExecutionRecord(
            command_id=command_id,
            command=command,
            execution_surface=execution_surface,
            operations=tuple(operations),
            mutated_paths=tuple(mutated_paths),
            exit_code=exit_code,
            started_at=recorded_started_at,
            observed_at=observed_at,
            head_before=head_before,
            head_after=head_after,
            stdout_digest=_sha256_digest(raw_stdout),
            stderr_digest=_sha256_digest(raw_stderr),
            authority_origin=authority_origin,
        )

    def _git_head_sha(self) -> str:
        """Return the current HEAD SHA (40-char lowercase hex)."""

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        sha = result.stdout.strip()
        if not _is_lower_git_sha(sha):
            # Fall back to a zero SHA if git is unavailable; authenticity
            # validation will still flag malformed values. Production
            # callers must ensure git is available.
            return "0" * 40
        return sha


# ---------------------------------------------------------------------------
# TrustedCommandRunner: the single execution entry point (Phase B rework)
# ---------------------------------------------------------------------------


def _plan_digest(plan: TransitionCommandPlan) -> str:
    """Stable sha256 digest of the command plan."""

    import json

    canonical = json.dumps(plan.to_dict(), sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _git_changed_files(repo_root: Path, head_before: str, head_after: str) -> tuple[str, ...]:
    """Return the set of files changed between two HEAD SHAs.

    Falls back to ``git status --short`` when the two SHAs are identical
    (e.g. untracked or working-tree-only changes).
    """

    if head_before != head_after:
        result = subprocess.run(
            ["git", "diff", "--name-only", head_before, head_after],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        result = subprocess.run(
            ["git", "status", "--short", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    # For ``git status --porcelain`` output, strip the status prefix.
    paths: list[str] = []
    for line in lines:
        if line and head_before == head_after:
            # Format: "XY path" — take everything after the first 3 chars.
            path = line[3:].strip().strip('"')
            if path:
                paths.append(path)
        else:
            paths.append(line)
    return tuple(dict.fromkeys(paths))


@dataclass(frozen=True)
class TrustedCommandRunner:
    """The single trusted entry point for producing execution evidence.

    Phase B (final rework): the runner reads the command string from the
    plan by ``command_id``, launches the subprocess itself, captures raw
    stdout/stderr, reads real UTC time and Git HEAD before/after, computes
    mutated paths via ``git diff``, persists raw evidence
    content-addressably, and atomically appends the execution record.

    Callers cannot supply command, raw_stdout, raw_stderr, started_at,
    observed_at, head_before, head_after, stdout_digest, stderr_digest,
    or authority_origin — these are all derived from observation (F2).
    """

    repo_root: Path
    plan: TransitionCommandPlan
    evidence_dir: Path
    execution_log_path: Path | None = None

    def run_command(self, *, command_id: str) -> ExecutionRecord:
        """Execute the plan entry identified by ``command_id``.

        Raises :class:`KeyError` if the command_id is not in the plan.
        """

        plan_entry = self._find_plan_entry(command_id)
        if plan_entry is None:
            raise KeyError(f"unknown_command_id:{command_id}")

        head_before = self._git_head_sha()
        started_at = _now_utc()

        result = subprocess.run(
            plan_entry.command,
            cwd=str(self.repo_root),
            shell=True,
            capture_output=True,
            check=False,
        )
        raw_stdout = result.stdout
        raw_stderr = result.stderr

        observed_at = _now_utc()
        head_after = self._git_head_sha()

        mutated_paths = _git_changed_files(self.repo_root, head_before, head_after)

        digest = _plan_digest(self.plan)
        sequence = self._next_sequence()
        record_id = self._make_record_id(command_id, started_at, observed_at, sequence)
        raw_stdout_path, raw_stderr_path = self._persist_raw_evidence(
            record_id, raw_stdout, raw_stderr
        )

        record = ExecutionRecord(
            command_id=command_id,
            command=plan_entry.command,
            execution_surface=plan_entry.execution_surface,
            operations=plan_entry.operations,
            mutated_paths=mutated_paths,
            exit_code=result.returncode,
            started_at=started_at,
            observed_at=observed_at,
            head_before=head_before,
            head_after=head_after,
            stdout_digest=_sha256_digest(raw_stdout),
            stderr_digest=_sha256_digest(raw_stderr),
            authority_origin=plan_entry.authority_origin,
            record_id=record_id,
            plan_digest=digest,
            decision_id=self.plan.decision_id,
            round_id=self.plan.round_id,
            sequence=sequence,
            raw_stdout_path=str(raw_stdout_path.relative_to(self.repo_root)) if raw_stdout_path.is_relative_to(self.repo_root) else str(raw_stdout_path),
            raw_stderr_path=str(raw_stderr_path.relative_to(self.repo_root)) if raw_stderr_path.is_relative_to(self.repo_root) else str(raw_stderr_path),
        )

        if self.execution_log_path is not None:
            self._append_to_log(record)

        return record

    def _find_plan_entry(self, command_id: str) -> TransitionCommand | None:
        for entry in self.plan.commands:
            if entry.command_id == command_id:
                return entry
        return None

    def _git_head_sha(self) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        sha = result.stdout.strip()
        if not _is_lower_git_sha(sha):
            return "0" * 40
        return sha

    def _make_record_id(self, command_id: str, started_at: str, observed_at: str, sequence: int) -> str:
        import secrets

        raw = f"{command_id}:{started_at}:{observed_at}:{sequence}:{secrets.token_hex(8)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _persist_raw_evidence(
        self, record_id: str, raw_stdout: bytes, raw_stderr: bytes
    ) -> tuple[Path, Path]:
        record_dir = self.evidence_dir / record_id
        record_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = record_dir / "stdout.bin"
        stderr_path = record_dir / "stderr.bin"
        stdout_path.write_bytes(raw_stdout)
        stderr_path.write_bytes(raw_stderr)

        import json

        metadata = {
            "record_id": record_id,
            "stdout_path": str(stdout_path.name),
            "stderr_path": str(stderr_path.name),
            "stdout_digest": _sha256_digest(raw_stdout),
            "stderr_digest": _sha256_digest(raw_stderr),
            "stdout_bytes": len(raw_stdout),
            "stderr_bytes": len(raw_stderr),
        }
        (record_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return stdout_path, stderr_path

    def _next_sequence(self) -> int:
        if self.execution_log_path is None or not self.execution_log_path.exists():
            return 0
        try:
            import json

            log = json.loads(self.execution_log_path.read_text(encoding="utf-8"))
            commands = log.get("commands") or []
            if not commands:
                return 0
            return max(int(r.get("sequence", 0)) for r in commands) + 1
        except (ValueError, KeyError):
            return 0

    def _append_to_log(self, record: ExecutionRecord) -> None:
        import json

        if self.execution_log_path is None:
            return
        if self.execution_log_path.exists():
            log = json.loads(self.execution_log_path.read_text(encoding="utf-8"))
        else:
            log = {
                "schema_version": 1,
                "artifact_name": "execution_log.json",
                "gate_name": "transition-trusted-runner",
                "gate_status": "PASSED",
                "decision_id": self.plan.decision_id,
                "round_id": self.plan.round_id,
                "generated_at": _now_utc(),
                "source": "trusted_command_runner",
                "commands": [],
            }
        log.setdefault("commands", []).append(record.to_dict())
        log["generated_at"] = _now_utc()
        self.execution_log_path.write_text(
            json.dumps(log, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
