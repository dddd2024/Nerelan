"""Small executor-neutral vertical slice using only the Python standard library."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Mapping, Sequence


_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported canonical JSON type: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Serialize JSON deterministically without insignificant whitespace."""

    return json.dumps(
        _plain(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def sha256_digest(value: Any) -> str:
    """Return the lowercase SHA-256 digest of canonical JSON."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _text(payload: Mapping[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing_or_invalid:{name}")
    return value.strip()


def _string_tuple(payload: Mapping[str, Any], name: str) -> tuple[str, ...]:
    value = payload.get(name)
    if not isinstance(value, list) or not value:
        raise ValueError(f"missing_or_invalid:{name}")
    result = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(result) != len(value) or len(set(result)) != len(result):
        raise ValueError(f"missing_or_invalid:{name}")
    return result


def _validate_relative_pattern(pattern: str) -> None:
    path = PurePosixPath(pattern.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or str(path) in {"", "."}:
        raise ValueError(f"invalid_allowed_path:{pattern}")


@dataclass(frozen=True)
class TaskContract:
    schema_version: str
    task_id: str
    objective: str
    repository_identity: str
    base_commit: str
    allowed_paths: tuple[str, ...]
    required_checks: tuple[str, ...]
    executor_hint: str

    def __post_init__(self) -> None:
        for name in ("schema_version", "task_id", "objective", "repository_identity", "executor_hint"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"missing_or_invalid:{name}")
        if not _SHA40.fullmatch(self.base_commit):
            raise ValueError("missing_or_invalid:base_commit")
        if not self.allowed_paths or not self.required_checks:
            raise ValueError("missing_or_invalid:allowed_paths_or_required_checks")
        if len(set(self.allowed_paths)) != len(self.allowed_paths):
            raise ValueError("duplicate:allowed_paths")
        if len(set(self.required_checks)) != len(self.required_checks):
            raise ValueError("duplicate:required_checks")
        for pattern in self.allowed_paths:
            _validate_relative_pattern(pattern)
        if any(not command.strip() for command in self.required_checks):
            raise ValueError("missing_or_invalid:required_checks")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TaskContract":
        if not isinstance(payload, Mapping):
            raise ValueError("contract_must_be_mapping")
        return cls(
            schema_version=_text(payload, "schema_version"),
            task_id=_text(payload, "task_id"),
            objective=_text(payload, "objective"),
            repository_identity=_text(payload, "repository_identity"),
            base_commit=_text(payload, "base_commit").lower(),
            allowed_paths=_string_tuple(payload, "allowed_paths"),
            required_checks=_string_tuple(payload, "required_checks"),
            executor_hint=_text(payload, "executor_hint"),
        )

    def to_dict(self) -> dict[str, Any]:
        return _plain(asdict(self))

    @property
    def digest(self) -> str:
        return sha256_digest(self)


@dataclass(frozen=True)
class ExecutionEvidence:
    schema_version: str
    task_id: str
    executor: str
    base_commit: str
    observed_head_or_tree: str
    changed_paths: tuple[str, ...]
    git_diff_check: Mapping[str, Any]
    required_check_results: tuple[Mapping[str, Any], ...]
    agent_completion_claim: bool
    started_at: str
    completed_at: str

    def to_dict(self) -> dict[str, Any]:
        return _plain(asdict(self))

    @property
    def digest(self) -> str:
        return sha256_digest(self)


@dataclass(frozen=True)
class AcceptanceResult:
    schema_version: str
    task_id: str
    accepted: bool
    scope_result: str
    required_check_results: tuple[Mapping[str, Any], ...]
    blocking_reasons: tuple[str, ...]
    evidence_digest: str

    def to_dict(self) -> dict[str, Any]:
        return _plain(asdict(self))


@dataclass(frozen=True)
class CapabilityObservation:
    task_class: str
    executor: str
    success: bool
    attempts: int
    elapsed_time: float
    failure_class: str | None

    def to_dict(self) -> dict[str, Any]:
        return _plain(asdict(self))


def export_task_bundle(contract: TaskContract, output_dir: Path | str) -> tuple[Path, Path]:
    """Write deterministic JSON and Markdown task-package files."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "task_contract.json"
    markdown_path = directory / "task.md"
    json_path.write_text(canonical_json(contract) + "\n", encoding="utf-8")
    markdown = "\n".join(
        [
            f"# Task {contract.task_id}",
            "",
            contract.objective,
            "",
            f"- Repository: `{contract.repository_identity}`",
            f"- Base commit: `{contract.base_commit}`",
            f"- Executor hint: `{contract.executor_hint}`",
            f"- Contract SHA-256: `{contract.digest}`",
            "",
            "## Allowed paths",
            "",
            *(f"- `{path}`" for path in contract.allowed_paths),
            "",
            "## Required checks",
            "",
            *(f"- `{command}`" for command in contract.required_checks),
            "",
            "Only modify allowed paths. Run exactly the required checks. A completion claim is not acceptance.",
            "",
        ]
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    return json_path, markdown_path


def _run(
    command: Sequence[str] | str,
    *,
    cwd: Path,
    shell: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        shell=shell,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _command_result(command: Sequence[str] | str, result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    rendered = command if isinstance(command, str) else " ".join(command)
    return {
        "command": rendered,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = _run(("git", *args), cwd=repo)
    if result.returncode != 0:
        raise ValueError(f"git_command_failed:{' '.join(args)}:{result.stderr.strip()}")
    return result


def collect_execution_evidence(
    contract: TaskContract,
    repository: Path | str,
    *,
    executor: str,
    agent_completion_claim: bool,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> ExecutionEvidence:
    """Collect Git evidence and run only the checks listed in the contract."""

    repo = Path(repository).resolve()
    if not repo.is_dir():
        raise ValueError("repository_not_found")
    actual_base = _git(repo, "rev-parse", f"{contract.base_commit}^{{commit}}").stdout.strip().lower()
    if actual_base != contract.base_commit:
        raise ValueError("base_commit_mismatch")
    observed_head = _git(repo, "rev-parse", "HEAD").stdout.strip().lower()
    name_status = _git(repo, "diff", "--name-status", contract.base_commit, "--").stdout
    changed: list[str] = []
    for line in name_status.splitlines():
        fields = line.split("\t")
        changed.extend(field.replace("\\", "/") for field in fields[1:])
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard").stdout
    changed.extend(line.replace("\\", "/") for line in untracked.splitlines() if line)
    diff_command = ("git", "diff", "--check", contract.base_commit, "--")
    diff_result = _run(diff_command, cwd=repo)
    check_results = tuple(
        _command_result(command, _run(command, cwd=repo, shell=True))
        for command in contract.required_checks
    )
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return ExecutionEvidence(
        schema_version=contract.schema_version,
        task_id=contract.task_id,
        executor=executor.strip() or "unknown",
        base_commit=actual_base,
        observed_head_or_tree=observed_head,
        changed_paths=tuple(dict.fromkeys(changed)),
        git_diff_check=_command_result(diff_command, diff_result),
        required_check_results=check_results,
        agent_completion_claim=bool(agent_completion_claim),
        started_at=started_at or now,
        completed_at=completed_at or now,
    )


def _path_allowed(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    return any(normalized == pattern or fnmatchcase(normalized, pattern) for pattern in patterns)


def accept_execution(contract: TaskContract, evidence: ExecutionEvidence) -> AcceptanceResult:
    """Deterministically accept only complete, matching, successful evidence."""

    reasons: list[str] = []
    if evidence.schema_version != contract.schema_version:
        reasons.append("schema_version_mismatch")
    if evidence.task_id != contract.task_id:
        reasons.append("task_id_mismatch")
    if evidence.base_commit != contract.base_commit:
        reasons.append("base_commit_mismatch")
    outside = tuple(path for path in evidence.changed_paths if not _path_allowed(path, contract.allowed_paths))
    if outside:
        reasons.extend(f"changed_path_outside_allowed_scope:{path}" for path in outside)
    if evidence.git_diff_check.get("exit_code") != 0:
        reasons.append("git_diff_check_failed")
    commands = tuple(result.get("command") for result in evidence.required_check_results)
    if commands != contract.required_checks:
        reasons.append("required_check_evidence_mismatch")
    for result in evidence.required_check_results:
        if not isinstance(result.get("exit_code"), int) or result.get("exit_code") != 0:
            reasons.append(f"required_check_failed:{result.get('command', '<missing>')}")
    accepted = not reasons
    summaries = tuple(
        {
            "command": result.get("command"),
            "exit_code": result.get("exit_code"),
            "passed": result.get("exit_code") == 0,
        }
        for result in evidence.required_check_results
    )
    return AcceptanceResult(
        schema_version=contract.schema_version,
        task_id=contract.task_id,
        accepted=accepted,
        scope_result="PASS" if not outside else "FAIL",
        required_check_results=summaries,
        blocking_reasons=tuple(dict.fromkeys(reasons)),
        evidence_digest=evidence.digest,
    )


def observe_capability(
    contract: TaskContract,
    evidence: ExecutionEvidence,
    acceptance: AcceptanceResult,
    *,
    task_class: str = "bounded_coding_task",
    attempts: int = 1,
) -> CapabilityObservation:
    started = datetime.fromisoformat(evidence.started_at)
    completed = datetime.fromisoformat(evidence.completed_at)
    elapsed = max(0.0, (completed - started).total_seconds())
    failure = None if acceptance.accepted else (
        acceptance.blocking_reasons[0].split(":", 1)[0] if acceptance.blocking_reasons else "unknown"
    )
    return CapabilityObservation(
        task_class=task_class,
        executor=evidence.executor,
        success=acceptance.accepted,
        attempts=max(1, attempts),
        elapsed_time=elapsed,
        failure_class=failure,
    )
