"""One native host consent -> one atomic Goal admission. No transport surface.

Only CombinedTrustedHost calls this module. No grant/token is returned to a
renderer, HTTP handler or model. The nonce lives only during this native call
and is burned before SQL admission, including on refusal/error/expiry.
"""
from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import json
import secrets
import threading
import time

from . import native_owner_dialog, native_owner_identity
from .control_store import canonical_json, sha256_json
from .functional_validation import repository_base
from .repository_workspace import resolve_repository_workspace
from .run_store import TaskStoreError


class NativeGoalAdmission:
    def __init__(self, host):
        self._host = host
        self._identity = native_owner_identity.interactive_owner()
        self._instance = secrets.token_hex(16)
        self._lock = threading.Lock()
        self._nonce = None

    def _scope(self, goal_id, payload, *, admitted=False, original=None):
        host = self._host
        identity = native_owner_identity.interactive_owner()
        if identity is None or identity != self._identity:
            raise TaskStoreError("native_owner_identity_unavailable_or_changed")
        control = host._control_store
        if control._conn.execute(
                "SELECT 1 FROM platform_coordinator_claims WHERE status = 'ACTIVE' LIMIT 1").fetchone():
            raise TaskStoreError("native_admission_old_active_claims_hold")
        goal = control.get_goal(goal_id)
        if admitted:
            if (goal.status != "RUNNING" or goal.window_id != payload["window_id"]
                    or goal.policy_ref != payload["policy_id"]):
                raise TaskStoreError("native_admission_goal_changed")
            goal = replace(goal, status=original.status, window_id=original.window_id,
                           policy_ref=original.policy_ref, updated_at=original.updated_at)
        if (goal.status != "PLANNED" or goal.window_id or not goal.artifact_digest
                or goal.executor_kind != "codex" or goal.orchestration_mode != "single"
                or len(goal.tasks) != 1 or goal.tasks[0].get("agent_role")
                or goal.tasks[0].get("dependencies")
                or goal.tasks[0].get("capability", "execute_task") != "execute_task"
                or goal.tasks[0].get("validation_command_id")):
            raise TaskStoreError("native_admission_requires_planned_single_codex_goal")
        links = control.list_goal_tasks(goal_id)
        if not admitted and links:
            raise TaskStoreError("native_admission_goal_already_materialized")
        binding = host._store.get_binding_public(goal.binding_ref)
        connection = host._store.get_connection_public(binding["connection_id"])
        if (not binding["enabled"] or binding["executor_id"] != "codex"
                or not connection["enabled"] or connection["executor_provider_id"] != "codex"
                or connection["auth_method"] != "external_cli_session"):
            raise TaskStoreError("native_admission_requires_pinned_native_codex_binding")
        workspace = resolve_repository_workspace(goal.repository)
        base = repository_base(goal.repository)
        if workspace.repository != goal.repository:
            raise TaskStoreError("native_admission_repository_changed")
        if admitted:
            if len(links) != 1:
                raise TaskStoreError("native_admission_task_changed")
            task = host._task_store.get_task(links[0]["task_id"])
            plan = host._goal_service._normalize_task(goal.tasks[0], seq=0)
            if (task.title != host._goal_service._execution_title(goal, plan)
                    or task.repository != goal.repository or task.branch != base
                    or task.binding_ref != goal.binding_ref or task.executor_kind != "codex"
                    or task.orchestration_mode != "single" or task.status != "QUEUED"
                    or task.policy_ref != payload["policy_id"]
                    or task.permission_profile != "AUTONOMOUS_WINDOW"):
                raise TaskStoreError("native_admission_task_changed")
        # Public metadata only: no execution snapshot, vault, credentials or tokens.
        return json.dumps({"goal": asdict(goal), "binding": binding,
                           "connection": connection, "workspace": str(workspace.repo_dir),
                           "base_sha": base, "window": payload,
                           "owner": asdict(identity), "host_instance": self._instance,
                           "consent_valid_seconds": 30,
                           "sandbox": "existing Codex sandbox; no changes",
                           "api_auth": "unchanged", "account_switching": False},
                          ensure_ascii=True, sort_keys=True, separators=(",", ":"))

    def admit(self, goal_id: str):
        if not self._lock.acquire(blocking=False):
            raise TaskStoreError("native_admission_in_progress")
        try:
            self._nonce = secrets.token_bytes(32)
            deadline = time.monotonic() + 30
            host = self._host
            now = datetime.now(timezone.utc)
            # Times are fixed BEFORE showing consent; dialog time spends the window.
            payload = {"window_id": "native-" + secrets.token_hex(16),
                       "policy_id": "native-" + secrets.token_hex(16), "policy_revision": 1,
                       "owner_identity": self._identity.sid if self._identity else "UNAVAILABLE",
                       "starts_at": now.isoformat(), "expires_at": (now + timedelta(minutes=30)).isoformat(),
                       "repositories": [], "capabilities": ["execute_task"],
                       "max_tasks": 1, "max_concurrent_tasks": 1, "max_retries": 0,
                       "max_token_units": 0, "max_cost_micro_units": 0,
                       "provider_quota_state": "UNKNOWN", "enforcement_class": "HARD_ADMISSION_ENFORCED"}
            with host._task_store._lock, host._store._lock:
                goal = host._control_store.get_goal(goal_id)
                payload["repositories"] = [goal.repository]
                before = self._scope(goal_id, payload)
                if canonical_json(asdict(goal)) != canonical_json(json.loads(before)["goal"]):
                    raise TaskStoreError("native_owner_scope_changed")
            scope = native_owner_dialog.OwnerDialogScope(
                self._instance, goal.id, goal.revision, goal.artifact_digest, goal.repository,
                goal.executor_kind, goal.binding_ref, str(goal.tasks[0]["id"]), payload["window_id"],
                1, sha256_json(payload), before)
            if not native_owner_dialog.confirm_admission(scope):
                raise TaskStoreError("native_owner_consent_refused")
            # Burn before any validation or write. No retry/consumer can reuse it.
            nonce, self._nonce = self._nonce, None
            if nonce is None:
                raise TaskStoreError("native_owner_consent_consumed")

            def validate(*, admitted=False):
                if self._scope(goal_id, payload, admitted=admitted, original=goal) != before:
                    raise TaskStoreError("native_owner_scope_changed")
                if time.monotonic() >= deadline:
                    raise TaskStoreError("native_owner_consent_expired")

            def sql_admit(window_id):
                validate()  # BEGIN IMMEDIATE already held; reread persisted truth.
                host._goal_service.approve(goal.id, expected_revision=goal.revision,
                                           policy_ref=payload["policy_id"])
                host._goal_service._launch(goal.id, expected_revision=goal.revision, window_id=window_id)
                validate(admitted=True)
                provenance = {"host_instance_id": self._instance,
                              "owner": asdict(self._identity), "scope_digest": sha256_json(before),
                              "goal_revision": goal.revision, "binding_ref": goal.binding_ref,
                              "workspace": json.loads(before)["workspace"],
                              "base_sha": json.loads(before)["base_sha"],
                              "native_mechanism": "Windows token SID + WTS console + native desktop dialog"}
                receipt = host._control_store.append_receipt(
                    window_id=window_id, operation_type="native_goal_admission", capability="execute_task",
                    repository=goal.repository, subject_id=goal.id, decision="allowed",
                    reason="native_owner_exact_scope", input_payload=provenance,
                    result=canonical_json(provenance))
                # Store full nonsecret provenance; append_receipt's result is bounded.
                updated = host._control_store._conn.execute(
                    "UPDATE platform_operation_receipts SET evidence_json = ?, confirmation_mode = ? "
                    "WHERE id = ? AND window_id = ? AND operation_type = 'native_goal_admission'",
                    (canonical_json(provenance), "NATIVE_OWNER", receipt.id, window_id))
                if updated.rowcount != 1:
                    raise TaskStoreError("native_admission_receipt_missing")
                validate(admitted=True)

            with host._task_store._lock, host._store._lock:
                validate()  # after consent, before the transaction
                return host._control_store.activate_window(
                    payload, confirmation="ACTIVATE", _host_sql_admit=sql_admit,
                    _host_expected_goal_id=goal.id)
        finally:
            self._nonce = None  # refusal, timeout, native/SQL errors, interrupts
            self._lock.release()
