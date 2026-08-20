"""Owner-activated autonomous execution windows and server-side policy checks."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Mapping

from .capability_registry import CapabilityRegistry
from .control_store import AutonomousWindowRecord, PlatformControlStore
from .run_store import TaskStoreError


MAX_WINDOW_DURATION = timedelta(days=7)
KNOWN_OPERATIONS = frozenset(
    {"execute_task", "resume_task", "reconcile_task", "validate_task", "open_draft_pr"}
)


def window_to_dict(window: AutonomousWindowRecord) -> dict[str, Any]:
    payload = asdict(window)
    payload["repositories"] = list(window.repositories)
    payload["capabilities"] = list(window.capabilities)
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
        normalized = self._validate_policy(payload)
        active = self.control_store.active_window()
        if active is not None:
            if (
                active.policy_id == normalized["policy_id"]
                and active.policy_revision == normalized["policy_revision"]
            ):
                return self.control_store.activate_window(
                    normalized, confirmation=str(payload.get("confirmation", ""))
                )
            raise TaskStoreError(f"active_window_already_exists:{active.id}")
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
    ) -> bool:
        decision = "allowed"
        reason = "operation_inside_active_window"
        try:
            window = self.control_store.get_window(window_id)
            if window.status != "ACTIVE" or self.control_store.active_window() is None:
                raise TaskStoreError("window_not_active")
            if repository not in window.repositories:
                raise TaskStoreError("repository_outside_window")
            if operation not in window.capabilities:
                raise TaskStoreError("capability_outside_window")
            if operation not in KNOWN_OPERATIONS or not self.capabilities.supports_operation(operation):
                raise TaskStoreError("capability_unavailable")
        except TaskStoreError as exc:
            decision = "denied"
            reason = str(exc)
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

    def summary(self, window_id: str) -> dict[str, Any]:
        window = self.control_store.get_window(window_id)
        receipts = self.control_store.list_receipts(window_id=window_id)
        allowed = sum(1 for receipt in receipts if receipt.decision == "allowed")
        denied = sum(1 for receipt in receipts if receipt.decision == "denied")
        goals = self.control_store.list_window_goals(window_id)
        usage_budget = self.control_store.window_budget_summary(window_id)
        return {
            "window": window_to_dict(window),
            "budget": {
                "tasks_remaining": max(0, window.max_tasks - window.tasks_started),
                "retries_remaining": max(0, window.max_retries - window.retries_used),
                "wip_limit": window.max_concurrent_tasks,
                **usage_budget,
            },
            "operations": {"allowed": allowed, "denied": denied, "total": len(receipts)},
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
        }

    def status(self) -> dict[str, Any]:
        active = self.control_store.active_window()
        return {
            "autonomy_enabled": active is not None,
            "active_window": window_to_dict(active) if active else None,
            "mode": "owner_activated_bounded_window",
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
        return {
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
