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

    def _scope(self, goal_id, payload, *, admitted=False, original=None, isolation_digest=None):
        host = self._host
        identity = native_owner_identity.interactive_owner()
        if identity is None or identity != self._identity:
            raise TaskStoreError("native_owner_identity_unavailable_or_changed")
        control = host._control_store
        isolation = None
        if isolation_digest is not None:
            from .unknown_claim_isolation import selected_snapshot
            isolation = selected_snapshot(control._conn, isolation_digest)
        if isolation is None and control._conn.execute(
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
                           "base_sha": base, "window": payload, "unknown_claim_isolation": isolation,
                           "owner": asdict(identity), "host_instance": self._instance,
                           "consent_valid_seconds": 30,
                           "sandbox": "existing Codex sandbox; no changes",
                           "api_auth": "unchanged", "account_switching": False},
                          ensure_ascii=True, sort_keys=True, separators=(",", ":"))

    def admit(self, goal_id: str, *, unknown_claims_sha256=None):
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
                before = self._scope(goal_id, payload, isolation_digest=unknown_claims_sha256)
                if canonical_json(asdict(goal)) != canonical_json(json.loads(before)["goal"]):
                    raise TaskStoreError("native_owner_scope_changed")
            displayed = json.loads(before)
            isolation = displayed["unknown_claim_isolation"]
            if isolation is not None:
                # Display-only projection of a separate JSON decode. `before`
                # remains full for exact readback, SHA/CAS and receipt evidence.
                # Never truncate the fresh Goal or its authority fields to fit.
                isolation["old_claim_semantics"] = "UNKNOWN; no release; no refund; no old retry"
                isolation["snapshot"]["claims"] = [
                    {"claim": {key: item["claim"][key] for key in
                               ("task_id", "window_id", "epoch", "status", "expires_at_ms")},
                     "provider_terminal_state": "UNKNOWN",
                     "runs": [{key: run[key] for key in
                               ("run_id", "execution_id", "lease_epoch", "lease_expiry_ms")}
                              for run in item["runs"]],
                     "reservations": [{key: reservation[key] for key in
                         ("task_id", "claim_epoch", "window_id", "state",
                          "reserved_token_units", "reserved_cost_micro_units",
                          "observed_token_units", "observed_cost_micro_units")}
                         for reservation in item["reservations"]],
                     "window_accounting": {key: value for key, value in item["window"].items()
                         if key in {"id", "tasks_started", "tasks_completed", "retries_used",
                                    "max_tasks", "max_token_units", "max_cost_micro_units",
                                    "observed_token_units", "observed_cost_micro_units",
                                    "unknown_observation_count"}}}
                    for item in isolation["snapshot"]["claims"]]
            display_text = json.dumps(displayed, ensure_ascii=True, sort_keys=True,
                                      separators=(",", ":"))
            scope = native_owner_dialog.OwnerDialogScope(
                self._instance, goal.id, goal.revision, goal.artifact_digest, goal.repository,
                goal.executor_kind, goal.binding_ref, str(goal.tasks[0]["id"]), payload["window_id"],
                1, sha256_json(payload), display_text)
            scope.text(admission=True)  # Native display bounds also apply before any callback.
            if not native_owner_dialog.confirm_admission(scope):
                raise TaskStoreError("native_owner_consent_refused")
            # Burn before any validation or write. No retry/consumer can reuse it.
            nonce, self._nonce = self._nonce, None
            if nonce is None:
                raise TaskStoreError("native_owner_consent_consumed")

            def validate(*, admitted=False):
                if self._scope(goal_id, payload, admitted=admitted, original=goal,
                               isolation_digest=unknown_claims_sha256) != before:
                    raise TaskStoreError("native_owner_scope_changed")
                if time.monotonic() >= deadline:
                    raise TaskStoreError("native_owner_consent_expired")

            def sql_admit(window_id):
                validate()  # BEGIN IMMEDIATE already held; reread persisted truth.
                host._goal_service.approve(goal.id, expected_revision=goal.revision,
                                           policy_ref=payload["policy_id"])
                host._goal_service._launch(goal.id, expected_revision=goal.revision, window_id=window_id)
                validate(admitted=True)
                approved = json.loads(before)
                from .binding_resolver import _validate_provider_base_url
                pinned_binding = {
                    "binding_ref": goal.binding_ref,
                    "model_id": approved["binding"]["model_id"],
                    "connection_id": approved["binding"]["connection_id"],
                    "executor_id": approved["binding"]["executor_id"],
                    "provider_id": approved["connection"]["provider"],
                    "auth_method": approved["connection"]["auth_method"],
                    "base_url": _validate_provider_base_url(approved["connection"]["base_url"]),
                }
                provenance = {"host_instance_id": self._instance,
                              "owner": asdict(self._identity), "scope_digest": sha256_json(before),
                              "approved_binding": pinned_binding,
                              "unknown_claim_isolation": approved["unknown_claim_isolation"],
                              "goal_revision": goal.revision, "binding_ref": goal.binding_ref,
                              "workspace": json.loads(before)["workspace"],
                              "base_sha": json.loads(before)["base_sha"],
                              "native_mechanism": "Windows token SID + WTS console + native desktop dialog"}
                receipt = host._control_store.append_receipt(
                    window_id=window_id, operation_type="native_goal_admission", capability="execute_task",
                    repository=goal.repository, subject_id=goal.id, decision="allowed",
                    reason="native_owner_exact_scope", input_payload={**provenance, "unknown_claim_isolation":
                                   ({"sha256": unknown_claims_sha256}
                                    if unknown_claims_sha256 is not None else None)},
                    result=canonical_json(provenance))
                # Store full nonsecret provenance; append_receipt's result is bounded.
                updated = host._control_store._conn.execute(
                    "UPDATE platform_operation_receipts SET evidence_json = ?, confirmation_mode = ? "
                    "WHERE id = ? AND window_id = ? AND operation_type = 'native_goal_admission'",
                    (canonical_json(provenance), "NATIVE_OWNER", receipt.id, window_id))
                if updated.rowcount != 1:
                    raise TaskStoreError("native_admission_receipt_missing")
                marked = host._control_store._conn.execute(
                    "UPDATE platform_autonomous_windows SET confirmation_mode = ? WHERE id = ?",
                    ("NATIVE_OWNER", window_id))
                if marked.rowcount != 1:
                    raise TaskStoreError("native_admission_window_missing")
                validate(admitted=True)

            with host._task_store._lock, host._store._lock:
                validate()  # after consent, before the transaction
                return host._control_store.activate_window(
                    payload, confirmation="ACTIVATE", _host_sql_admit=sql_admit,
                    _host_expected_goal_id=goal.id,
                    _host_preserve_claim_windows=unknown_claims_sha256 is not None)
        finally:
            self._nonce = None  # refusal, timeout, native/SQL errors, interrupts
            self._lock.release()
