"""Owner-activated autonomous execution windows and server-side policy checks."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any, Mapping

from .capability_registry import CapabilityRegistry
from .control_store import AutonomousWindowRecord, PlatformControlStore
from .run_store import TaskStoreError


MAX_WINDOW_DURATION = timedelta(days=7)
# A standing policy renews windows of at most MAX_WINDOW_DURATION each, never
# beyond this horizon from its Owner activation (Governance v2.1 D, #1310).
MAX_STANDING_HORIZON = timedelta(days=90)
KNOWN_OPERATIONS = frozenset(
    {"execute_task", "resume_task", "reconcile_task", "validate_task", "open_draft_pr", "approve_goal", "land_reviewed_pr"}
)


def goal_admission_snapshots(binding: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Exact host-authorized snapshots in the existing immutable binding."""
    if "goal_admissions" not in binding:
        return ()
    values = binding["goal_admissions"]
    if not isinstance(values, list) or not 1 <= len(values) <= 100:
        raise TaskStoreError("delegated_goal_admissions_invalid")
    snapshots = []
    for value in values:
        if not isinstance(value, dict) or set(value) != {"goal_id", "revision", "artifact_digest", "idempotency_key"}:
            raise TaskStoreError("delegated_goal_snapshot_invalid")
        if (any(not isinstance(value[key], str) or not re.fullmatch(r"[A-Za-z0-9._:-]{3,160}", value[key])
                for key in ("goal_id", "idempotency_key"))
                or type(value["revision"]) is not int or not 1 <= value["revision"] <= 1_000_000
                or not isinstance(value["artifact_digest"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", value["artifact_digest"])):
            raise TaskStoreError("delegated_goal_snapshot_invalid")
        snapshots.append(dict(value))
    for key in ("goal_id", "idempotency_key"):
        if len({value[key] for value in snapshots}) != len(snapshots):
            raise TaskStoreError("delegated_goal_snapshot_duplicate")
    return tuple(snapshots)


def bound_goal_admission(binding: Mapping[str, Any], goal: Any) -> dict[str, Any] | None:
    snapshots = goal_admission_snapshots(binding)
    if not snapshots:
        return None
    for value in snapshots:
        if value["goal_id"] == goal.id:
            if (value["revision"] != goal.revision or value["artifact_digest"] != goal.artifact_digest
                    or value["idempotency_key"] != goal.idempotency_key):
                raise TaskStoreError("delegated_goal_snapshot_mismatch")
            return value
    raise TaskStoreError("delegated_goal_outside_scope")

GITHUB_POLICY_CAPABILITIES = frozenset({
    "read_repository", "create_issue", "update_issue", "create_branch",
    "push_task_branch", "open_draft_pr", "mark_ready", "request_review",
    "merge_pr", "delete_merged_branch", "push_main",
})
PUBLICATION_POLICY_CAPABILITIES = frozenset({
    "create_tag", "create_github_release", "publish_package", "publish_container",
    "deploy_preview", "deploy_staging", "deploy_production", "rollback_deployment",
})
STOP_CONDITIONS = frozenset({
    "max_prs_opened", "max_merges_to_main", "max_releases_created",
    "max_deploys_to_environment", "budget_exhausted", "window_expired",
    "manual_stop", "blocking_review_thread", "ci_failure_on_head",
    "main_drift_detected", "authority_revoked",
})
_CAP_FIELDS = ("maxPrsOpened", "maxMergesToMain", "maxReleasesCreated", "maxDeploysToEnvironment")


def canonical_policy_json(policy: Mapping[str, Any]) -> str:
    return json.dumps(policy, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def policy_digest(policy: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_policy_json(policy).encode("utf-8")).hexdigest()


def _policy_object(value: Any, required: set[str], optional: set[str] | None = None) -> Mapping[str, Any]:
    if (not isinstance(value, Mapping) or not required <= set(value)
            or set(value) - required - (optional or set())):
        raise TaskStoreError("canonical_policy_fields_invalid")
    return value


def _policy_strings(value: Any, *, choices: frozenset[str] | None = None) -> list[str]:
    if (not isinstance(value, list) or len(value) > 100
            or any(not isinstance(item, str) or not item or item != item.strip()
                   or len(item) > 240 or any(ord(char) < 32 for char in item) for item in value)
            or len(set(value)) != len(value)
            or (choices is not None and any(item not in choices for item in value))):
        raise TaskStoreError("canonical_policy_array_invalid")
    return value


def _policy_int(value: Any, *, maximum: int = 1_000_000) -> int:
    if type(value) is not int or not 0 <= value <= maximum:
        raise TaskStoreError("canonical_policy_integer_invalid")
    return value


def validate_canonical_policy(value: Any, *, now: datetime | None = None) -> dict[str, Any]:
    """Validate every canonical field; selected unavailable adapters are explicit.

    This phase supports the host's fixed checker, not arbitrary filesystem,
    shell, network or editing privileges. Inactive capability metadata remains
    in the original canonical object; nothing is silently dropped/defaulted.
    """
    policy = _policy_object(value, {"mode", "repository", "resourceAccess",
        "githubCapabilities", "publicationCapabilities", "publicationPolicy",
        "mergePolicy", "autonomousWindow", "budgets"})
    if (not isinstance(policy["mode"], str)
            or policy["mode"] not in {"ASK_FOR_APPROVAL", "CONTROLLER_REVIEW", "OWNER_CONTROL", "CUSTOM"}):
        raise TaskStoreError("canonical_policy_mode_invalid")
    if (not isinstance(policy["repository"], str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", policy["repository"])):
        raise TaskStoreError("canonical_policy_repository_invalid")
    resource = _policy_object(policy["resourceAccess"],
        {"filesystem", "network", "shell", "secrets", "workerApproval"})
    filesystem = _policy_object(resource["filesystem"], {"allowedPaths", "writablePaths"}, {"tempDir"})
    for name in ("allowedPaths", "writablePaths"):
        for path in _policy_strings(filesystem[name]):
            if ("\\" in path or ":" in path or path.startswith("/")
                    or any(part in {"", ".", ".."} for part in path.split("/"))
                    or str(PurePosixPath(path)) != path or any(char in path for char in "*?[]")):
                raise TaskStoreError("canonical_policy_path_invalid")
    if filesystem["writablePaths"] or "tempDir" in filesystem:
        raise TaskStoreError("canonical_policy_filesystem_write_unsupported")
    network = _policy_object(resource["network"], {"allowedDomains", "allowWrite"})
    domains = _policy_strings(network["allowedDomains"])
    if type(network["allowWrite"]) is not bool:
        raise TaskStoreError("canonical_policy_boolean_invalid")
    if domains or network["allowWrite"]:
        raise TaskStoreError("canonical_policy_network_unsupported")
    shell = _policy_object(resource["shell"], {"allowedCommands", "deniedCommands"})
    allowed_commands = _policy_strings(shell["allowedCommands"])
    denied_commands = _policy_strings(shell["deniedCommands"])
    if (not allowed_commands or any(command != "git_diff_check" for command in allowed_commands)
            or set(allowed_commands) & set(denied_commands)):
        raise TaskStoreError("canonical_policy_checker_unsupported")
    secrets = _policy_object(resource["secrets"], {"access", "allowedKeys"})
    _policy_strings(secrets["allowedKeys"])
    if secrets["access"] != "none" or secrets["allowedKeys"]:
        raise TaskStoreError("canonical_policy_secrets_unsupported")
    approval = _policy_object(resource["workerApproval"], {"required", "approvers"})
    _policy_strings(approval["approvers"])
    if type(approval["required"]) is not bool:
        raise TaskStoreError("canonical_policy_boolean_invalid")
    if approval["required"] or approval["approvers"]:
        raise TaskStoreError("canonical_policy_worker_approval_unsupported")
    github = _policy_strings(policy["githubCapabilities"], choices=GITHUB_POLICY_CAPABILITIES)
    publication = _policy_strings(policy["publicationCapabilities"], choices=PUBLICATION_POLICY_CAPABILITIES)
    pub = _policy_object(policy["publicationPolicy"], {"allowedArtifactOrPackage", "allowedRegistry",
        "allowedRepository", "allowedEnvironment"}, {"rollbackStrategy"})
    for name in ("allowedArtifactOrPackage", "allowedRegistry", "allowedRepository", "allowedEnvironment"):
        _policy_strings(pub[name])
    if "rollbackStrategy" in pub and (not isinstance(pub["rollbackStrategy"], str)
            or not pub["rollbackStrategy"].strip() or len(pub["rollbackStrategy"]) > 240):
        raise TaskStoreError("canonical_policy_rollback_invalid")
    merge = _policy_object(policy["mergePolicy"], {"allowedRepositories", "allowedBaseBranches",
        "requiredChecks", "allowedMergeMethods", "requireExactHead"})
    for name in ("allowedRepositories", "allowedBaseBranches", "requiredChecks"):
        _policy_strings(merge[name])
    _policy_strings(merge["allowedMergeMethods"], choices=frozenset({"merge", "squash", "rebase"}))
    if type(merge["requireExactHead"]) is not bool:
        raise TaskStoreError("canonical_policy_boolean_invalid")
    for repo in (*merge["allowedRepositories"], *pub["allowedRepository"]):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise TaskStoreError("canonical_policy_repository_invalid")
    for branch in merge["allowedBaseBranches"]:
        if (not re.fullmatch(r"[A-Za-z0-9._/-]{1,200}", branch)
                or ".." in branch or "//" in branch or branch.startswith("/") or branch.endswith("/")):
            raise TaskStoreError("canonical_policy_branch_invalid")
    window = _policy_object(policy["autonomousWindow"],
        {"enabled", "startsAt", "expiresAt", "stopConditions", *_CAP_FIELDS})
    if type(window["enabled"]) is not bool:
        raise TaskStoreError("canonical_policy_boolean_invalid")
    if not isinstance(window["startsAt"], str) or not isinstance(window["expiresAt"], str):
        raise TaskStoreError("invalid_autonomy_window_time")
    starts = AutonomyService._parse_time(window["startsAt"])
    expires = AutonomyService._parse_time(window["expiresAt"])
    current = now or datetime.now(timezone.utc)
    if (expires <= starts or expires - starts > MAX_WINDOW_DURATION
            or (window["enabled"] and (expires <= current or starts > current + timedelta(minutes=5)))):
        raise TaskStoreError("invalid_autonomy_window_time")
    budgets = _policy_object(policy["budgets"], set(_CAP_FIELDS))
    for name in _CAP_FIELDS:
        _policy_int(budgets[name])
        _policy_int(window[name])
        if budgets[name] != window[name]:
            raise TaskStoreError("canonical_policy_budget_conflict")
    if not isinstance(window["stopConditions"], list) or len(window["stopConditions"]) > 20:
        raise TaskStoreError("canonical_policy_stop_conditions_invalid")
    seen: set[tuple[str, str]] = set()
    for raw in window["stopConditions"]:
        rule = _policy_object(raw, {"type", "scope"}, {"limit"})
        if (not isinstance(rule["type"], str) or not isinstance(rule["scope"], str)
                or rule["type"] not in STOP_CONDITIONS or rule["scope"] not in {"task", "window"}):
            raise TaskStoreError("canonical_policy_stop_condition_invalid")
        key = (rule["type"], rule["scope"])
        if key in seen:
            raise TaskStoreError("canonical_policy_stop_condition_duplicate")
        seen.add(key)
        if "limit" in rule and _policy_int(rule["limit"]) < 1:
            raise TaskStoreError("canonical_policy_stop_limit_invalid")
        if rule["type"].startswith("max_") and "limit" not in rule:
            raise TaskStoreError("canonical_policy_stop_limit_required")
        if rule["type"] not in {"budget_exhausted", "window_expired", "manual_stop", "authority_revoked"}:
            raise TaskStoreError("canonical_policy_stop_adapter_unsupported")
    if github or publication:
        raise TaskStoreError("canonical_policy_capability_unsupported")
    if policy["mode"] not in {"CONTROLLER_REVIEW", "CUSTOM"}:
        raise TaskStoreError("canonical_policy_confirmation_mode_unsupported")
    # JSON copy preserves every field and array order; no coercion/defaulting.
    return json.loads(canonical_policy_json(policy))


def window_to_dict(window: AutonomousWindowRecord) -> dict[str, Any]:
    payload = asdict(window)
    payload["repositories"] = list(window.repositories)
    payload["capabilities"] = list(window.capabilities)
    payload["continuous"] = window.continuous
    return payload


class AutonomyService:
    def __init__(
        self,
        *,
        control_store: PlatformControlStore,
        capabilities: CapabilityRegistry,
    ) -> None:
        self.control_store = control_store
        self.capabilities = capabilities

    def activate(self, payload: Mapping[str, Any]) -> AutonomousWindowRecord:
        """Trusted in-process Owner-window activation."""
        normalized = self._validate_policy(payload)
        # Expiry, immutable replay and exclusivity share the store's write
        # transaction. A preflight read here cannot fence another host.
        return self.control_store.activate_window(
            normalized, confirmation=str(payload.get("confirmation", ""))
        )

    def authorize(
        self,
        *,
        window_id: str,
        operation: str,
        repository: str,
        subject_id: str,
        input_payload: Mapping[str, Any],
        record_receipt: bool = True,
    ) -> bool:
        decision = "allowed"
        reason = "operation_inside_active_window"
        try:
            active = self.control_store.active_window()
            window = self.control_store.get_window(window_id)
            if window.status != "ACTIVE" or active is None or active.id != window.id:
                raise TaskStoreError("window_not_active")
            if repository not in window.repositories:
                raise TaskStoreError("repository_outside_window")
            if operation not in window.capabilities:
                raise TaskStoreError("capability_outside_window")
            if operation not in KNOWN_OPERATIONS or not self.capabilities.supports_operation(operation):
                raise TaskStoreError("capability_unavailable")
            if operation == "approve_goal":
                # Goal approval inside a window needed the retired delegated
                # policy authority; Owner windows never grant it.
                raise TaskStoreError("delegated_goal_authority_required")
        except TaskStoreError as exc:
            decision = "denied"
            reason = str(exc)
        if record_receipt or decision != "allowed":
            self.control_store.append_receipt(
                window_id=window_id,
                operation_type="policy_evaluation",
                capability=operation,
                repository=repository,
                subject_id=subject_id,
                decision=decision,
                reason=reason,
                input_payload=input_payload,
            )
        return decision == "allowed"

    def summary(self, window_id: str, *, limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
        window = self.control_store.get_window(window_id)
        page = self.control_store.list_receipts_page(window_id=window_id, limit=limit, cursor=cursor)
        receipts = page["items"]
        goals = self.control_store.list_window_goals(window_id)
        usage_budget = self.control_store.window_budget_summary(window_id)
        return {
            "window": window_to_dict(window),
            "budget": {
                "tasks_remaining": None if window.continuous else max(0, window.max_tasks - window.tasks_started),
                "retries_remaining": max(0, window.max_retries - window.retries_used),
                "wip_limit": window.max_concurrent_tasks,
                **usage_budget,
            },
            "operations": self.control_store.receipt_totals(window_id=window_id),
            "adopted_goals": list(self.control_store.window_adopted_goals(window_id)),
            "goals": [
                {
                    "id": goal.id,
                    "title": goal.title,
                    "status": goal.status,
                    "revision": goal.revision,
                    "updated_at": goal.updated_at,
                }
                for goal in goals
            ],
            "receipts": [asdict(receipt) for receipt in receipts],
            "next_cursor": page["next_cursor"],
        }

    def status(self) -> dict[str, Any]:
        active = self.control_store.active_window()
        latest = None if active else next(iter(self.control_store.list_windows(limit=1)), None)
        window = active or latest
        return {
            "autonomy_enabled": active is not None,
            "active_window": window_to_dict(active) if active else None,
            "latest_window": window_to_dict(latest) if latest else None,
            "last_progress_at": self.control_store.window_last_progress_at(window.id) if window else None,
            # Work still waiting in this window; the stalled warning needs it, not the max_tasks budget.
            "unfinished_tasks": self.control_store.window_unfinished_task_count(active.id) if active else 0,
            "mode": ("delegated_controller_bounded_window" if active and active.confirmation_mode == "DELEGATED_CONTROLLER"
                     else "owner_activated_bounded_window"),
        }

    def _validate_policy(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        policy_id = str(payload.get("policy_id", "")).strip()
        owner = str(payload.get("owner_identity", "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9._:-]{3,100}", policy_id) or not owner:
            raise TaskStoreError("invalid_autonomy_policy_identity")
        revision = self._bounded_int(payload, "policy_revision", minimum=1, maximum=1_000_000)
        starts = self._parse_time(str(payload.get("starts_at", "")))
        expires = self._parse_time(str(payload.get("expires_at", "")))
        now = datetime.now(timezone.utc)
        if starts > now + timedelta(minutes=5) or expires <= now or expires <= starts:
            raise TaskStoreError("invalid_autonomy_window_time")
        if expires - starts > MAX_WINDOW_DURATION:
            raise TaskStoreError("autonomy_window_duration_exceeded")
        raw_repositories = payload.get("repositories", ())
        raw_capabilities = payload.get("capabilities", ())
        if not isinstance(raw_repositories, (list, tuple)) or not isinstance(raw_capabilities, (list, tuple)):
            raise TaskStoreError("autonomy_policy_arrays_required")
        repositories = tuple(dict.fromkeys(str(value).strip() for value in raw_repositories))
        if not repositories or any(not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) for repo in repositories):
            raise TaskStoreError("invalid_autonomy_repositories")
        capabilities = tuple(dict.fromkeys(str(value).strip() for value in raw_capabilities))
        if not capabilities or any(operation not in KNOWN_OPERATIONS for operation in capabilities):
            raise TaskStoreError("invalid_autonomy_capabilities")
        unavailable = [operation for operation in capabilities if not self.capabilities.supports_operation(operation)]
        if unavailable:
            raise TaskStoreError(f"unavailable_autonomy_capability:{','.join(unavailable)}")
        max_token_units = self._optional_budget_int(payload, "max_token_units")
        max_cost_micro_units = self._optional_budget_int(payload, "max_cost_micro_units")
        per_task_token_reservation = self._optional_budget_int(
            payload, "per_task_token_reservation"
        )
        per_task_cost_reservation = self._optional_budget_int(
            payload, "per_task_cost_reservation"
        )
        for limit, reservation, name in (
            (max_token_units, per_task_token_reservation, "token"),
            (max_cost_micro_units, per_task_cost_reservation, "cost"),
        ):
            if bool(limit) != bool(reservation) or (limit and reservation > limit):
                raise TaskStoreError(f"invalid_autonomy_budget_pair:{name}")
        provider_quota_state = str(
            payload.get("provider_quota_state", "NOT_CONFIGURED")
        ).strip().upper()
        if provider_quota_state not in {"NOT_CONFIGURED", "OBSERVED", "UNKNOWN"}:
            raise TaskStoreError("invalid_provider_quota_state")
        enforcement_class = (
            "HARD_ADMISSION_ENFORCED"
            if max_token_units or max_cost_micro_units
            else "POST_RUN_OBSERVED"
        )
        adopted = payload.get("adopt_unfinished_goals", ())
        if not isinstance(adopted, (list, tuple)):
            raise TaskStoreError("window_adoption_invalid")
        normalized = {
            "window_id": str(payload.get("window_id", "")).strip(),
            "policy_id": policy_id,
            "policy_revision": revision,
            "owner_identity": owner,
            "starts_at": self._format_time(starts),
            "expires_at": self._format_time(expires),
            "repositories": repositories,
            "capabilities": capabilities,
            "max_concurrent_tasks": self._bounded_int(payload, "max_concurrent_tasks", 1, 8),
            "max_tasks": self._bounded_int(payload, "max_tasks", 1, 100),
            "max_retries": self._bounded_int(payload, "max_retries", 0, 5),
            "max_token_units": max_token_units,
            "max_cost_micro_units": max_cost_micro_units,
            "per_task_token_reservation": per_task_token_reservation,
            "per_task_cost_reservation": per_task_cost_reservation,
            "provider_quota_state": provider_quota_state,
            "enforcement_class": enforcement_class,
        }
        if adopted:
            # Only an explicit Owner list adopts stranded Goals (#1277); absent keeps the digest unchanged.
            normalized["adopt_unfinished_goals"] = tuple(adopted)
        standing = payload.get("standing_renewal")
        if standing is not None:
            if not isinstance(standing, Mapping) or set(standing) != {"window_hours", "renew_until"}:
                raise TaskStoreError("standing_renewal_invalid")
            hours = standing["window_hours"]
            if type(hours) is not int or not 1 <= hours <= MAX_WINDOW_DURATION.days * 24:
                raise TaskStoreError("standing_renewal_window_hours_invalid")
            until = self._parse_time(str(standing["renew_until"]))
            if until <= expires or until > now + MAX_STANDING_HORIZON:
                raise TaskStoreError("standing_renewal_horizon_invalid")
            normalized["standing_renewal"] = {"window_hours": hours, "renew_until": self._format_time(until)}
        return normalized

    @staticmethod
    def _parse_time(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise TaskStoreError("invalid_autonomy_window_time") from exc
        if parsed.tzinfo is None:
            raise TaskStoreError("autonomy_time_requires_timezone")
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _format_time(value: datetime) -> str:
        return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _bounded_int(
        payload: Mapping[str, Any], key: str, minimum: int, maximum: int
    ) -> int:
        try:
            value = int(payload.get(key, minimum))
        except (TypeError, ValueError) as exc:
            raise TaskStoreError(f"invalid_autonomy_limit:{key}") from exc
        if value < minimum or value > maximum:
            raise TaskStoreError(f"invalid_autonomy_limit:{key}")
        return value

    @staticmethod
    def _optional_budget_int(payload: Mapping[str, Any], key: str) -> int:
        raw = payload.get(key, 0)
        if raw is None:
            return 0
        if type(raw) is not int or raw < 0 or raw > 10**15:
            raise TaskStoreError(f"invalid_autonomy_budget:{key}")
        return raw
