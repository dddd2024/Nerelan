"""Canonical candidate-policy data and side-effect-free operation previews.

Confirmation strings and upstream observations are declarations supplied by
the caller. This module does not authenticate them, activate a window, mint
authority, reserve a budget, append a receipt, or invoke an adapter.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import json
from pathlib import PurePosixPath
import re
from typing import Any

from .autonomy import KNOWN_OPERATIONS, MAX_WINDOW_DURATION
from .control_store import canonical_json, reject_sensitive_keys, sha256_json
from .run_store import TaskStoreError


DECLARED_CAPABILITIES = KNOWN_OPERATIONS | frozenset(
    "read_repository modify_approved_paths modify_project create_issue update_issue "
    "create_branch push_task_branch mark_ready request_review merge_pr "
    "delete_merged_branch push_main create_tag create_github_release publish_package "
    "publish_container deploy_preview deploy_staging deploy_production rollback_deployment "
    "spawn_worker approve_worker_low_risk approve_worker_in_scope replan_within_goal "
    "retry_product_failure retry_infrastructure_failure".split()
)
ROLES = frozenset({"controller", "planner", "coder", "reviewer", "verifier", "publisher"})
STOP_CONDITIONS = frozenset(
    "policy_expiry policy_identity_mismatch secret_exposure authority_expansion "
    "unexpected_repository unexpected_environment rollback_failure receipt_failure "
    "budget_corruption unknown_capability merge_conflict base_drift path_drift "
    "required_check_failure artifact_mismatch worker_outside_scope".split()
)
MANDATORY_STOPS = frozenset(
    "policy_expiry policy_identity_mismatch secret_exposure authority_expansion "
    "unexpected_repository unexpected_environment rollback_failure receipt_failure "
    "budget_corruption unknown_capability".split()
)
FIELDS = frozenset(
    "schema_version policy_id policy_revision owner_identity owner_confirmation_event "
    "created_at starts_at expires_at repositories base_branches head_branch_patterns "
    "paths goals capabilities worker_delegation required_checks required_review_count "
    "merge_methods publication_targets deployment_environments deployment_artifact_digests rollback_policy "
    "operation_budgets usage_budgets retry_budgets stop_conditions notifications".split()
)
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,199}\Z")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_OID = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})\Z")
_DIGEST = re.compile(r"[a-f0-9]{64}\Z")
_ARTIFACT = re.compile(r"sha256:[a-f0-9]{64}\Z")
_REFERENCE = re.compile(r"(?:vault|credential):[A-Za-z0-9][A-Za-z0-9._:-]{0,99}\Z")


class PolicyPreviewError(ValueError):
    """Stable sanitized data-validation reason; never includes supplied values."""


@dataclass(frozen=True)
class CanonicalPolicyCandidate:
    canonical_document: str
    canonical_digest: str

    def document(self) -> dict[str, Any]:
        """Return a fresh copy; mutation cannot change the canonical candidate."""
        return json.loads(self.canonical_document)


@dataclass(frozen=True)
class PolicyPreviewResult:
    eligible: bool
    reason: str
    canonical_digest: str
    execution_authorized: bool = field(default=False, init=False)
    owner_confirmation_verified: bool = field(default=False, init=False)
    upper_authority_verified: bool = field(default=False, init=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _bounded_data(value: Any, depth: int = 0, counter: list[int] | None = None) -> None:
    counter = [0] if counter is None else counter
    counter[0] += 1
    if counter[0] > 4096 or depth > 8:
        raise PolicyPreviewError("policy_data_limit")
    if type(value) is dict:
        if len(value) > 64 or any(type(k) is not str or len(k) > 100 for k in value):
            raise PolicyPreviewError("invalid_policy_data")
        for child in value.values():
            _bounded_data(child, depth + 1, counter)
    elif type(value) is list:
        if len(value) > 128:
            raise PolicyPreviewError("policy_data_limit")
        for child in value:
            _bounded_data(child, depth + 1, counter)
    elif type(value) is str:
        if len(value) > 4096:
            raise PolicyPreviewError("policy_data_limit")
    elif value is not None and type(value) not in {bool, int}:
        raise PolicyPreviewError("invalid_policy_data")


def _mapping(value: Any, required: set[str] | frozenset[str], optional: set[str] | None = None) -> dict:
    if type(value) is not dict or not required <= value.keys() or value.keys() - required - (optional or set()):
        raise PolicyPreviewError("policy_fields_invalid")
    return value


def _text(value: Any, maximum: int = 200) -> str:
    if type(value) is not str or not value or len(value) > maximum or value != value.strip() or not value.isprintable():
        raise PolicyPreviewError("policy_text_invalid")
    return value


def _integer(value: Any, maximum: int = 10**15, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise PolicyPreviewError("policy_integer_invalid")
    return value


def _boolean(value: Any) -> bool:
    if type(value) is not bool:
        raise PolicyPreviewError("policy_boolean_invalid")
    return value


def _strings(value: Any, *, empty: bool = False, choices: frozenset | None = None) -> list[str]:
    if type(value) is not list or len(value) > 64 or (not value and not empty):
        raise PolicyPreviewError("policy_array_invalid")
    result = sorted(set(_text(v) for v in value))
    if choices is not None and not set(result) <= choices:
        raise PolicyPreviewError("policy_choice_invalid")
    return result


def _time(value: Any) -> datetime:
    try:
        result = datetime.fromisoformat(_text(value, 64).replace("Z", "+00:00"))
    except ValueError as exc:
        raise PolicyPreviewError("policy_time_invalid") from exc
    if result.tzinfo is None:
        raise PolicyPreviewError("policy_timezone_required")
    return result.astimezone(timezone.utc)


def _time_text(value: Any) -> str:
    return _time(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _pattern(value: str, *, path: bool = False) -> str:
    _text(value, 255)
    if value in {"*", "**", "**/*", ".", "./", "/"}:
        raise PolicyPreviewError("broad_policy_scope")
    if "\\" in value or value.startswith("/") or re.match(r"[A-Za-z]:", value):
        raise PolicyPreviewError("noncanonical_policy_scope")
    if any(p in {"", ".", ".."} for p in value.split("/")):
        raise PolicyPreviewError("noncanonical_policy_scope")
    if path and value.endswith("/"):
        raise PolicyPreviewError("noncanonical_policy_scope")
    return value


def _artifact(value: Any) -> str:
    if not _ARTIFACT.fullmatch(_text(value)):
        raise PolicyPreviewError("artifact_digest_invalid")
    return value


def normalize_policy_candidate(payload: dict[str, Any]) -> CanonicalPolicyCandidate:
    """Validate proposed data; a digest is not approval or activated authority."""
    _bounded_data(payload)
    raw = _mapping(payload, FIELDS, {"canonical_digest"})
    try:
        reject_sensitive_keys(raw)
    except TaskStoreError as exc:
        raise PolicyPreviewError("sensitive_policy_data") from exc
    if _integer(raw["schema_version"], 1, 1) != 1:
        raise PolicyPreviewError("policy_version_invalid")
    normalized: dict[str, Any] = {"schema_version": 1}
    for key in ("policy_id", "owner_identity", "owner_confirmation_event"):
        value = _text(raw[key])
        if not _ID.fullmatch(value):
            raise PolicyPreviewError("policy_identity_invalid")
        normalized[key] = value
    normalized["policy_revision"] = _integer(raw["policy_revision"], 1_000_000, 1)
    for key in ("created_at", "starts_at", "expires_at"):
        normalized[key] = _time_text(raw[key])
    created, starts, expires = (_time(normalized[k]) for k in ("created_at", "starts_at", "expires_at"))
    if not created <= starts < expires or expires - starts > MAX_WINDOW_DURATION:
        raise PolicyPreviewError("policy_time_order_invalid")
    normalized["repositories"] = _strings(raw["repositories"])
    if any(not _REPO.fullmatch(repo) for repo in normalized["repositories"]):
        raise PolicyPreviewError("policy_repository_invalid")
    for key in ("base_branches", "head_branch_patterns", "paths", "goals"):
        normalized[key] = _strings(raw[key])
        for value in normalized[key]:
            _pattern(value, path=key == "paths")
        if key in {"base_branches", "goals"} and any(any(c in v for c in "*?[") for v in normalized[key]):
            raise PolicyPreviewError("policy_exact_scope_required")
    normalized["capabilities"] = _strings(raw["capabilities"], choices=DECLARED_CAPABILITIES)
    worker = _mapping(raw["worker_delegation"], {"allowed_roles", "max_workers", "allow_in_scope_approval"})
    normalized["worker_delegation"] = {
        "allowed_roles": _strings(worker["allowed_roles"], empty=True, choices=ROLES),
        "max_workers": _integer(worker["max_workers"], 8),
        "allow_in_scope_approval": _boolean(worker["allow_in_scope_approval"]),
    }
    checks = raw["required_checks"]
    if type(checks) is not list or len(checks) > 64:
        raise PolicyPreviewError("policy_checks_invalid")
    normalized_checks = []
    for check in checks:
        item = _mapping(check, {"workflow_key", "source_app_id", "conclusion"})
        if item["conclusion"] != "success":
            raise PolicyPreviewError("policy_check_conclusion_invalid")
        normalized_checks.append({"workflow_key": _text(item["workflow_key"]),
            "source_app_id": _integer(item["source_app_id"], 10**12, 1), "conclusion": "success"})
    if len({c["workflow_key"] for c in normalized_checks}) != len(normalized_checks):
        raise PolicyPreviewError("policy_check_duplicate")
    normalized["required_checks"] = sorted(normalized_checks, key=lambda c: c["workflow_key"])
    normalized["required_review_count"] = _integer(raw["required_review_count"], 10)
    normalized["merge_methods"] = _strings(raw["merge_methods"], empty=True, choices=frozenset({"merge", "squash", "rebase"}))
    targets = raw["publication_targets"]
    if type(targets) is not list or len(targets) > 32:
        raise PolicyPreviewError("policy_targets_invalid")
    normalized_targets = []
    for target in targets:
        item = _mapping(target, {"capability", "identity", "version_patterns", "artifact_digests", "credential_refs"})
        capability = _text(item["capability"])
        if capability not in {"create_tag", "create_github_release", "publish_package", "publish_container"}:
            raise PolicyPreviewError("policy_target_capability_invalid")
        refs = _strings(item["credential_refs"], empty=True)
        if any(not _REFERENCE.fullmatch(ref) for ref in refs):
            raise PolicyPreviewError("credential_reference_invalid")
        normalized_targets.append({"capability": capability, "identity": _text(item["identity"]),
            "version_patterns": _strings(item["version_patterns"]),
            "artifact_digests": [_artifact(d) for d in _strings(item["artifact_digests"])], "credential_refs": refs})
    identities = [(t["capability"], t["identity"]) for t in normalized_targets]
    if len(set(identities)) != len(identities):
        raise PolicyPreviewError("policy_target_duplicate")
    normalized["publication_targets"] = sorted(normalized_targets, key=lambda t: (t["capability"], t["identity"]))
    normalized["deployment_environments"] = _strings(raw["deployment_environments"], empty=True)
    normalized["deployment_artifact_digests"] = [
        _artifact(d) for d in _strings(raw["deployment_artifact_digests"], empty=True)
    ]
    rollback = _mapping(raw["rollback_policy"], {"required", "allowed", "strategy", "artifact_digests"})
    normalized["rollback_policy"] = {"required": _boolean(rollback["required"]),
        "allowed": _boolean(rollback["allowed"]), "strategy": _text(rollback["strategy"]),
        "artifact_digests": [_artifact(d) for d in _strings(rollback["artifact_digests"], empty=True)]}
    budgets = _mapping(raw["operation_budgets"], frozenset(normalized["capabilities"]))
    normalized["operation_budgets"] = {k: _integer(v, 1000) for k, v in budgets.items()}
    usage = _mapping(raw["usage_budgets"], {"max_token_units", "max_cost_micro_units", "max_runtime_seconds"})
    normalized["usage_budgets"] = {k: _integer(v) for k, v in usage.items()}
    if normalized["usage_budgets"]["max_runtime_seconds"] > int((expires - starts).total_seconds()):
        raise PolicyPreviewError("policy_runtime_exceeds_window")
    retries = _mapping(raw["retry_budgets"], {"product_failure", "infrastructure_failure"})
    normalized["retry_budgets"] = {k: _integer(v, 10) for k, v in retries.items()}
    normalized["stop_conditions"] = _strings(raw["stop_conditions"], choices=STOP_CONDITIONS)
    if not MANDATORY_STOPS <= set(normalized["stop_conditions"]):
        raise PolicyPreviewError("mandatory_stop_condition_missing")
    notices = _mapping(raw["notifications"], {"on_completion", "on_blocked", "on_failure", "summary_at_expiry"})
    normalized["notifications"] = {k: _boolean(v) for k, v in notices.items()}
    digest = sha256_json(normalized)
    if "canonical_digest" in raw and raw["canonical_digest"] != digest:
        raise PolicyPreviewError("policy_digest_mismatch")
    normalized["canonical_digest"] = digest
    document = canonical_json(normalized)
    if len(document.encode("utf-8")) > 65536:
        raise PolicyPreviewError("policy_data_limit")
    return CanonicalPolicyCandidate(document, digest)


def _pattern_within(lower: str, upper: str, *, path: bool = False) -> bool:
    if lower == upper:
        return True
    if not any(c in lower for c in "*?["):
        return PurePosixPath(lower).full_match(upper) if path else fnmatchcase(lower, upper)
    # Only prove the simple descendant case; unfamiliar glob relations deny.
    if upper.endswith("/**") or upper.endswith("/*"):
        prefix = upper[:-2] if upper.endswith("/**") else upper[:-1]
        # A single-component path wildcard cannot contain descendants.
        if path and not upper.endswith("/**"):
            return False
        return lower.startswith(prefix) and not any(c in prefix for c in "*?[")
    return False


def _within_authority(policy: dict, upper: dict) -> bool:
    for key in ("repositories", "base_branches", "goals", "capabilities", "merge_methods", "deployment_environments", "deployment_artifact_digests"):
        if not set(policy[key]) <= set(upper[key]):
            return False
    for key in ("head_branch_patterns", "paths"):
        if any(not any(_pattern_within(p, u, path=key == "paths") for u in upper[key]) for p in policy[key]):
            return False
    if policy["owner_identity"] != upper["owner_identity"]:
        return False
    if _time(policy["starts_at"]) < _time(upper["starts_at"]) or _time(policy["expires_at"]) > _time(upper["expires_at"]):
        return False
    for key in ("operation_budgets", "usage_budgets", "retry_budgets"):
        if any(v > upper[key].get(k, -1) for k, v in policy[key].items()):
            return False
    worker, upstream = policy["worker_delegation"], upper["worker_delegation"]
    if not set(worker["allowed_roles"]) <= set(upstream["allowed_roles"]) or worker["max_workers"] > upstream["max_workers"]:
        return False
    if worker["allow_in_scope_approval"] and not upstream["allow_in_scope_approval"]:
        return False
    if policy["required_review_count"] < upper["required_review_count"] or not set(upper["stop_conditions"]) <= set(policy["stop_conditions"]):
        return False
    lower_checks = {c["workflow_key"]: c for c in policy["required_checks"]}
    if any(lower_checks.get(c["workflow_key"]) != c for c in upper["required_checks"]):
        return False
    upper_targets = {(t["capability"], t["identity"]): t for t in upper["publication_targets"]}
    for target in policy["publication_targets"]:
        other = upper_targets.get((target["capability"], target["identity"]))
        if other is None or any(not set(target[k]) <= set(other[k]) for k in ("artifact_digests", "credential_refs")):
            return False
        if any(not any(_pattern_within(p, u) for u in other["version_patterns"]) for p in target["version_patterns"]):
            return False
    lower_rb, upper_rb = policy["rollback_policy"], upper["rollback_policy"]
    if lower_rb["allowed"] and not upper_rb["allowed"] or upper_rb["required"] and not lower_rb["required"]:
        return False
    if lower_rb["strategy"] != upper_rb["strategy"] or not set(lower_rb["artifact_digests"]) <= set(upper_rb["artifact_digests"]):
        return False
    return True


def preview_policy_operation(
    payload: dict[str, Any], *, request: dict[str, Any], upper_authority: dict[str, Any],
    observations: dict[str, Any], supported_operations: frozenset[str], now: datetime,
) -> PolicyPreviewResult:
    """Simulate one request under two declared policies; never authorize it."""
    digest = ""
    def result(reason: str, eligible: bool = False) -> PolicyPreviewResult:
        return PolicyPreviewResult(eligible, reason, digest)
    try:
        candidate = normalize_policy_candidate(payload)
        digest = candidate.canonical_digest
        policy = candidate.document()
        upper = normalize_policy_candidate(upper_authority).document()
        if not isinstance(now, datetime) or now.tzinfo is None:
            return result("observation_time_invalid")
        now = now.astimezone(timezone.utc)
        _bounded_data(request)
        _bounded_data(observations)
        _mapping(request, {"operation", "repository", "base_branch", "head_branch", "paths", "goal_id", "estimated_usage"},
            {"head_sha", "actor_identity", "worker_role", "merge_method", "publication_identity", "version", "artifact_digest", "credential_refs", "environment", "rollback_artifact_digest", "retry_kind"})
        _mapping(observations, {"active_policy", "active_upper_authority", "policy_usage", "upper_usage", "stop_signals"},
            {"head_sha", "checks", "reviews", "workers_active", "merge_state"})
        for current, observation, prefix in (
            (policy, observations["active_policy"], "policy"),
            (upper, observations["active_upper_authority"], "upper_authority"),
        ):
            active = _mapping(observation, {"policy_id", "policy_revision", "canonical_digest", "state"})
            if active["state"] != "ACTIVE":
                return result(prefix + "_inactive")
            if any(active[k] != current[k] or type(active[k]) is not type(current[k]) for k in ("policy_id", "policy_revision", "canonical_digest")):
                return result(prefix + "_identity_mismatch")
        for current in (policy, upper):
            if now < _time(current["created_at"]) or now < _time(current["starts_at"]):
                return result("policy_not_started")
            if now >= _time(current["expires_at"]):
                return result("policy_expired")
        if not _within_authority(policy, upper):
            return result("authority_expansion")
        signals = _strings(observations["stop_signals"], empty=True, choices=STOP_CONDITIONS)
        if set(signals) & (set(policy["stop_conditions"]) | set(upper["stop_conditions"])):
            return result("stop_condition_observed")
        operation = _text(request["operation"])
        if operation not in policy["capabilities"] or operation not in upper["capabilities"]:
            return result("capability_outside_policy")
        for key, scope in (("repository", "repositories"), ("base_branch", "base_branches"), ("goal_id", "goals")):
            if _text(request[key]) not in policy[scope] or request[key] not in upper[scope]:
                return result("request_outside_scope")
        branch = _pattern(_text(request["head_branch"]))
        if any(c in branch for c in "*?[") or not all(any(fnmatchcase(branch, pattern) for pattern in p["head_branch_patterns"]) for p in (policy, upper)):
            return result("request_outside_scope")
        paths = _strings(request["paths"], empty=True)
        if operation in {"modify_approved_paths", "modify_project"} and not paths:
            return result("changed_paths_required")
        for path in paths:
            _pattern(path, path=True)
            if any(c in path for c in "*?[") or not all(any(PurePosixPath(path).full_match(pattern) for pattern in p["paths"]) for p in (policy, upper)):
                return result("request_outside_scope")
        role = request.get("worker_role")
        if operation in {"spawn_worker", "approve_worker_low_risk", "approve_worker_in_scope"} and role is None:
            return result("worker_outside_scope")
        if role is not None and (role not in policy["worker_delegation"]["allowed_roles"] or role not in upper["worker_delegation"]["allowed_roles"]):
            return result("worker_outside_scope")
        if operation in {"approve_worker_low_risk", "approve_worker_in_scope"} and not all(p["worker_delegation"]["allow_in_scope_approval"] for p in (policy, upper)):
            return result("worker_approval_unavailable")
        if role is not None or operation == "spawn_worker":
            count = _integer(observations.get("workers_active"), 1000)
            if count >= min(p["worker_delegation"]["max_workers"] for p in (policy, upper)):
                return result("worker_budget_exceeded")
        head = request.get("head_sha")
        if head is not None and (type(head) is not str or not _OID.fullmatch(head)):
            return result("head_identity_invalid")
        bound_operations = {"merge_pr", "mark_ready", "push_main", "create_tag", "create_github_release", "publish_package", "publish_container", "deploy_preview", "deploy_staging", "deploy_production", "rollback_deployment"}
        if policy["required_checks"] or policy["required_review_count"] or operation in bound_operations:
            if head is None or observations.get("head_sha") != head:
                return result("head_identity_mismatch")
        checks = observations.get("checks", [])
        if type(checks) is not list:
            return result("checks_invalid")
        check_map = {}
        for item in checks:
            _mapping(item, {"workflow_key", "source_app_id", "head_sha", "conclusion"})
            key = _text(item["workflow_key"])
            if key in check_map:
                return result("checks_conflicting")
            check_map[key] = item
        for expected in policy["required_checks"]:
            actual = check_map.get(expected["workflow_key"])
            if actual is None or actual["head_sha"] != head or type(actual["source_app_id"]) is not int or actual["source_app_id"] != expected["source_app_id"] or actual["conclusion"] != "success":
                return result("required_check_unsatisfied")
        reviews = observations.get("reviews", [])
        if type(reviews) is not list:
            return result("reviews_invalid")
        accepted = set()
        actor = request.get("actor_identity")
        if policy["required_review_count"] and (type(actor) is not str or not actor):
            return result("review_actor_identity_missing")
        for review in reviews:
            _mapping(review, {"head_sha", "reviewer_identity", "accepted"})
            identity = _text(review["reviewer_identity"])
            if _boolean(review["accepted"]) and review["head_sha"] == head and identity != actor:
                accepted.add(identity)
        if len(accepted) < policy["required_review_count"]:
            return result("required_review_unsatisfied")
        if operation == "merge_pr":
            if request.get("merge_method") not in policy["merge_methods"] or policy["required_review_count"] < 1 or actor is None:
                return result("merge_constraints_unsatisfied")
            if observations.get("merge_state") != "CLEAN":
                return result("merge_constraints_unsatisfied")
        if operation in {"create_tag", "create_github_release", "publish_package", "publish_container"}:
            targets = [t for t in policy["publication_targets"] if t["capability"] == operation and t["identity"] == request.get("publication_identity")]
            if len(targets) != 1:
                return result("publication_target_mismatch")
            target = targets[0]
            if request.get("artifact_digest") not in target["artifact_digests"]:
                return result("artifact_identity_mismatch")
            if not any(fnmatchcase(_text(request.get("version")), pattern) for pattern in target["version_patterns"]):
                return result("publication_version_mismatch")
            refs = _strings(request.get("credential_refs", []), empty=True)
            if not set(refs) <= set(target["credential_refs"]):
                return result("credential_reference_outside_scope")
        if operation.startswith("deploy_") or operation == "rollback_deployment":
            if request.get("environment") not in policy["deployment_environments"]:
                return result("deployment_environment_mismatch")
            rb = policy["rollback_policy"]
            if (rb["required"] or operation == "rollback_deployment") and (not rb["allowed"] or request.get("rollback_artifact_digest") not in rb["artifact_digests"]):
                return result("rollback_constraints_unsatisfied")
            if request.get("artifact_digest") not in policy["deployment_artifact_digests"]:
                return result("artifact_identity_mismatch")
        estimate = _mapping(request["estimated_usage"], {"token_units", "cost_micro_units", "runtime_seconds"})
        for key in estimate:
            if estimate[key] is None:
                return result("usage_estimate_unknown")
            _integer(estimate[key])
        for current, usage in ((policy, observations["policy_usage"]), (upper, observations["upper_usage"])):
            _mapping(usage, {"operation_counts", "token_units", "cost_micro_units", "runtime_seconds", "retry_counts"})
            counts = usage["operation_counts"]
            if type(counts) is not dict or operation not in counts or counts[operation] is None:
                return result("operation_usage_unknown")
            if _integer(counts[operation]) >= current["operation_budgets"][operation]:
                return result("operation_budget_exceeded")
            for key, limit in (("token_units", "max_token_units"), ("cost_micro_units", "max_cost_micro_units"), ("runtime_seconds", "max_runtime_seconds")):
                if usage[key] is None:
                    return result("usage_observation_unknown")
                if _integer(usage[key]) + estimate[key] > current["usage_budgets"][limit]:
                    return result("usage_budget_exceeded")
            retry = request.get("retry_kind")
            if retry is not None:
                if retry not in current["retry_budgets"]:
                    return result("retry_kind_invalid")
                retries = usage["retry_counts"]
                if type(retries) is not dict or retry not in retries or retries[retry] is None:
                    return result("retry_usage_unknown")
                if _integer(retries[retry]) >= current["retry_budgets"][retry]:
                    return result("retry_budget_exceeded")
        # The current adapters provide only these existing operations. Metadata
        # for future capabilities cannot make a privileged backend available.
        if operation not in KNOWN_OPERATIONS or operation not in supported_operations:
            return result("backend_capability_unavailable")
        return result("preview_conditions_satisfied", True)
    except (PolicyPreviewError, TypeError, KeyError, ValueError):
        return result("invalid_preview_data")
