"""Pure, claims-only review records; no verifier, persistence or authority.

The trusted collector must verify Git/scanner identities separately. Normalizing
a supplied identity or disposing of a finding never establishes acceptance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re
from typing import Any, Sequence

from .control_store import canonical_json, sha256_json
from .opencode_executor import redact_secrets


class ReviewContractError(ValueError):
    """Stable error code, without echoing an untrusted payload."""


_TARGET_FIELDS = frozenset({
    "forge", "repository", "change_request", "base_ref", "base_sha", "base_tree_sha",
    "head_ref", "head_sha", "head_tree_sha", "patch_sha256", "paths",
    "excluded_paths", "profile", "observations_sha256",
})
_FINDING_FIELDS = frozenset({
    "rule_id", "category", "severity", "confidence", "path", "start_line", "end_line",
    "symbol", "summary", "source", "evidence_refs",
})
_DERIVED_FINDING_FIELDS = frozenset({"target_digest", "fingerprint", "finding_id"})
_FEEDBACK_FIELDS = frozenset({"finding_id", "target_digest", "finding_record_digest", "status",
                              "reason", "evidence_refs", "adjudicator_ref", "observed_at"})
_SOURCE_ORDER = {"deterministic": 0, "external": 1, "model": 2}
_CATEGORIES = frozenset({"correctness", "security", "compatibility", "concurrency",
                         "performance", "accessibility", "architecture", "other"})
_FEEDBACK_STATUSES = frozenset({"ACKNOWLEDGED", "NOT_REPRODUCIBLE", "DISMISSED_WITH_REASON"})
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}\Z")
_FLAGS = ("evidence_verified", "independent_acceptance", "execution_authorized",
          "repair_authorized", "landing_authorized")


def _error(code: str) -> None:
    raise ReviewContractError(code)


def _bounded(value: Any, depth: int = 0, budget: list[int] | None = None) -> None:
    if budget is None:
        budget = [0]
    budget[0] += 1
    if depth > 8 or budget[0] > 5000:
        _error("review_data_too_large")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                _error("review_data_invalid")
            _bounded(key, depth + 1, budget)
            _bounded(item, depth + 1, budget)
    elif type(value) in (list, tuple):
        for item in value:
            _bounded(item, depth + 1, budget)
    elif type(value) is str:
        if len(value) > 4000 or not value.isprintable():
            _error("review_text_invalid")
    elif value is not None and type(value) not in (int, bool):
        _error("review_data_invalid")


def _mapping(value: Any, fields: frozenset[str]) -> dict:
    if type(value) is not dict or set(value) != fields:
        _error("review_fields_invalid")
    _bounded(value)
    return value


def _text(value: Any, maximum: int = 200) -> str:
    if (type(value) is not str or not value or len(value) > maximum
            or value != value.strip() or not value.isprintable()):
        _error("review_text_invalid")
    return value


def _digest(value: Any) -> str:
    if type(value) is not str or not _SHA256.fullmatch(value):
        _error("review_digest_invalid")
    return value


def _key(value: Any) -> str:
    if type(value) is not str or not _KEY.fullmatch(value):
        _error("review_key_invalid")
    return value


def _summary(value: Any) -> str:
    value = _text(value, 2000)
    # Discard the whole field when the shared detector matches. This prevents
    # a partially redacted Authorization phrase from retaining its credential.
    return "[REDACTED]" if redact_secrets(value) != value else value


def _path(value: Any) -> str:
    value = _text(value, 400)
    if (value.startswith("/") or any(c in value for c in "\\:*?[]")
            or any(part in ("", ".", "..") for part in value.split("/"))):
        _error("review_path_invalid")
    return value


def _strings(value: Any, validator: Any, *, empty: bool = False, maximum: int = 256) -> list[str]:
    if type(value) not in (list, tuple) or len(value) > maximum or (not value and not empty):
        _error("review_list_invalid")
    items = [validator(item) for item in value]
    if len(items) != len(set(items)):
        _error("review_duplicate_value")
    return sorted(items)


def _target_document(raw: Any) -> dict:
    raw = _mapping(raw, _TARGET_FIELDS)
    doc = {key: _text(raw[key]) for key in ("forge", "repository", "base_ref", "head_ref", "profile")}
    doc["change_request"] = None if raw["change_request"] is None else _text(raw["change_request"])
    for key in ("base_sha", "base_tree_sha", "head_sha", "head_tree_sha"):
        oid = raw[key]
        if type(oid) is not str or not _OID.fullmatch(oid):
            _error("review_oid_invalid")
        doc[key] = oid
    if len({len(doc[key]) for key in ("base_sha", "base_tree_sha", "head_sha", "head_tree_sha")}) != 1:
        _error("review_oid_family_mismatch")
    for key in ("patch_sha256", "observations_sha256"):
        doc[key] = _digest(raw[key])
    doc["paths"] = _strings(raw["paths"], _path)
    doc["excluded_paths"] = _strings(raw["excluded_paths"], _path, empty=True)
    if not set(doc["excluded_paths"]) <= set(doc["paths"]):
        _error("review_exclusion_outside_scope")
    if not set(doc["paths"]) - set(doc["excluded_paths"]):
        _error("review_scope_empty")
    return doc


@dataclass(frozen=True, slots=True)
class _ClaimsOnly:
    evidence_verified: bool = field(default=False, init=False)
    independent_acceptance: bool = field(default=False, init=False)
    execution_authorized: bool = field(default=False, init=False)
    repair_authorized: bool = field(default=False, init=False)
    landing_authorized: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class ReviewTarget(_ClaimsOnly):
    _json: str = field(repr=False)

    def __post_init__(self) -> None:
        doc = _target_document(json.loads(self._json))
        if canonical_json(doc) != self._json:
            _error("review_target_not_canonical")

    @property
    def document(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256_json(self.document)

    @property
    def reviewed_paths(self) -> frozenset[str]:
        doc = self.document
        return frozenset(doc["paths"]) - frozenset(doc["excluded_paths"])

    def to_record(self) -> dict:
        return {"document": self.document, "digest": self.digest, **{key: False for key in _FLAGS}}


def normalize_review_target(raw: Any) -> ReviewTarget:
    return ReviewTarget(canonical_json(_target_document(raw)))


def _finding_document(target: ReviewTarget, raw: Any) -> dict:
    if type(target) is not ReviewTarget:
        _error("review_target_invalid")
    raw = _mapping(raw, _FINDING_FIELDS)
    doc = {key: _key(raw[key]) for key in ("rule_id",)}
    for key, allowed in (("category", _CATEGORIES),
                         ("severity", {"critical", "high", "medium", "low", "info"}),
                         ("confidence", {"high", "medium", "low"}),
                         ("source", set(_SOURCE_ORDER))):
        if type(raw[key]) is not str or raw[key] not in allowed:
            _error("review_enum_invalid")
        doc[key] = raw[key]
    doc["path"] = _path(raw["path"])
    if doc["path"] not in target.reviewed_paths:
        _error("review_finding_outside_scope")
    for key in ("start_line", "end_line"):
        if type(raw[key]) is not int or not 1 <= raw[key] <= 10_000_000:
            _error("review_line_invalid")
        doc[key] = raw[key]
    if doc["end_line"] < doc["start_line"]:
        _error("review_line_invalid")
    doc["symbol"] = None if raw["symbol"] is None else _text(raw["symbol"])
    doc["summary"] = _summary(raw["summary"])
    doc["evidence_refs"] = _strings(raw["evidence_refs"], _digest, maximum=32)
    identity = {key: doc[key] for key in ("rule_id", "category", "path", "start_line", "end_line", "symbol")}
    doc["fingerprint"] = sha256_json(identity)
    doc["target_digest"] = target.digest
    doc["finding_id"] = sha256_json({"target_digest": target.digest, "fingerprint": doc["fingerprint"]})
    return doc


@dataclass(frozen=True, slots=True)
class ReviewFinding(_ClaimsOnly):
    target: ReviewTarget
    _json: str = field(repr=False)

    def __post_init__(self) -> None:
        raw = json.loads(self._json)
        _mapping(raw, _FINDING_FIELDS | _DERIVED_FINDING_FIELDS)
        doc = _finding_document(self.target, {key: raw[key] for key in _FINDING_FIELDS})
        if canonical_json(doc) != self._json:
            _error("review_finding_identity_mismatch")

    @property
    def document(self) -> dict:
        return json.loads(self._json)

    @property
    def finding_id(self) -> str:
        return self.document["finding_id"]

    def to_record(self) -> dict:
        return {"document": self.document, **{key: False for key in _FLAGS}}


def normalize_review_finding(target: ReviewTarget, raw: Any) -> ReviewFinding:
    return ReviewFinding(target, canonical_json(_finding_document(target, raw)))


def _findings(values: Any) -> tuple[ReviewFinding, ...]:
    if type(values) not in (list, tuple) or len(values) > 256:
        _error("review_findings_invalid")
    if any(type(value) is not ReviewFinding for value in values):
        _error("review_finding_invalid")
    return tuple(values)


@dataclass(frozen=True, slots=True)
class FindingGroup(_ClaimsOnly):
    representative: ReviewFinding
    contributions: tuple[ReviewFinding, ...]

    def __post_init__(self) -> None:
        if type(self.contributions) is not tuple:
            _error("review_group_identity_mismatch")
        values = _findings(self.contributions)
        if (type(self.representative) is not ReviewFinding or not values
                or self.representative not in values
                or any(value.finding_id != self.representative.finding_id for value in values)):
            _error("review_group_identity_mismatch")

    @property
    def document(self) -> dict:
        docs = [finding.document for finding in self.contributions]
        return {"representative": self.representative.document,
                "contributions": docs,
                "sources": sorted({doc["source"] for doc in docs}),
                "evidence_refs": sorted({ref for doc in docs for ref in doc["evidence_refs"]})}


def deduplicate_review_findings(values: Sequence[ReviewFinding]) -> tuple[FindingGroup, ...]:
    findings = _findings(values)
    if len({finding.target.digest for finding in findings}) > 1:
        _error("review_target_generation_mismatch")
    groups: dict[str, dict[str, ReviewFinding]] = {}
    for finding in findings:
        groups.setdefault(finding.finding_id, {})[finding._json] = finding
    result = []
    for finding_id in sorted(groups):
        contributions = tuple(sorted(groups[finding_id].values(),
            key=lambda value: (_SOURCE_ORDER[value.document["source"]], value._json)))
        result.append(FindingGroup(contributions[0], contributions))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class FindingState(_ClaimsOnly):
    finding: ReviewFinding
    current_target: ReviewTarget

    def __post_init__(self) -> None:
        if type(self.finding) is not ReviewFinding or type(self.current_target) is not ReviewTarget:
            _error("review_target_invalid")

    @property
    def status(self) -> str:
        return "OPEN" if self.finding.target.digest == self.current_target.digest else "STALE_AFTER_TARGET_CHANGE"


def reconcile_review_findings(values: Sequence[ReviewFinding], current_target: ReviewTarget) -> tuple[FindingState, ...]:
    if type(current_target) is not ReviewTarget:
        _error("review_target_invalid")
    findings = _findings(values)
    return tuple(FindingState(finding, current_target) for finding in sorted(findings, key=lambda value: value._json))


@dataclass(frozen=True, slots=True)
class ReviewFeedback(_ClaimsOnly):
    finding: ReviewFinding
    _json: str = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.finding) is not ReviewFinding:
            _error("review_finding_invalid")
        raw = _mapping(json.loads(self._json), _FEEDBACK_FIELDS)
        normalized = _feedback_document(self.finding, **{key: raw[key] for key in
            ("status", "reason", "evidence_refs", "adjudicator_ref", "observed_at")})
        if canonical_json(normalized) != self._json:
            _error("review_feedback_identity_mismatch")

    @property
    def document(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256_json(self.document)

    def to_record(self) -> dict:
        return {"document": self.document, "digest": self.digest, **{key: False for key in _FLAGS}}


def _feedback_document(
    finding: ReviewFinding, *, status: str,
    reason: str, evidence_refs: Sequence[str], adjudicator_ref: str, observed_at: str,
) -> dict:
    if type(status) is not str or status not in _FEEDBACK_STATUSES:
        _error("review_feedback_status_invalid")
    timestamp = _text(observed_at, 80)
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            _error("review_feedback_time_invalid")
        timestamp = parsed.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    except (ValueError, OverflowError):
        _error("review_feedback_time_invalid")
    return {"finding_id": finding.finding_id, "target_digest": finding.target.digest,
           "finding_record_digest": sha256_json(finding.document), "status": status,
           "reason": _summary(reason),
           "evidence_refs": _strings(evidence_refs, _digest, maximum=32),
           "adjudicator_ref": _key(adjudicator_ref), "observed_at": timestamp}


def record_review_feedback(
    finding: ReviewFinding, current_target: ReviewTarget, *, status: str,
    reason: str, evidence_refs: Sequence[str], adjudicator_ref: str, observed_at: str,
) -> ReviewFeedback:
    if type(finding) is not ReviewFinding or type(current_target) is not ReviewTarget:
        _error("review_feedback_target_invalid")
    if finding.target.digest != current_target.digest:
        _error("review_feedback_stale_target")
    doc = _feedback_document(finding, status=status, reason=reason, evidence_refs=evidence_refs,
                             adjudicator_ref=adjudicator_ref, observed_at=observed_at)
    return ReviewFeedback(finding, canonical_json(doc))


def feedback_for_current_target(feedback: ReviewFeedback, current_target: ReviewTarget) -> ReviewFeedback | None:
    if type(feedback) is not ReviewFeedback or type(current_target) is not ReviewTarget:
        _error("review_feedback_target_invalid")
    return feedback if feedback.document["target_digest"] == current_target.digest else None
