"""Policy-data previews use declared fixtures, never actual authority or CI."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.autonomy_policy_preview import (
    DECLARED_CAPABILITIES, MANDATORY_STOPS, PolicyPreviewError,
    normalize_policy_candidate, preview_policy_operation,
)
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry


NOW = datetime(2026, 10, 3, 0, 30, tzinfo=timezone.utc)
HEAD = "a" * 40
ARTIFACT = "sha256:" + "b" * 64


def policy():
    return {
        "schema_version": 1, "policy_id": "policy.alpha", "policy_revision": 1,
        "owner_identity": "owner.dddd2024", "owner_confirmation_event": "declared:event.1",
        "created_at": "2026-10-02T23:55:00Z", "starts_at": "2026-10-03T00:00:00Z",
        "expires_at": "2026-10-03T03:00:00Z", "repositories": ["dddd2024/Nerelan"],
        "base_branches": ["main"], "head_branch_patterns": ["codex/*"],
        "paths": ["reverse_agent/platform_v1/**"], "goals": ["goal-alpha"],
        "capabilities": ["execute_task"],
        "worker_delegation": {"allowed_roles": ["coder", "reviewer"], "max_workers": 2, "allow_in_scope_approval": False},
        "required_checks": [{"workflow_key": "CI", "source_app_id": 15368, "conclusion": "success"}],
        "required_review_count": 1, "merge_methods": ["merge"], "publication_targets": [],
        "deployment_environments": ["staging"], "deployment_artifact_digests": [ARTIFACT],
        "rollback_policy": {"required": True, "allowed": True, "strategy": "previous_artifact", "artifact_digests": [ARTIFACT]},
        "operation_budgets": {"execute_task": 2},
        "usage_budgets": {"max_token_units": 1000, "max_cost_micro_units": 10000, "max_runtime_seconds": 3600},
        "retry_budgets": {"product_failure": 1, "infrastructure_failure": 2},
        "stop_conditions": sorted(MANDATORY_STOPS),
        "notifications": {"on_completion": True, "on_blocked": True, "on_failure": True, "summary_at_expiry": True},
    }


def request(operation="execute_task"):
    return {"operation": operation, "repository": "dddd2024/Nerelan", "base_branch": "main",
        "head_branch": "codex/work", "paths": ["reverse_agent/platform_v1/example.py"],
        "goal_id": "goal-alpha", "head_sha": HEAD, "actor_identity": "controller",
        "estimated_usage": {"token_units": 10, "cost_micro_units": 100, "runtime_seconds": 1}}


def observations(p, upper):
    def active(item):
        candidate = normalize_policy_candidate(item).document()
        return {**{k: candidate[k] for k in ("policy_id", "policy_revision", "canonical_digest")}, "state": "ACTIVE"}
    def usage(item):
        return {"operation_counts": {op: 0 for op in item["capabilities"]}, "token_units": 0,
            "cost_micro_units": 0, "runtime_seconds": 0,
            "retry_counts": {"product_failure": 0, "infrastructure_failure": 0}}
    return {"active_policy": active(p), "active_upper_authority": active(upper),
        "policy_usage": usage(p), "upper_usage": usage(upper), "stop_signals": [], "head_sha": HEAD,
        "checks": [{"workflow_key": "CI", "source_app_id": 15368, "head_sha": HEAD, "conclusion": "success"}],
        "reviews": [{"head_sha": HEAD, "reviewer_identity": "declared.auditor", "accepted": True}], "workers_active": 0}


def preview(p=None, *, req=None, upper=None, obs=None, now=NOW, available=None):
    p = policy() if p is None else p
    upper = deepcopy(p) if upper is None else upper
    return preview_policy_operation(p, request=request() if req is None else req, upper_authority=upper,
        observations=observations(p, upper) if obs is None else obs,
        supported_operations=frozenset({"execute_task"}) if available is None else available, now=now)


def test_preview_never_authenticates_declared_confirmation_or_grants_execution():
    value = preview()
    assert value.eligible and value.reason == "preview_conditions_satisfied"
    assert value.to_dict()["execution_authorized"] is False
    assert value.to_dict()["owner_confirmation_verified"] is False
    assert value.to_dict()["upper_authority_verified"] is False
    with pytest.raises(FrozenInstanceError):
        value.execution_authorized = True


def test_canonical_data_is_copy_isolated_order_invariant_and_digest_bound():
    p = policy()
    p["goals"] = ["goal-beta", "goal-alpha"]
    p["paths"] = ["tests/**", "reverse_agent/platform_v1/**"]
    original = deepcopy(p)
    candidate = normalize_policy_candidate(p)
    reordered = dict(reversed(list(p.items())))
    reordered["goals"] = ["goal-alpha", "goal-beta", "goal-alpha"]
    reordered["paths"] = list(reversed(p["paths"]))
    assert normalize_policy_candidate(reordered) == candidate
    assert p == original
    document = candidate.document()
    document["paths"].append("frontend/**")
    assert candidate.document()["paths"] == sorted(original["paths"])
    assert normalize_policy_candidate(candidate.document()) == candidate
    p["notifications"]["on_failure"] = False
    assert normalize_policy_candidate(p).canonical_digest != candidate.canonical_digest
    changed = candidate.document()
    changed["owner_confirmation_event"] = "declared:event.2"
    with pytest.raises(PolicyPreviewError, match="policy_digest_mismatch"):
        normalize_policy_candidate(changed)


def test_equivalent_timezones_preserve_digest_and_subsecond_boundary():
    p = policy()
    p["starts_at"] = "2026-10-03T00:30:00.000001Z"
    equivalent = deepcopy(p)
    equivalent["starts_at"] = "2026-10-03T08:30:00.000001+08:00"
    assert normalize_policy_candidate(p) == normalize_policy_candidate(equivalent)
    assert preview(p, now=NOW).reason == "policy_not_started"
    assert preview(p, now=NOW + timedelta(microseconds=1)).eligible
    assert preview(p, now=datetime(2026, 10, 3, 3, tzinfo=timezone.utc)).reason == "policy_expired"


@pytest.mark.parametrize("field,value", [
    ("schema_version", True), ("schema_version", 2), ("policy_revision", 0),
    ("policy_revision", "1"), ("owner_identity", " owner"), ("repositories", ["*"]),
    ("paths", ["**"]), ("paths", ["../private"]), ("paths", ["C:/private"]),
    ("paths", ["safe/../../private"]), ("paths", ["safe\\file.py"]),
    ("paths", ["safe//file.py"]), ("base_branches", ["*"]),
    ("capabilities", ["full_access"]), ("created_at", "2026-10-02T23:55:00"),
    ("expires_at", "2026-10-11T00:00:00Z"), ("required_review_count", True),
    ("canonical_digest", "0" * 64),
])
def test_invalid_policy_data_cannot_become_candidate(field, value):
    p = policy(); p[field] = value
    with pytest.raises(PolicyPreviewError):
        normalize_policy_candidate(p)


@pytest.mark.parametrize("section,key,value", [
    ("usage_budgets", "max_token_units", True),
    ("usage_budgets", "max_cost_micro_units", -1),
    ("usage_budgets", "max_runtime_seconds", 10801),
    ("operation_budgets", "execute_task", 1001),
    ("retry_budgets", "product_failure", 11),
    ("worker_delegation", "max_workers", 9),
    ("worker_delegation", "allow_in_scope_approval", "true"),
    ("notifications", "on_failure", 1),
])
def test_budget_and_boolean_types_are_strict(section, key, value):
    p = policy(); p[section][key] = value
    with pytest.raises(PolicyPreviewError):
        normalize_policy_candidate(p)


def test_unknown_or_secret_shaped_fields_and_recursive_data_are_rejected():
    for key in ("full_access", "api_key"):
        p = policy(); p[key] = "PRIVATE_SENTINEL"
        with pytest.raises(PolicyPreviewError) as raised:
            normalize_policy_candidate(p)
        assert "PRIVATE_SENTINEL" not in str(raised.value)
    p = policy(); p["notifications"]["password"] = "PRIVATE_SENTINEL"
    with pytest.raises(PolicyPreviewError) as raised:
        normalize_policy_candidate(p)
    assert "PRIVATE_SENTINEL" not in str(raised.value)
    recursive = {}; recursive["self"] = recursive
    with pytest.raises(PolicyPreviewError, match="policy_data_limit"):
        normalize_policy_candidate(recursive)
    p = policy(); p["goals"] = ["goal-alpha"] * 129
    with pytest.raises(PolicyPreviewError):
        normalize_policy_candidate(p)


def test_mandatory_stop_conditions_cannot_be_disabled():
    p = policy(); p["stop_conditions"].remove("secret_exposure")
    with pytest.raises(PolicyPreviewError, match="mandatory_stop_condition_missing"):
        normalize_policy_candidate(p)
    p = policy(); upper = deepcopy(p); obs = observations(p, upper)
    obs["stop_signals"] = ["secret_exposure"]
    assert preview(p, upper=upper, obs=obs).reason == "stop_condition_observed"


@pytest.mark.parametrize("bound", ["active_policy", "active_upper_authority"])
@pytest.mark.parametrize("key,value", [("state", "REVOKED"), ("policy_revision", 2),
    ("policy_revision", True), ("canonical_digest", "0" * 64), ("policy_id", "other.policy")])
def test_revoked_or_stale_policy_and_upstream_observations_deny(bound, key, value):
    p = policy(); upper = deepcopy(p); obs = observations(p, upper); obs[bound][key] = value
    result = preview(p, upper=upper, obs=obs)
    assert not result.eligible and result.reason.endswith(("_inactive", "_identity_mismatch"))
    assert not result.execution_authorized


@pytest.mark.parametrize("field,value", [("repository", "other/repo"), ("base_branch", "release"),
    ("head_branch", "owner/work"), ("goal_id", "goal-other"),
    ("paths", ["reverse_agent/platform_v1/file.py", "credentials/data"]),
    ("operation", "open_draft_pr")])
def test_request_scope_is_intersected_with_both_policies(field, value):
    req = request(); req[field] = value
    assert not preview(req=req).eligible


def test_path_wildcards_are_component_sensitive_and_not_proof_by_prefix():
    p = policy(); p["paths"] = ["reverse_agent/platform_v1/*"]
    req = request(); req["paths"] = ["reverse_agent/platform_v1/nested/file.py"]
    assert preview(p, req=req).reason == "request_outside_scope"
    upper = policy(); upper["paths"] = ["reverse_agent/*/safe/**"]
    p = policy(); p["paths"] = ["reverse_agent/**"]
    assert preview(p, upper=upper).reason == "authority_expansion"
    upper = policy(); p = policy(); p["paths"] = ["reverse_agent/platform_v1/nested/**"]
    req = request(); req["paths"] = ["reverse_agent/platform_v1/nested/file.py"]
    assert preview(p, req=req, upper=upper).eligible


@pytest.mark.parametrize("change", ["repository", "goal", "path", "capability", "budget", "review", "check", "worker", "rollback"])
def test_candidate_cannot_expand_or_relax_upstream_authority(change):
    upper = policy(); p = deepcopy(upper)
    if change == "repository": p["repositories"].append("other/repo")
    if change == "goal": p["goals"].append("goal-other")
    if change == "path": p["paths"].append("frontend/**")
    if change == "capability":
        p["capabilities"].append("open_draft_pr"); p["operation_budgets"]["open_draft_pr"] = 1
    if change == "budget": p["usage_budgets"]["max_token_units"] += 1
    if change == "review": p["required_review_count"] = 0
    if change == "check": p["required_checks"] = []
    if change == "worker": p["worker_delegation"]["allow_in_scope_approval"] = True
    if change == "rollback": p["rollback_policy"]["required"] = False
    assert preview(p, upper=upper).reason == "authority_expansion"


@pytest.mark.parametrize("change,reason", [
    ("head", "head_identity_mismatch"), ("check_head", "required_check_unsatisfied"),
    ("app", "required_check_unsatisfied"), ("conclusion", "required_check_unsatisfied"),
    ("duplicate", "checks_conflicting"), ("review_head", "required_review_unsatisfied"),
    ("self_review", "required_review_unsatisfied"), ("missing_actor", "review_actor_identity_missing"),
])
def test_check_and_review_declarations_bind_exact_head_and_declared_actor(change, reason):
    p = policy(); upper = deepcopy(p); obs = observations(p, upper); req = request()
    if change == "head": obs["head_sha"] = "c" * 40
    if change == "check_head": obs["checks"][0]["head_sha"] = "c" * 40
    if change == "app": obs["checks"][0]["source_app_id"] = 1
    if change == "conclusion": obs["checks"][0]["conclusion"] = "skipped"
    if change == "duplicate": obs["checks"].append(deepcopy(obs["checks"][0]))
    if change == "review_head": obs["reviews"][0]["head_sha"] = "c" * 40
    if change == "self_review": obs["reviews"][0]["reviewer_identity"] = "controller"
    if change == "missing_actor": del req["actor_identity"]
    assert preview(p, req=req, upper=upper, obs=obs).reason == reason


def test_duplicate_review_identity_is_not_two_reviews():
    p = policy(); p["required_review_count"] = 2; upper = deepcopy(p); obs = observations(p, upper)
    obs["reviews"].append(deepcopy(obs["reviews"][0]))
    assert preview(p, upper=upper, obs=obs).reason == "required_review_unsatisfied"


@pytest.mark.parametrize("bound", ["policy_usage", "upper_usage"])
@pytest.mark.parametrize("field,value,reason", [
    ("token_units", None, "usage_observation_unknown"),
    ("cost_micro_units", None, "usage_observation_unknown"),
    ("runtime_seconds", None, "usage_observation_unknown"),
    ("token_units", 991, "usage_budget_exceeded"),
    ("cost_micro_units", 9901, "usage_budget_exceeded"),
    ("runtime_seconds", 3600, "usage_budget_exceeded"),
    ("token_units", True, "invalid_preview_data"),
])
def test_known_projected_usage_is_required_for_each_budget(bound, field, value, reason):
    p = policy(); upper = deepcopy(p); obs = observations(p, upper); obs[bound][field] = value
    assert preview(p, upper=upper, obs=obs).reason == reason


def test_budget_boundary_missing_counts_and_unknown_estimates_fail_closed():
    p = policy(); upper = deepcopy(p); obs = observations(p, upper)
    obs["policy_usage"]["token_units"] = 990
    obs["policy_usage"]["operation_counts"]["execute_task"] = 1
    assert preview(p, upper=upper, obs=obs).eligible
    obs["policy_usage"]["operation_counts"]["execute_task"] = 2
    assert preview(p, upper=upper, obs=obs).reason == "operation_budget_exceeded"
    del obs["policy_usage"]["operation_counts"]["execute_task"]
    assert preview(p, upper=upper, obs=obs).reason == "operation_usage_unknown"
    req = request(); req["estimated_usage"]["token_units"] = None
    assert preview(req=req).reason == "usage_estimate_unknown"


@pytest.mark.parametrize("bound", ["policy_usage", "upper_usage"])
def test_retry_count_is_bounded_and_unknown_is_not_zero(bound):
    p = policy(); upper = deepcopy(p); obs = observations(p, upper); req = request()
    req["retry_kind"] = "product_failure"
    assert preview(p, req=req, upper=upper, obs=obs).eligible
    obs[bound]["retry_counts"]["product_failure"] = 1
    assert preview(p, req=req, upper=upper, obs=obs).reason == "retry_budget_exceeded"
    obs[bound]["retry_counts"]["product_failure"] = None
    assert preview(p, req=req, upper=upper, obs=obs).reason == "retry_usage_unknown"


def test_worker_scope_and_concurrency_are_checked_without_spawning():
    req = request(); req["worker_role"] = "publisher"
    assert preview(req=req).reason == "worker_outside_scope"
    req["worker_role"] = "coder"; p = policy(); upper = deepcopy(p); obs = observations(p, upper)
    assert preview(p, req=req, upper=upper, obs=obs).eligible
    obs["workers_active"] = 2
    assert preview(p, req=req, upper=upper, obs=obs).reason == "worker_budget_exceeded"


def privileged_policy(operation):
    p = policy(); p["capabilities"].append(operation); p["operation_budgets"][operation] = 1
    if operation in {"create_tag", "create_github_release", "publish_package", "publish_container"}:
        p["publication_targets"] = [{"capability": operation, "identity": "approved.package",
            "version_patterns": ["v1.*"], "artifact_digests": [ARTIFACT], "credential_refs": ["vault:publication"]}]
    req = request(operation)
    req.update(merge_method="merge", publication_identity="approved.package", version="v1.2",
        artifact_digest=ARTIFACT, credential_refs=["vault:publication"], environment="staging",
        rollback_artifact_digest=ARTIFACT)
    upper = deepcopy(p); obs = observations(p, upper); obs["merge_state"] = "CLEAN"
    return p, req, upper, obs


@pytest.mark.parametrize("operation", ["merge_pr", "mark_ready", "push_main", "create_tag",
    "create_github_release", "publish_package", "publish_container", "deploy_preview",
    "deploy_staging", "deploy_production", "rollback_deployment", "delete_merged_branch"])
def test_future_privileged_capabilities_remain_unavailable_even_with_declared_success(operation):
    p, req, upper, obs = privileged_policy(operation)
    result = preview(p, req=req, upper=upper, obs=obs, available=DECLARED_CAPABILITIES)
    assert result.reason == "backend_capability_unavailable"
    assert not result.eligible and not result.execution_authorized


@pytest.mark.parametrize("field,value,reason", [
    ("publication_identity", "other.package", "publication_target_mismatch"),
    ("version", "v2.0", "publication_version_mismatch"),
    ("artifact_digest", "sha256:" + "c" * 64, "artifact_identity_mismatch"),
    ("credential_refs", ["vault:other"], "credential_reference_outside_scope"),
])
def test_publication_identity_version_artifact_and_reference_scope(field, value, reason):
    p, req, upper, obs = privileged_policy("publish_package"); req[field] = value
    assert preview(p, req=req, upper=upper, obs=obs).reason == reason


@pytest.mark.parametrize("field,value,reason", [
    ("environment", "production", "deployment_environment_mismatch"),
    ("artifact_digest", "sha256:" + "c" * 64, "artifact_identity_mismatch"),
    ("rollback_artifact_digest", "sha256:" + "c" * 64, "rollback_constraints_unsatisfied"),
])
def test_deployment_and_rollback_bind_approved_artifacts(field, value, reason):
    p, req, upper, obs = privileged_policy("deploy_staging"); req[field] = value
    assert preview(p, req=req, upper=upper, obs=obs).reason == reason


def test_raw_credentials_are_not_accepted_as_references():
    p, _, _, _ = privileged_policy("publish_package")
    p["publication_targets"][0]["credential_refs"] = ["sk-PRIVATE_SENTINEL"]
    with pytest.raises(PolicyPreviewError) as raised:
        normalize_policy_candidate(p)
    assert "PRIVATE_SENTINEL" not in str(raised.value)


def test_service_preview_never_calls_store_or_mutates_input_and_usage():
    class NoStoreAccess:
        def __getattr__(self, name):
            raise AssertionError("preview must not access the store")
    p = policy(); upper = deepcopy(p); obs = observations(p, upper); req = request()
    before = deepcopy((p, upper, obs, req))
    service = AutonomyService(control_store=NoStoreAccess(), capabilities=CapabilityRegistry())
    result = service.preview(p, request=req, upper_authority=upper, observations=obs, now=NOW)
    assert result["eligible"] and not result["execution_authorized"]
    assert (p, upper, obs, req) == before
    assert service.preview(p, request=req, upper_authority=upper, observations=obs, now=NOW) == result


def test_unavailable_existing_backend_and_malformed_observations_are_denied():
    assert preview(available=frozenset()).reason == "backend_capability_unavailable"
    p = policy(); upper = deepcopy(p); obs = observations(p, upper)
    del obs["active_upper_authority"]
    assert preview(p, upper=upper, obs=obs).reason == "invalid_preview_data"
    assert not preview(now=NOW.replace(tzinfo=None)).eligible
