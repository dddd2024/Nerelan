"""Truthful report closure for the Architecture Spine authority chain.

Phase E of the authority closure rework. The final report must:

* derive its changed-file inventory from the real ``git diff`` output;
* clearly separate local validation from remote observations;
* never simultaneously claim that exact-head checks are both observed and
  pending;
* never let a stale observation support a new head.

This module is data-only: it does not execute Git or GitHub commands. Callers
feed it observed transcripts and the module reports whether the resulting
report would be internally consistent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_LOCAL_STATUSES = frozenset({"LOCAL_VALIDATED", "LOCAL_PARTIAL", "LOCAL_FAILED"})
_REMOTE_STATUSES = frozenset({
    "REMOTE_NOT_OBSERVED",
    "REMOTE_PENDING",
    "REMOTE_PASSED",
    "REMOTE_FAILED",
})
# Statuses that represent "the remote side has reached a conclusion".
_REMOTE_CONCLUSIVE = frozenset({"REMOTE_PASSED", "REMOTE_FAILED"})


@dataclass(frozen=True)
class ChangedFileInventory:
    """Changed-file inventory derived from the real Git diff.

    ``source`` records the provenance so downstream consumers can distinguish
    a real ``git diff --name-only`` transcript from any inferred substitute.
    """

    paths: tuple[str, ...]
    source: str
    base_sha: str
    head_sha: str

    def __post_init__(self) -> None:
        if not isinstance(self.paths, tuple) or not self.paths:
            raise ValueError("empty_changed_file_inventory")
        if not self.source.strip():
            raise ValueError("missing_or_invalid:source")
        if not self.base_sha.strip() or not self.head_sha.strip():
            raise ValueError("missing_or_invalid:sha")
        if self.base_sha == self.head_sha:
            raise ValueError("identical_base_and_head")

    @classmethod
    def from_git_diff(
        cls,
        diff_output: str,
        *,
        base_sha: str,
        head_sha: str,
    ) -> "ChangedFileInventory":
        """Build an inventory from ``git diff --name-only`` output.

        Empty diff output is rejected so the report cannot silently masquerade
        a no-op round as a real execution.
        """

        if not diff_output or not diff_output.strip():
            raise ValueError("empty_diff")
        paths = tuple(
            line.strip()
            for line in diff_output.splitlines()
            if line.strip()
        )
        if not paths:
            raise ValueError("empty_diff")
        return cls(
            paths=paths,
            source="git_diff_name_only",
            base_sha=base_sha,
            head_sha=head_sha,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "paths": list(self.paths),
            "source": self.source,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
        }


@dataclass(frozen=True)
class RemoteObservation:
    """Exact-head remote observations for CI, State Gate and Decision Preflight."""

    head_sha: str
    observed_at: str
    ci_status: str
    state_gate_status: str
    decision_preflight_status: str

    def __post_init__(self) -> None:
        for name, value in (
            ("ci_status", self.ci_status),
            ("state_gate_status", self.state_gate_status),
            ("decision_preflight_status", self.decision_preflight_status),
        ):
            if value not in _REMOTE_STATUSES:
                raise ValueError(f"invalid_remote_status:{name}:{value}")

    def is_stale_for(self, current_head: str) -> bool:
        """Return ``True`` when the observation was made against a different head."""

        if not self.head_sha:
            return False
        return self.head_sha != current_head

    def is_conclusive(self) -> bool:
        """Return ``True`` when all three signals have reached a conclusion.

        A conclusive observation has every signal in ``REMOTE_PASSED`` or
        ``REMOTE_FAILED``. ``REMOTE_NOT_OBSERVED`` and ``REMOTE_PENDING`` are
        not conclusive.
        """

        return all(
            status in _REMOTE_CONCLUSIVE
            for status in (
                self.ci_status,
                self.state_gate_status,
                self.decision_preflight_status,
            )
        )

    def has_pending(self) -> bool:
        return any(
            status == "REMOTE_PENDING"
            for status in (
                self.ci_status,
                self.state_gate_status,
                self.decision_preflight_status,
            )
        )

    def has_conclusive(self) -> bool:
        return any(
            status in _REMOTE_CONCLUSIVE
            for status in (
                self.ci_status,
                self.state_gate_status,
                self.decision_preflight_status,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "head_sha": self.head_sha,
            "observed_at": self.observed_at,
            "ci_status": self.ci_status,
            "state_gate_status": self.state_gate_status,
            "decision_preflight_status": self.decision_preflight_status,
        }


@dataclass(frozen=True)
class ReportTruth:
    """Final-report truth record combining local and remote evidence."""

    changed_files: ChangedFileInventory
    local_status: str
    remote_observation: RemoteObservation | None

    def __post_init__(self) -> None:
        if self.local_status not in _LOCAL_STATUSES:
            raise ValueError(f"invalid_local_status:{self.local_status}")

    def is_internally_consistent(self) -> bool:
        return not self.consistency_violations()

    def consistency_violations(self) -> tuple[str, ...]:
        violations: list[str] = []
        observation = self.remote_observation
        if observation is not None:
            # The report must not simultaneously claim that exact-head checks
            # are both observed (conclusive) and pending.
            if observation.has_pending() and observation.has_conclusive():
                violations.append(
                    "remote_status_contradiction:pending_and_conclusive_mixed"
                )
            # A stale observation cannot support a new head.
            if observation.head_sha and observation.head_sha != self.changed_files.head_sha:
                violations.append(
                    f"stale_remote_observation:head={observation.head_sha}:current={self.changed_files.head_sha}"
                )
            # LOCAL_FAILED contradicts REMOTE_PASSED: the local evidence and
            # the remote evidence cannot disagree on outcome.
            if self.local_status == "LOCAL_FAILED" and (
                observation.ci_status == "REMOTE_PASSED"
                or observation.state_gate_status == "REMOTE_PASSED"
                or observation.decision_preflight_status == "REMOTE_PASSED"
            ):
                violations.append(
                    "local_remote_status_contradiction:local_failed_remote_passed"
                )
        return tuple(dict.fromkeys(violations))

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_files": self.changed_files.to_dict(),
            "local_status": self.local_status,
            "remote_observation": (
                self.remote_observation.to_dict() if self.remote_observation else None
            ),
            "internally_consistent": self.is_internally_consistent(),
            "consistency_violations": list(self.consistency_violations()),
        }
