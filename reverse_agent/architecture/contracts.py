"""Strict, stable JSON contracts for the Architecture Spine v1."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, TypedDict

from .risk import AcceptanceStatus, AuthorizationStatus, RiskTier, WorkflowRoute


SCHEMA_VERSION = 1
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing_or_invalid:{field}")
    return value.strip()


def _strings(value: object, field: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"missing_or_invalid:{field}")
    items = tuple(_text(item, field) for item in value)
    if not allow_empty and not items:
        raise ValueError(f"missing_or_invalid:{field}")
    return items


def _schema(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported_schema_version")


def stable_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class PlanningReference:
    artifact_type: str
    path_or_uri: str
    digest: str
    summary: str
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PlanningReference":
        _schema(payload)
        digest = _text(payload.get("digest"), "digest").lower()
        if not _SHA256.fullmatch(digest):
            raise ValueError("missing_or_invalid:digest")
        if payload.get("command_authority") not in (None, False):
            raise ValueError("planning_reference_cannot_authorize_commands")
        return cls(
            artifact_type=_text(payload.get("artifact_type"), "artifact_type"),
            path_or_uri=_text(payload.get("path_or_uri"), "path_or_uri"),
            digest=digest,
            summary=_text(payload.get("summary"), "summary"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "path_or_uri": self.path_or_uri,
            "digest": self.digest,
            "summary": self.summary,
            "command_authority": False,
        }


@dataclass(frozen=True)
class GitHubWorkItem:
    repository: str
    item_number: int
    immutable_observation_ref: str
    title: str
    acceptance_criteria: tuple[str, ...]
    requested_operations: tuple[str, ...]
    requested_paths: tuple[str, ...]
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "GitHubWorkItem":
        _schema(payload)
        number = payload.get("item_number")
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ValueError("missing_or_invalid:item_number")
        return cls(
            repository=_text(payload.get("repository"), "repository"),
            item_number=number,
            immutable_observation_ref=_text(payload.get("immutable_observation_ref"), "immutable_observation_ref"),
            title=_text(payload.get("title"), "title"),
            acceptance_criteria=_strings(payload.get("acceptance_criteria"), "acceptance_criteria"),
            requested_operations=_strings(payload.get("requested_operations"), "requested_operations"),
            requested_paths=_strings(payload.get("requested_paths"), "requested_paths"),
        )

    @property
    def identity(self) -> str:
        return f"{self.repository}#{self.item_number}@{self.immutable_observation_ref}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository": self.repository,
            "item_number": self.item_number,
            "immutable_observation_ref": self.immutable_observation_ref,
            "title": self.title,
            "acceptance_criteria": list(self.acceptance_criteria),
            "requested_operations": list(self.requested_operations),
            "requested_paths": list(self.requested_paths),
        }


@dataclass(frozen=True)
class WorkflowIdentity:
    workflow_id: str
    work_item_identity: str
    attempt: int = 1
    decision_id: str = ""
    round_id: str = ""
    policy_digest: str = ""
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _text(self.workflow_id, "workflow_id")
        _text(self.work_item_identity, "work_item_identity")
        if self.attempt < 1:
            raise ValueError("missing_or_invalid:attempt")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workflow_id": self.workflow_id,
            "work_item_identity": self.work_item_identity,
            "attempt": self.attempt,
            "decision_id": self.decision_id,
            "round_id": self.round_id,
            "policy_digest": self.policy_digest,
        }


@dataclass(frozen=True)
class ExecutionEnvelope:
    operations: tuple[str, ...]
    paths: tuple[str, ...]
    network_requested: bool = False
    binary_execution_requested: bool = False
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operations": list(self.operations),
            "paths": list(self.paths),
            "network_requested": self.network_requested,
            "binary_execution_requested": self.binary_execution_requested,
        }


@dataclass(frozen=True)
class AuthorizationRequirement:
    required: bool
    route: WorkflowRoute
    reasons: tuple[str, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.required != (self.route is WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED):
            raise ValueError("authorization_requirement_route_mismatch")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "required": self.required,
            "route": self.route.value,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class AuthorizationRequest:
    workflow_identity: WorkflowIdentity
    risk_tier: RiskTier
    envelope: ExecutionEnvelope
    decision_id: str = ""
    round_id: str = ""
    command: str = ""
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workflow_identity": self.workflow_identity.to_dict(),
            "risk_tier": self.risk_tier.value,
            "envelope": self.envelope.to_dict(),
            "decision_id": self.decision_id,
            "round_id": self.round_id,
            "command": self.command,
        }


@dataclass(frozen=True)
class AuthorizationResult:
    status: AuthorizationStatus
    reasons: tuple[str, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "status": self.status.value, "reasons": list(self.reasons)}


@dataclass(frozen=True)
class ArchitectureDecision:
    risk_tier: RiskTier | None
    route: WorkflowRoute
    reasons: tuple[str, ...]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "risk_tier": self.risk_tier.value if self.risk_tier else None,
            "route": self.route.value,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class AcceptanceResult:
    status: AcceptanceStatus
    executable: bool
    reasons: tuple[str, ...]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "executable": self.executable,
            "reasons": list(self.reasons),
        }


class DevelopmentWorkflowState(TypedDict, total=False):
    work_item_input: dict[str, Any]
    planning_inputs: list[dict[str, Any]]
    work_item: dict[str, Any]
    planning_references: list[dict[str, Any]]
    workflow_identity: dict[str, Any]
    risk_decision: dict[str, Any]
    risk_policy_snapshot: dict[str, Any]
    caller_supplied_risk_policy_snapshot: dict[str, Any]
    authorization_result: dict[str, Any]
    acceptance_result: dict[str, Any]
    node_trace: list[str]


@dataclass(frozen=True)
class PathRiskFloorSnapshot:
    """Architecture-layer path-risk floor data.

    This concrete dataclass mirrors the control-plane ``PathRiskFloor`` but
    lives in the architecture layer so it can be carried inside a
    ``RiskPolicySnapshot`` without violating the layer boundary.
    """

    entries: tuple[tuple[str, str], ...]
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PathRiskFloorSnapshot":
        raw_entries = payload.get("entries")
        if not isinstance(raw_entries, (list, tuple)):
            raise ValueError("missing_or_invalid:path_risk_floor")
        entries: list[tuple[str, str]] = []
        for item in raw_entries:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise ValueError("missing_or_invalid:path_risk_floor")
            pattern = _text(item[0], "path_risk_floor_pattern")
            tier_label = _text(item[1], "path_risk_floor_tier").upper()
            try:
                RiskTier(tier_label)
            except ValueError as exc:
                raise ValueError(f"missing_or_invalid:path_risk_floor_tier:{tier_label}") from exc
            entries.append((pattern, tier_label))
        if not entries:
            raise ValueError("missing_or_invalid:path_risk_floor")
        return cls(entries=tuple(entries))

    def risk_for_path(self, path: str) -> str | None:
        normalized = path.replace("\\", "/").lstrip("./")
        highest: str | None = None
        rank = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}
        for pattern, tier_label in self.entries:
            candidate = pattern.replace("\\", "/").lstrip("./")
            if not self._matches(candidate, normalized):
                continue
            if highest is None or rank.get(tier_label, 0) > rank.get(highest, 0):
                highest = tier_label
        return highest

    @staticmethod
    def _matches(candidate: str, normalized: str) -> bool:
        from fnmatch import fnmatch

        leading_any = candidate.startswith("**/")
        if leading_any:
            candidate = candidate[3:]
        trailing_any = candidate.endswith("/**")
        if trailing_any:
            candidate = candidate[:-3]
        candidate = candidate.strip("/")

        if leading_any and trailing_any:
            if not candidate:
                return True
            return (
                normalized == candidate
                or normalized.startswith(f"{candidate}/")
                or normalized.endswith(f"/{candidate}")
                or f"/{candidate}/" in f"/{normalized}/"
            )
        if leading_any:
            if "*" in candidate or "?" in candidate:
                return fnmatch(normalized, candidate) or fnmatch(normalized, f"*/{candidate}")
            return normalized == candidate or normalized.endswith(f"/{candidate}")
        if trailing_any:
            return normalized == candidate or normalized.startswith(f"{candidate}/")
        return normalized == candidate or fnmatch(normalized, candidate)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "entries": [[pattern, tier] for pattern, tier in self.entries],
        }


@dataclass(frozen=True)
class CapabilityRiskRule:
    """Maps an operation name to a minimum risk tier.

    When an envelope declares ``operation``, its risk must be at least
    ``risk_tier``. Used by :meth:`RiskPolicySnapshot.resolved_capability_risk_for`
    to compute a single ``capability_flag_risk`` value for the classifier.
    """

    operation: str
    risk_tier: RiskTier
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CapabilityRiskRule":
        operation = _text(payload.get("operation"), "capability_risk_rule_operation")
        tier_label = _text(payload.get("risk_tier"), "capability_risk_rule_tier").upper()
        try:
            tier = RiskTier(tier_label)
        except ValueError as exc:
            raise ValueError(f"missing_or_invalid:capability_risk_rule_tier:{tier_label}") from exc
        return cls(operation=operation, risk_tier=tier)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "risk_tier": self.risk_tier.value,
        }


_TIER_RANK = {RiskTier.R0: 0, RiskTier.R1: 1, RiskTier.R2: 2, RiskTier.R3: 3}


@dataclass(frozen=True)
class RiskPolicySnapshot:
    """Immutable, Decision-bound runtime risk policy.

    Phase D: bound to the active Decision (``decision_id``/``round_id``),
    carries the path-risk floor and capability-risk rules, and exposes a
    ``policy_digest`` that the runtime can compare against the authorized
    digest to detect drift. The classify node fails closed when the snapshot
    is missing, the identity mismatches, or the digest has changed.
    """

    decision_id: str
    round_id: str
    path_risk_floor: PathRiskFloorSnapshot
    capability_risk_rules: tuple[CapabilityRiskRule, ...]
    policy_digest: str
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RiskPolicySnapshot":
        _schema(payload)
        decision_id = _text(payload.get("decision_id"), "decision_id")
        round_id = _text(payload.get("round_id"), "round_id")
        floor_payload = payload.get("path_risk_floor")
        if not isinstance(floor_payload, Mapping):
            raise ValueError("missing_or_invalid:path_risk_floor")
        path_risk_floor = PathRiskFloorSnapshot.from_mapping(floor_payload)
        raw_rules = payload.get("capability_risk_rules")
        if not isinstance(raw_rules, (list, tuple)) or not raw_rules:
            raise ValueError("missing_or_invalid:capability_risk_rules")
        rules = tuple(
            CapabilityRiskRule.from_mapping(item) if isinstance(item, Mapping)
            else CapabilityRiskRule.from_mapping({"operation": item[0], "risk_tier": item[1]})
            for item in raw_rules
        )
        # Phase E 8.3: preserve a caller-supplied policy_digest so the
        # provider can detect a forged digest. When the payload omits the
        # digest (the normal case), recompute it from the canonical content.
        supplied_digest = payload.get("policy_digest")
        if isinstance(supplied_digest, str) and supplied_digest:
            digest = supplied_digest
        else:
            digest = _compute_policy_digest(decision_id, round_id, path_risk_floor, rules)
        return cls(
            decision_id=decision_id,
            round_id=round_id,
            path_risk_floor=path_risk_floor,
            capability_risk_rules=rules,
            policy_digest=digest,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "round_id": self.round_id,
            "path_risk_floor": self.path_risk_floor.to_dict(),
            "capability_risk_rules": [rule.to_dict() for rule in self.capability_risk_rules],
            "policy_digest": self.policy_digest,
        }

    def identity_matches(self, decision_id: str, round_id: str) -> bool:
        return self.decision_id == decision_id and self.round_id == round_id

    def resolved_capability_risk_for(self, operations: tuple[str, ...]) -> RiskTier | None:
        """Return the max risk tier across all capability rules that match.

        If none of the operations appear in the rules, returns ``None``.
        """

        normalized = {op.strip().lower() for op in operations if isinstance(op, str) and op.strip()}
        applicable: list[RiskTier] = [
            rule.risk_tier
            for rule in self.capability_risk_rules
            if rule.operation in normalized
        ]
        if not applicable:
            return None
        return max(applicable, key=lambda tier: _TIER_RANK[tier])


def _compute_policy_digest(
    decision_id: str,
    round_id: str,
    path_risk_floor: PathRiskFloorSnapshot,
    capability_risk_rules: tuple[CapabilityRiskRule, ...],
) -> str:
    import hashlib

    payload = {
        "decision_id": decision_id,
        "round_id": round_id,
        "path_risk_floor": path_risk_floor.to_dict(),
        "capability_risk_rules": [rule.to_dict() for rule in capability_risk_rules],
    }
    serialized = stable_json(payload)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
