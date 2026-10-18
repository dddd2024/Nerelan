"""TEST-ONLY host grant protocol prototype. No production caller or permission.

Must not be connected to HTTP, TrustedHost dispatch, or legacy activation.
Consumption proves only local consent continuity, NOT durable admission.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import secrets
import threading
import time

from . import native_owner_dialog
from .control_store import PlatformControlStore, canonical_json
from .repository_workspace import resolve_repository_workspace


@dataclass(frozen=True)
class FixturePolicy:
    """Host-owned fixture policy; not a resolved production execution policy."""

    repository: str
    binding_ref: str
    revision: int = 1
    executor_kind: str = "codex"
    max_tasks: int = 1
    max_minutes: int = 30
    max_retries: int = 0


@dataclass(frozen=True)
class ConsentPreview:
    """Immutable test evidence. Never an execution permission or receipt."""

    snapshot_json: str
    digest: str


class TestOnlyHostGrantPreparer:
    """Instantiate only in isolated fixtures; no dialog callback injection here.

    Selection accepts only a persisted Goal ID. All other scope comes from the
    store and host-owned fixture policy. Tokens stay in the calling host memory.
    """

    __test__ = False

    def __init__(self, control: PlatformControlStore, policy: FixturePolicy):
        if (type(policy) is not FixturePolicy or policy.executor_kind != "codex"
                or type(policy.revision) is not int or policy.revision < 1
                or type(policy.max_tasks) is not int or policy.max_tasks != 1
                or type(policy.max_minutes) is not int or not 0 < policy.max_minutes <= 30
                or type(policy.max_retries) is not int or policy.max_retries != 0
                or not policy.binding_ref):
            raise ValueError("invalid_fixture_policy")
        self._control = control
        self._policy = policy
        self._host = secrets.token_hex(32)
        self._pending: dict[str, tuple[str, ConsentPreview, float]] = {}
        self._lock = threading.Lock()

    def _snapshot(self, goal_id: str, window: str) -> ConsentPreview:
        goal = self._control.get_goal(goal_id)
        policy = self._policy
        if (goal.id != goal_id or goal.status != "PLANNED" or goal.window_id
                or goal.executor_kind != "codex" or goal.orchestration_mode != "single"
                or goal.repository != policy.repository or goal.binding_ref != policy.binding_ref
                or len(goal.tasks) != 1 or goal.tasks[0].get("agent_role")
                or goal.tasks[0].get("dependencies")
                or goal.tasks[0].get("capability", "execute_task") != "execute_task"):
            raise ValueError("goal_outside_fixture_scope")
        repo = resolve_repository_workspace(goal.repository)
        if repo.repository != policy.repository:
            raise ValueError("repository_mismatch")
        payload = json.dumps({"goal": asdict(goal), "policy": asdict(policy),
                                  "workspace": str(repo.repo_dir), "window": window,
                                  "host": self._host, "purpose": "TEST_ONLY_NO_PERMISSION"},
                             ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return ConsentPreview(payload, hashlib.sha256(payload.encode()).hexdigest())

    def prepare_for_test(self, goal_id: str) -> str | None:
        window = "preview-" + secrets.token_hex(16)
        before = self._snapshot(goal_id, window)
        goal = self._control.get_goal(goal_id)
        policy_json = canonical_json(asdict(self._policy))
        scope = native_owner_dialog.OwnerDialogScope(
            self._host, goal_id, goal.revision, before.digest, goal.repository,
            goal.executor_kind, goal.binding_ref, str(goal.tasks[0]["id"]), window,
            self._policy.revision, hashlib.sha256(policy_json.encode()).hexdigest(),
            before.snapshot_json)
        started = time.monotonic()
        if not native_owner_dialog.confirm_scope(scope):
            return None
        # Reject mutations during the OS dialog, including same-revision changes.
        if self._snapshot(goal_id, window) != before or time.monotonic() - started >= 30:
            raise ValueError("selection_changed_or_timed_out")
        token = secrets.token_urlsafe(32)
        with self._lock:
            # A new YES revokes older selections and bounds retained memory.
            self._pending.clear()
            self._pending[token] = (goal_id, before, started + 30)
        return token

    def consume_for_test(self, token: str, *, goal_id: str) -> ConsentPreview:
        """Burn before validation; failures cannot retry. Never launches anything."""
        with self._lock:
            entry = self._pending.pop(token, None)
            if entry is None:
                raise ValueError("unknown_or_consumed_grant")
            selected, preview, deadline = entry
            if selected != goal_id or time.monotonic() >= deadline:
                raise ValueError("grant_scope_or_expiry")
            window = json.loads(preview.snapshot_json)["window"]
            if self._snapshot(selected, window) != preview:
                raise ValueError("stale_grant")
            return preview
