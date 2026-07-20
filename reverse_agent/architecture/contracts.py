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
    authorization_result: dict[str, Any]
    acceptance_result: dict[str, Any]
    node_trace: list[str]
