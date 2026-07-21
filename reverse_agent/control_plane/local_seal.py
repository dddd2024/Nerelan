"""Phase B: non-self-referential local execution seal.

Splits the post-execution gate into two stages so that the evaluator and
sealer are never part of their own subject set (F4):

- ``evaluate_reconciliation`` reads sealed subject records and produces a
  ``ReconciliationCandidate`` with a stable subject digest.
- ``seal_local`` validates the candidate, binds it to subject/plan/result
  digests, and emits a ``LOCAL_RECONCILED`` (or ``LOCAL_RECONCILIATION_BLOCKED``)
  seal.

The local seal never claims remote success. Final acceptance requires an
independent remote publication seal.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable

from .models import (
    ExecutionRecord,
    TransitionCommand,
    TransitionCommandPlan,
)


# Command ids that belong to the evaluator/sealer itself. Records with these
# ids are excluded from the subject set so the gate cannot validate itself.
_SELF_COMMAND_IDS = frozenset({
    "gate.reconcile_evaluate",
    "gate.seal_local",
})


def _sha256_json(payload: Any) -> str:
    """Stable sha256 digest of a JSON-serializable payload."""

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# ReconciliationCandidate (evaluator output)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconciliationCandidate:
    """Result of evaluating sealed subject records against the plan."""

    status: str  # "RECONCILED" | "BLOCKED"
    decision_id: str
    round_id: str
    subject_record_count: int
    subject_digest: str
    missing_command_ids: tuple[str, ...]
    matched_command_ids: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    matched_records: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "decision_id": self.decision_id,
            "round_id": self.round_id,
            "subject_record_count": self.subject_record_count,
            "subject_digest": self.subject_digest,
            "missing_command_ids": list(self.missing_command_ids),
            "matched_command_ids": list(self.matched_command_ids),
            "blocking_reasons": list(self.blocking_reasons),
            "matched_records": [dict(r) for r in self.matched_records],
        }


def evaluate_reconciliation(
    plan: TransitionCommandPlan,
    records: Iterable[ExecutionRecord],
) -> ReconciliationCandidate:
    """Evaluate sealed subject records against the plan.

    The evaluator/sealer command ids (``gate.reconcile_evaluate``,
    ``gate.seal_local``) are filtered out of the subject set so the gate
    cannot validate itself (F4).
    """

    subject_records = tuple(
        r for r in records
        if r.command_id not in _SELF_COMMAND_IDS
    )

    matched: list[dict[str, Any]] = []
    matched_ids: list[str] = []
    blocking_reasons: list[str] = []

    plan_by_id: dict[str, TransitionCommand] = {}
    for entry in plan.commands:
        plan_by_id[entry.command_id] = entry

    for record in subject_records:
        plan_entry = plan_by_id.get(record.command_id)
        if plan_entry is None:
            blocking_reasons.append(
                f"unknown_command_id:{record.command_id}"
            )
            continue
        if plan_entry.command != record.command:
            blocking_reasons.append(
                f"command_string_diverges:{record.command_id}"
            )
            continue
        if record.exit_code is None or record.exit_code not in plan_entry.expected_exit_codes:
            blocking_reasons.append(
                f"exit_code_outside_expected:{record.command_id}:{record.exit_code}"
            )
            continue
        matched.append(record.to_dict())
        matched_ids.append(record.command_id)

    # Required command coverage: every required plan entry that is part of
    # the subject set must have a match. Commands marked
    # ``subject_to_reconciliation=False`` (e.g. the evaluator/sealer itself)
    # are required to be executed but are NOT part of the subject set being
    # reconciled (F4: non-self-referential reconciliation).
    required_ids = {
        entry.command_id for entry in plan.commands
        if entry.required and entry.subject_to_reconciliation
    }
    matched_id_set = set(matched_ids)
    missing = tuple(
        dict.fromkeys(
            command_id for command_id in (
                entry.command_id for entry in plan.commands
                if entry.required and entry.subject_to_reconciliation
            )
            if command_id not in matched_id_set
        )
    )

    status = "RECONCILED" if not blocking_reasons and not missing else "BLOCKED"
    subject_digest = _sha256_json([r.to_dict() for r in subject_records])

    return ReconciliationCandidate(
        status=status,
        decision_id=plan.decision_id,
        round_id=plan.round_id,
        subject_record_count=len(subject_records),
        subject_digest=subject_digest,
        missing_command_ids=missing,
        matched_command_ids=tuple(dict.fromkeys(matched_ids)),
        blocking_reasons=tuple(dict.fromkeys(blocking_reasons)),
        matched_records=tuple(matched),
    )


# ---------------------------------------------------------------------------
# LocalSeal (sealer output)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LocalSeal:
    """Local execution seal binding subject, plan and result digests.

    Status is ``LOCAL_RECONCILED`` when the candidate passed; otherwise
    ``LOCAL_RECONCILIATION_BLOCKED``. The seal never claims remote success.
    """

    status: str
    decision_id: str
    round_id: str
    activation_base_sha: str
    subject_digest: str
    plan_digest: str
    result_digest: str
    sealed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "decision_id": self.decision_id,
            "round_id": self.round_id,
            "activation_base_sha": self.activation_base_sha,
            "subject_digest": self.subject_digest,
            "plan_digest": self.plan_digest,
            "result_digest": self.result_digest,
            "sealed_at": self.sealed_at,
        }


def _plan_digest(plan: TransitionCommandPlan) -> str:
    """Stable digest of the command plan (prevents plan tampering)."""

    return _sha256_json(plan.to_dict())


def _candidate_result_digest(candidate: ReconciliationCandidate) -> str:
    """Stable digest of the candidate result (prevents result tampering)."""

    return _sha256_json(candidate.to_dict())


def _now_utc() -> str:
    from datetime import datetime, timezone
    return datetime.now(tz=timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def seal_local(
    *,
    candidate: ReconciliationCandidate,
    plan: TransitionCommandPlan,
    decision_id: str,
    round_id: str,
    activation_base_sha: str,
) -> LocalSeal:
    """Produce a local execution seal from a reconciliation candidate.

    The sealer validates that the candidate is RECONCILED and binds it to
    the plan digest and a result digest. It never claims remote success.
    """

    status = "LOCAL_RECONCILED" if candidate.status == "RECONCILED" else "LOCAL_RECONCILIATION_BLOCKED"
    return LocalSeal(
        status=status,
        decision_id=decision_id,
        round_id=round_id,
        activation_base_sha=activation_base_sha,
        subject_digest=candidate.subject_digest,
        plan_digest=_plan_digest(plan),
        result_digest=_candidate_result_digest(candidate),
        sealed_at=_now_utc(),
    )
