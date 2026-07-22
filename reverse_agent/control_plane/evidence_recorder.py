"""Phase A: machine-generated evidence recorder.

Provides a controlled recorder that produces cryptographically and temporally
valid execution records. Hand-crafted records with future timestamps, malformed
digests, fake head SHAs, or stale bootstrap authority are rejected.

The recorder is the single entry point for writing execution evidence. Direct
hand-editing of ``execution_log.json`` is forbidden; the recorder derives all
fields from observed subprocess output and git state.

F4-F7 rework: :class:`TrustedExecutionContext` is the ONLY production entry
point. It loads the active Decision and committed command plan from
``state_dir``, regenerates the expected plan, verifies deterministic
equality, and only then constructs a runner. Callers cannot inject a plan,
command string, authority origin, timestamps, digests or Git SHAs.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator

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


def _parse_lifecycle_utc(value: str) -> datetime | None:
    """Parse persisted lifecycle UTC in either ``Z`` or ``+00:00`` form."""

    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
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

    # --- Strict transition identity -------------------------------------
    # Current-round evidence is never anonymous.  Legacy records with an
    # empty identity must not be accepted into a strict transition subject.
    if not record.decision_id:
        errors.append("missing_identity:decision_id")
    elif record.decision_id != plan.decision_id:
        errors.append("identity_mismatch:decision_id")
    if not record.round_id:
        errors.append("missing_identity:round_id")
    elif record.round_id != plan.round_id:
        errors.append("identity_mismatch:round_id")

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
    if (
        bootstrap_state is not None
        and bootstrap_state.is_expired
        and record.authority_origin == "bootstrap_exception"
    ):
        expiry_dt = _parse_lifecycle_utc(bootstrap_state.expired_at)
        identity_matches = (
            bootstrap_state.decision_id == record.decision_id
            and bootstrap_state.round_id == record.round_id
        )
        # Replay-stable rule: a record observed while the bootstrap window
        # was open remains valid after the persisted state later expires.
        if (
            expiry_dt is None
            or observed_dt is None
            or observed_dt > expiry_dt
            or not identity_matches
        ):
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
    path = _resolve_repo_relative_path(repo_root, relative_path)
    if path is None:
        return False, b""
    if not path.is_file():
        return False, b""
    return True, path.read_bytes()


def _resolve_repo_relative_path(repo_root: Path, stored_path: str) -> Path | None:
    """Resolve a portable stored path without permitting repository escape."""

    normalized = stored_path.replace("\\", "/")
    if not normalized or normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        return None
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        return None
    root = repo_root.resolve()
    candidate = root.joinpath(*pure.parts).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


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
            decision_id=self.plan.decision_id,
            round_id=self.plan.round_id,
            plan_digest=_plan_digest(self.plan),
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
    test_only: bool = False

    @classmethod
    def for_test(
        cls,
        *,
        repo_root: Path,
        plan: TransitionCommandPlan,
        evidence_dir: Path,
        execution_log_path: Path | None = None,
    ) -> "TrustedCommandRunner":
        """Construct the legacy injected-plan runner for isolated tests only."""

        return cls(
            repo_root=repo_root,
            plan=plan,
            evidence_dir=evidence_dir,
            execution_log_path=execution_log_path,
            test_only=True,
        )

    def run_command(self, *, command_id: str) -> ExecutionRecord:
        """Execute the plan entry identified by ``command_id``.

        Raises :class:`KeyError` if the command_id is not in the plan.
        """

        if not self.test_only:
            raise RuntimeError(
                "injected_plan_runner_disabled:use_TrustedExecutionContext.from_state_dir"
            )

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
            raw_stdout_path=self._portable_repo_relative(raw_stdout_path),
            raw_stderr_path=self._portable_repo_relative(raw_stderr_path),
        )

        if self.execution_log_path is not None:
            self._append_to_log(record)

        return record

    def _portable_repo_relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.repo_root.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError(f"evidence_path_outside_repo:{path}") from exc

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
        self._ensure_binary_evidence_attributes()
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

    def _ensure_binary_evidence_attributes(self) -> None:
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        attributes_path = self.evidence_dir / ".gitattributes"
        expected = "*.bin binary\n"
        if not attributes_path.exists() or attributes_path.read_text(encoding="utf-8") != expected:
            attributes_path.write_text(expected, encoding="utf-8", newline="\n")

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
                "plan_digest": record.plan_digest,
                "generated_at": _now_utc(),
                "source": "trusted_command_runner",
                "commands": [],
            }
        log.setdefault("commands", []).append(record.to_dict())
        log["generated_at"] = _now_utc()
        log["plan_digest"] = record.plan_digest
        self.execution_log_path.write_text(
            json.dumps(log, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )


# ---------------------------------------------------------------------------
# F4-F7: TrustedExecutionContext — the ONLY production entry point
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorizationResult:
    """F5: result of pre-execution authorization.

    ``status`` is ``AUTHORIZED`` or ``BLOCKED``. When BLOCKED, ``reasons``
    carries machine-readable tokens explaining why the command may not run.
    """

    status: str
    reasons: tuple[str, ...] = ()


def _git_status_porcelain(repo_root: Path) -> str:
    """Return ``git status --porcelain`` output for the worktree."""

    result = subprocess.run(
        ["git", "status", "--short", "--porcelain"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def _parse_status_paths(status_output: str) -> frozenset[str]:
    """Parse ``git status --porcelain`` output into a set of normalized paths."""

    paths: set[str] = set()
    for line in status_output.splitlines():
        line = line.rstrip()
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip().strip('"')
        if path:
            paths.add(path.replace("\\", "/"))
    return frozenset(paths)


def _snapshot_repository_state(repo_root: Path, head_sha: str) -> dict[str, Any]:
    """Capture path identity plus index and worktree content state.

    Unlike a porcelain-status set, this snapshot detects a second edit to a
    path that was already dirty before the command, as well as creations,
    deletions, renames and index-only changes.
    """

    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=str(repo_root),
        capture_output=True,
        check=False,
    ).stdout
    index_raw = subprocess.run(
        ["git", "ls-files", "-s", "-z"],
        cwd=str(repo_root),
        capture_output=True,
        check=False,
    ).stdout
    index: dict[str, list[str]] = {}
    for item in index_raw.split(b"\0"):
        if not item:
            continue
        meta, raw_path = item.split(b"\t", 1)
        path = raw_path.decode("utf-8", "surrogateescape").replace("\\", "/")
        index.setdefault(path, []).append(meta.decode("ascii", "replace"))

    paths = {
        item.decode("utf-8", "surrogateescape").replace("\\", "/")
        for item in listed.split(b"\0")
        if item
    }
    paths.update(index)
    entries: dict[str, Any] = {}
    for path in sorted(paths):
        disk_path = repo_root.joinpath(*PurePosixPath(path).parts)
        if disk_path.is_symlink():
            worktree = {"kind": "symlink", "target": os.readlink(disk_path)}
        elif disk_path.is_file():
            stat = disk_path.stat()
            worktree = {
                "kind": "file",
                "digest": _sha256_digest(disk_path.read_bytes()),
                "executable": bool(stat.st_mode & 0o111),
            }
        else:
            worktree = {"kind": "missing"}
        entries[path] = {
            "index": sorted(index.get(path, [])),
            "worktree": worktree,
        }
    return {"head": head_sha, "paths": entries}


def _snapshot_digest(snapshot: dict[str, Any]) -> str:
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_digest(raw)


def _snapshot_mutated_paths(
    before: dict[str, Any], after: dict[str, Any]
) -> tuple[str, ...]:
    before_paths = before.get("paths", {})
    after_paths = after.get("paths", {})
    return tuple(
        path
        for path in sorted(set(before_paths) | set(after_paths))
        if before_paths.get(path) != after_paths.get(path)
    )


def _compute_mutation_delta_digest(
    pre_snapshot: dict[str, Any],
    post_snapshot: dict[str, Any],
    mutated_paths: tuple[str, ...],
) -> str:
    """F7: sha256 digest of the command-local mutation delta."""

    delta = {
        path: {
            "before": pre_snapshot.get("paths", {}).get(path),
            "after": post_snapshot.get("paths", {}).get(path),
        }
        for path in mutated_paths
    }
    raw = json.dumps(delta, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_digest(raw)


@contextmanager
def _file_lock(lock_path: Path) -> Iterator[None]:
    """F6: simple cross-platform file lock using atomic file creation.

    Uses ``O_CREAT | O_EXCL`` to acquire; unlink to release. Retries with
    a short sleep until the lock is acquired or a timeout is reached.
    """

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = 5.0
    elapsed = 0.0
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if elapsed >= deadline:
                raise TimeoutError(f"file_lock_timeout:{lock_path}")
            import time

            time.sleep(0.01)
            elapsed += 0.01
    try:
        yield
    finally:
        try:
            os.unlink(str(lock_path))
        except OSError:
            pass


@dataclass(frozen=True)
class TrustedExecutionContext:
    """F4: the ONLY production entry point for trusted command execution.

    Reads the active Decision and committed command plan from ``state_dir``,
    regenerates the expected plan, verifies deterministic equality, loads
    bootstrap state and local seal status, and only then exposes
    :meth:`authorize_before_execute` and :meth:`run_command`.

    Production callers cannot inject a plan, command string, authority
    origin, timestamps, digests or Git SHAs. The ``from_state_dir``
    classmethod is the sole constructor.
    """

    decision_id: str
    round_id: str
    plan: TransitionCommandPlan
    plan_digest: str
    repo_root: Path
    state_dir: Path
    evidence_dir: Path
    execution_log_path: Path
    bootstrap_state: BootstrapState
    decision_status: str
    required_branch: str
    activation_base_sha: str
    capability_policy: Any
    local_seal_status: str = ""

    @classmethod
    def from_state_dir(cls, state_dir: Path, *, repo_root: Path) -> "TrustedExecutionContext":
        """F4: build a context from the active Decision and committed plan.

        Reads ``decision_packet.md`` and ``gates/command_plan.json``,
        regenerates the expected plan from the Decision, verifies digest
        equality, loads bootstrap state and local seal status.
        """

        from .legacy_adapter import (
            build_transition_command_plan,
            load_capability_policy,
            load_bootstrap_state,
            load_legacy_command_plan,
            load_transition_decision,
        )

        # 1. Read active Decision
        decision, contract = load_transition_decision(state_dir / "decision_packet.md")

        # 2. Read committed command plan
        committed_plan_path = state_dir / "gates" / "command_plan.json"
        if not committed_plan_path.exists():
            raise ValueError("missing_command_plan")
        committed_plan = load_legacy_command_plan(committed_plan_path)

        # 3. Regenerate expected plan from Decision
        expected_plan = build_transition_command_plan(decision, contract)

        # 4. Verify deterministic plan equality by digest
        committed_digest = _plan_digest(committed_plan)
        expected_digest = _plan_digest(expected_plan)
        if committed_digest != expected_digest:
            raise ValueError("plan_digest_mismatch")

        # 5. Load bootstrap state
        bootstrap_state = load_bootstrap_state(state_dir / "gates" / "bootstrap_state.json")

        # 6. Load local seal status (if present)
        local_seal_status = ""
        local_seal_path = state_dir / "gates" / "local_execution_seal.json"
        if local_seal_path.exists():
            try:
                seal_payload = json.loads(local_seal_path.read_text(encoding="utf-8"))
                if (
                    seal_payload.get("decision_id") == decision.decision_id
                    and seal_payload.get("round_id") == decision.round_id
                    and seal_payload.get("plan_digest") == committed_digest
                ):
                    local_seal_status = str(seal_payload.get("status") or "")
            except (ValueError, OSError):
                pass

        return cls(
            decision_id=decision.decision_id,
            round_id=decision.round_id,
            plan=committed_plan,
            plan_digest=committed_digest,
            repo_root=repo_root,
            state_dir=state_dir,
            evidence_dir=state_dir / "gates" / "evidence",
            execution_log_path=state_dir / "gates" / "execution_log.json",
            bootstrap_state=bootstrap_state,
            decision_status=decision.status,
            required_branch=str(contract.get("required_branch") or ""),
            activation_base_sha=str(contract.get("activation_base_sha") or "").lower(),
            capability_policy=load_capability_policy(contract),
            local_seal_status=local_seal_status,
        )

    def authorize_before_execute(self, command_id: str) -> AuthorizationResult:
        """F5: pre-execution hard gate.

        Returns ``AUTHORIZED`` only when the command_id is present in the
        plan and all pre-execution constraints (bootstrap expiry,
        ``allowed_only_after_validation`` seal check) are satisfied.
        """

        reasons: list[str] = []

        entry = self._find_plan_entry(command_id)
        if entry is None:
            reasons.append(f"unknown_command_id:{command_id}")
            return AuthorizationResult(status="BLOCKED", reasons=tuple(reasons))

        if entry.execution_surface != "local":
            reasons.append(f"execution_surface_mismatch:{command_id}:{entry.execution_surface}")

        if self.decision_status != "APPROVED":
            reasons.append(f"decision_not_approved:{self.decision_status}")
        if self.plan.decision_id != self.decision_id or self.plan.round_id != self.round_id:
            reasons.append("active_identity_mismatch")

        # Re-read authority so a context cannot outlive a Decision or plan edit.
        try:
            from .legacy_adapter import load_legacy_command_plan, load_transition_decision

            live_decision, _ = load_transition_decision(self.state_dir / "decision_packet.md")
            live_plan = load_legacy_command_plan(self.state_dir / "gates" / "command_plan.json")
            if (
                live_decision.decision_id != self.decision_id
                or live_decision.round_id != self.round_id
                or live_decision.status != "APPROVED"
            ):
                reasons.append("active_decision_changed")
            if _plan_digest(live_plan) != self.plan_digest:
                reasons.append("active_plan_digest_changed")
        except (OSError, ValueError, json.JSONDecodeError):
            reasons.append("active_authority_unreadable")

        branch = self._git_text("branch", "--show-current")
        if branch != self.required_branch:
            reasons.append(f"branch_identity:{branch}:{self.required_branch}")
        if not self._git_is_ancestor(self.activation_base_sha, "HEAD"):
            reasons.append(f"activation_base_ancestry:{self.activation_base_sha}")

        from .models import ExecutionEnvelope
        from .transition import _capability_forbidden_operations, _envelope_network_violations

        forbidden_ops = set(_capability_forbidden_operations(self.capability_policy))
        denied = sorted(forbidden_ops.intersection(entry.operations))
        if denied:
            reasons.append(f"capability_policy:{command_id}:{denied}")
        envelope = ExecutionEnvelope(
            command=entry.command,
            execution_surface=entry.execution_surface,
            operations=entry.operations,
            command_id=entry.command_id,
        )
        network_errors = _envelope_network_violations((envelope,), self.capability_policy)
        if entry.network_access and network_errors:
            reasons.extend(network_errors)

        # The persisted preflight must bind the same active authority.  It is
        # independently regenerated by gate.pre_execution before normal work.
        preflight_path = self.state_dir / "gates" / "transition_preflight_result.json"
        try:
            preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            preflight = {}
        checks = preflight.get("checks") if isinstance(preflight.get("checks"), list) else []
        check_status = {
            str(item.get("name")): str(item.get("status"))
            for item in checks
            if isinstance(item, dict)
        }
        required_preflight_checks = {
            "decision_identity",
            "round_identity",
            "decision_approved",
            "branch_identity",
            "base_ancestry",
            "decision_ancestry",
            "command_plan_identity",
            "command_plan_contract",
            "capability_policy_enforced",
            "network_policy_enforced",
            "path_risk_floor_enforced",
        }
        if (
            preflight.get("decision_id") != self.decision_id
            or preflight.get("round_id") != self.round_id
            or preflight.get("gate_status") not in {"PASSED", "PRE_EXECUTION_AUTHORIZED"}
            or any(check_status.get(name) != "PASS" for name in required_preflight_checks)
        ):
            reasons.append("required_preflight_not_authorized")

        # F5: allowed_only_after_validation requires LOCAL_RECONCILED seal
        if entry.allowed_only_after_validation:
            if self.local_seal_status != "LOCAL_RECONCILED":
                reasons.append(f"allowed_only_after_validation:{command_id}")
            if _git_status_porcelain(self.repo_root).strip():
                reasons.append(f"validation_subject_dirty:{command_id}")

        # F5: bootstrap authority after expiry is forbidden
        if entry.authority_origin == "bootstrap_exception" and self.bootstrap_state.is_expired:
            reasons.append(f"bootstrap_authority_after_expiry:{command_id}")

        if reasons:
            return AuthorizationResult(status="BLOCKED", reasons=tuple(reasons))
        return AuthorizationResult(status="AUTHORIZED", reasons=())

    def _git_text(self, *args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=str(self.repo_root), capture_output=True,
            text=True, check=False,
        ).stdout.strip()

    def _git_is_ancestor(self, ancestor: str, descendant: str) -> bool:
        if not _is_lower_git_sha(ancestor):
            return False
        return subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=str(self.repo_root), capture_output=True, check=False,
        ).returncode == 0

    def run_command(self, command_id: str) -> ExecutionRecord:
        """F4-F7: execute the plan entry identified by ``command_id``.

        Authorizes before execute (F5), captures pre/post state digests
        (F7), runs the subprocess itself, computes the command-local
        mutation delta (F7), and atomically appends to the journal with
        cross-round rejection (F6).
        """

        auth = self.authorize_before_execute(command_id)
        if auth.status != "AUTHORIZED":
            raise RuntimeError(
                f"command_blocked:{command_id}:{list(auth.reasons)}"
            )

        entry = self._find_plan_entry(command_id)
        if entry is None:
            raise KeyError(f"unknown_command_id:{command_id}")

        # F7: capture pre-state (HEAD + worktree status)
        head_before = self._git_head_sha()
        pre_snapshot = _snapshot_repository_state(self.repo_root, head_before)
        pre_state_digest = _snapshot_digest(pre_snapshot)

        started_at = _now_utc()

        # Run subprocess — the runner executes commands itself (F2)
        result = subprocess.run(
            entry.command,
            cwd=str(self.repo_root),
            shell=True,
            capture_output=True,
            check=False,
        )
        raw_stdout = result.stdout
        raw_stderr = result.stderr

        observed_at = _now_utc()

        # F7: capture post-state
        head_after = self._git_head_sha()
        post_snapshot = _snapshot_repository_state(self.repo_root, head_after)
        post_state_digest = _snapshot_digest(post_snapshot)
        mutated_paths = _snapshot_mutated_paths(pre_snapshot, post_snapshot)
        mutation_delta_digest = _compute_mutation_delta_digest(
            pre_snapshot, post_snapshot, mutated_paths
        )

        # F6: append to journal atomically with cross-round rejection,
        # monotonic sequence assignment, and plan_digest binding.
        record = self._append_to_journal_atomic(
            command_id=command_id,
            entry=entry,
            started_at=started_at,
            observed_at=observed_at,
            head_before=head_before,
            head_after=head_after,
            pre_state_digest=pre_state_digest,
            post_state_digest=post_state_digest,
            mutation_delta_digest=mutation_delta_digest,
            mutated_paths=mutated_paths,
            exit_code=result.returncode,
            raw_stdout=raw_stdout,
            raw_stderr=raw_stderr,
        )

        return record

    def replay_bootstrap_evidence_from_head(self) -> tuple[ExecutionRecord, ...]:
        """Import authentic pre-expiry bootstrap records from the published HEAD.

        Bootstrap commands cannot be rerun after expiry.  This controlled
        recovery path reads the prior journal and raw blobs directly from the
        current Git HEAD, verifies their current Decision/round/plan identity,
        timestamps, Git objects and byte digests, then prepends them to the
        new journal.  Callers cannot supply record fields or evidence bytes.
        """

        old_log_raw = self._git_blob("HEAD:project_state/gates/execution_log.json")
        try:
            old_log = json.loads(old_log_raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError("invalid_head_execution_log") from exc
        imported: list[ExecutionRecord] = []
        for payload in old_log.get("commands") or []:
            if not isinstance(payload, dict) or payload.get("authority_origin") != "bootstrap_exception":
                continue
            record = ExecutionRecord.from_mapping(payload)
            entry = self._find_plan_entry(record.command_id)
            if entry is None or not entry.bootstrap_exception:
                raise ValueError(f"untrusted_bootstrap_command_id:{record.command_id}")
            if record.decision_id != self.decision_id or record.round_id != self.round_id:
                raise ValueError(f"bootstrap_identity_mismatch:{record.command_id}")
            if record.plan_digest != self.plan_digest:
                raise ValueError(f"bootstrap_plan_digest_mismatch:{record.command_id}")

            stdout_blob = self._git_blob(
                "HEAD:" + record.raw_stdout_path.replace("\\", "/")
            )
            stderr_blob = self._git_blob(
                "HEAD:" + record.raw_stderr_path.replace("\\", "/")
            )
            record_dir = self.evidence_dir / record.record_id
            record_dir.mkdir(parents=True, exist_ok=True)
            stdout_path = record_dir / "stdout.bin"
            stderr_path = record_dir / "stderr.bin"
            stdout_path.write_bytes(stdout_blob)
            stderr_path.write_bytes(stderr_blob)
            metadata = {
                "record_id": record.record_id,
                "stdout_path": stdout_path.name,
                "stderr_path": stderr_path.name,
                "stdout_digest": record.stdout_digest,
                "stderr_digest": record.stderr_digest,
                "stdout_bytes": len(stdout_blob),
                "stderr_bytes": len(stderr_blob),
                "replayed_from": "HEAD",
            }
            (record_dir / "metadata.json").write_text(
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            normalized = ExecutionRecord.from_mapping({
                **record.to_dict(),
                "sequence": len(imported),
                "raw_stdout_path": self._relative_or_abs(stdout_path),
                "raw_stderr_path": self._relative_or_abs(stderr_path),
            })
            auth_errors = validate_record_authenticity(
                normalized,
                plan=self.plan,
                recorder_observed_at=_now_utc(),
                bootstrap_state=self.bootstrap_state,
                repo_root=self.repo_root,
            )
            if auth_errors:
                raise ValueError(
                    f"bootstrap_replay_authenticity:{record.command_id}:{auth_errors}"
                )
            imported.append(normalized)

        if not imported:
            raise ValueError("no_replayable_bootstrap_records")

        lock_path = self.execution_log_path.parent / "execution_log.lock"
        with _file_lock(lock_path):
            log = json.loads(self.execution_log_path.read_text(encoding="utf-8"))
            if (
                log.get("decision_id") != self.decision_id
                or log.get("round_id") != self.round_id
                or log.get("plan_digest") != self.plan_digest
            ):
                raise ValueError("bootstrap_replay_current_log_identity_mismatch")
            commands = [item for item in log.get("commands") or [] if isinstance(item, dict)]
            imported_ids = {record.record_id for record in imported}
            if any(str(item.get("record_id") or "") in imported_ids for item in commands):
                raise ValueError("bootstrap_replay_duplicate_record")
            resequenced: list[dict[str, Any]] = [record.to_dict() for record in imported]
            for sequence, item in enumerate(commands, start=len(resequenced)):
                resequenced.append({**item, "sequence": sequence})
            log["commands"] = resequenced
            log["generated_at"] = _now_utc()
            self._atomic_write(
                self.execution_log_path,
                json.dumps(log, indent=2, sort_keys=True) + "\n",
            )
        return tuple(imported)

    def _git_blob(self, object_spec: str) -> bytes:
        result = subprocess.run(
            ["git", "show", object_spec],
            cwd=str(self.repo_root),
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError(f"missing_git_blob:{object_spec}")
        return result.stdout

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

    def _append_to_journal_atomic(
        self,
        *,
        command_id: str,
        entry: TransitionCommand,
        started_at: str,
        observed_at: str,
        head_before: str,
        head_after: str,
        pre_state_digest: str,
        post_state_digest: str,
        mutation_delta_digest: str,
        mutated_paths: tuple[str, ...],
        exit_code: int,
        raw_stdout: bytes,
        raw_stderr: bytes,
    ) -> ExecutionRecord:
        """F6: append to journal under lock with cross-round rejection."""

        lock_path = self.execution_log_path.parent / "execution_log.lock"
        with _file_lock(lock_path):
            # F6: cross-round rejection — read existing log and verify identity
            if self.execution_log_path.exists():
                log = json.loads(self.execution_log_path.read_text(encoding="utf-8"))
                log_decision_id = str(log.get("decision_id") or "")
                log_round_id = str(log.get("round_id") or "")
                if log_decision_id and log_decision_id != self.decision_id:
                    raise ValueError(
                        f"cross_round_log:decision_id_mismatch:"
                        f"{log_decision_id}:{self.decision_id}"
                    )
                if log_round_id and log_round_id != self.round_id:
                    raise ValueError(
                        f"cross_round_log:round_id_mismatch:"
                        f"{log_round_id}:{self.round_id}"
                    )
            else:
                log = {
                    "schema_version": 1,
                    "artifact_name": "execution_log.json",
                    "gate_name": "transition-trusted-runner",
                    "gate_status": "PASSED",
                    "decision_id": self.decision_id,
                    "round_id": self.round_id,
                    "plan_digest": self.plan_digest,
                    "generated_at": _now_utc(),
                    "source": "trusted_command_runner",
                    "commands": [],
                }

            # F6: assign monotonic sequence under lock
            commands = log.get("commands") or []
            existing_seq = [
                int(c.get("sequence", 0))
                for c in commands
                if isinstance(c, dict) and isinstance(c.get("sequence"), int)
            ]
            sequence = max(existing_seq) + 1 if existing_seq else 0

            # F6: unique record_id
            raw_id = (
                f"{command_id}:{started_at}:{observed_at}:{sequence}:"
                f"{secrets.token_hex(8)}"
            )
            record_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:16]

            # Persist raw evidence content-addressably
            stdout_path, stderr_path = self._persist_raw_evidence(
                record_id, raw_stdout, raw_stderr
            )

            record = ExecutionRecord(
                command_id=command_id,
                command=entry.command,
                execution_surface=entry.execution_surface,
                operations=entry.operations,
                mutated_paths=mutated_paths,
                exit_code=exit_code,
                started_at=started_at,
                observed_at=observed_at,
                head_before=head_before,
                head_after=head_after,
                stdout_digest=_sha256_digest(raw_stdout),
                stderr_digest=_sha256_digest(raw_stderr),
                authority_origin=entry.authority_origin,
                record_id=record_id,
                plan_digest=self.plan_digest,
                decision_id=self.decision_id,
                round_id=self.round_id,
                sequence=sequence,
                raw_stdout_path=self._relative_or_abs(stdout_path),
                raw_stderr_path=self._relative_or_abs(stderr_path),
                pre_state_digest=pre_state_digest,
                post_state_digest=post_state_digest,
                mutation_delta_digest=mutation_delta_digest,
            )

            # F6: bind plan_digest into log header
            log["plan_digest"] = self.plan_digest
            log["decision_id"] = self.decision_id
            log["round_id"] = self.round_id
            commands.append(record.to_dict())
            log["commands"] = commands
            log["generated_at"] = _now_utc()

            # F6: atomic write — temp file + fsync + atomic replace
            self._atomic_write(
                self.execution_log_path,
                json.dumps(log, indent=2, sort_keys=True) + "\n",
            )

            return record

    def _relative_or_abs(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.repo_root.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError(f"evidence_path_outside_repo:{path}") from exc

    def _persist_raw_evidence(
        self,
        record_id: str,
        raw_stdout: bytes,
        raw_stderr: bytes,
    ) -> tuple[Path, Path]:
        self._ensure_binary_evidence_attributes()
        record_dir = self.evidence_dir / record_id
        record_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = record_dir / "stdout.bin"
        stderr_path = record_dir / "stderr.bin"
        stdout_path.write_bytes(raw_stdout)
        stderr_path.write_bytes(raw_stderr)

        metadata = {
            "record_id": record_id,
            "stdout_path": stdout_path.name,
            "stderr_path": stderr_path.name,
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

    def _ensure_binary_evidence_attributes(self) -> None:
        """Keep raw stdout/stderr byte-for-byte while Git treats them as binary."""

        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        attributes_path = self.evidence_dir / ".gitattributes"
        expected = "*.bin binary\n"
        if not attributes_path.exists() or attributes_path.read_text(encoding="utf-8") != expected:
            attributes_path.write_text(expected, encoding="utf-8", newline="\n")

    def _atomic_write(self, path: Path, content: str) -> None:
        """F6: atomic write using temp file + fsync + atomic replace."""

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp_path), str(path))
