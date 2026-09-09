"""Provider-free, read-only readiness aggregation for the trusted Task API.

System Doctor proves only facts already owned by Nerelan. A readiness fact whose
canonical owner is not yet integrated is reported as ``UNKNOWN`` rather than
being guessed from ambient host state.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

READY = "READY"
DEGRADED = "DEGRADED"
BLOCKED = "BLOCKED"
UNKNOWN = "UNKNOWN"
DOCTOR_STATES = frozenset({READY, DEGRADED, BLOCKED, UNKNOWN})


@dataclass(frozen=True)
class DoctorCheck:
    """One bounded readiness fact safe to return to the product surface."""

    id: str
    component: str
    state: str
    required: bool
    summary: str
    reason_code: str
    remediation_id: str

    def __post_init__(self) -> None:
        if self.state not in DOCTOR_STATES:
            raise ValueError("invalid_doctor_state")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "component": self.component,
            "state": self.state,
            "required": self.required,
            "summary": self.summary,
            "reason_code": self.reason_code,
            "remediation_id": self.remediation_id,
        }


def aggregate_state(checks: tuple[DoctorCheck, ...]) -> str:
    """Apply the closed OPS-3A fail-closed precedence."""

    if any(check.required and check.state == BLOCKED for check in checks):
        return BLOCKED
    if any(check.required and check.state == UNKNOWN for check in checks):
        return UNKNOWN
    if any(check.state == DEGRADED for check in checks):
        return DEGRADED
    return READY


class SystemDoctor:
    """Aggregate bounded local readiness facts without diagnostic side effects."""

    def __init__(
        self,
        *,
        store: Any,
        runtime_status_provider: Callable[[], Mapping[str, Any]],
    ) -> None:
        self._store = store
        self._runtime_status_provider = runtime_status_provider

    def run(self) -> dict[str, Any]:
        checks = (
            DoctorCheck(
                id="task_api_reachable",
                component="task_api",
                state=READY,
                required=True,
                summary="Trusted Task API is serving the Doctor request.",
                reason_code="task_api_reachable",
                remediation_id="none",
            ),
            self._task_store_readable(),
            self._task_store_storage_path(),
            self._runtime_status_available(),
            self._not_integrated(
                check_id="repository_workspace_readiness",
                component="repository_workspace",
                reason_code="repository_workspace_truth_not_integrated",
                remediation_id="complete_repository_workspace_binding",
            ),
            self._not_integrated(
                check_id="executor_readiness",
                component="executor",
                reason_code="executor_provenance_truth_not_integrated",
                remediation_id="complete_executor_provenance_integration",
            ),
            self._not_integrated(
                check_id="connection_binding_readiness",
                component="connection_binding",
                reason_code="connection_binding_truth_not_integrated",
                remediation_id="complete_product_setup_integration",
            ),
            self._not_integrated(
                check_id="desktop_lifecycle_readiness",
                component="desktop_lifecycle",
                reason_code="desktop_lifecycle_truth_not_integrated",
                remediation_id="complete_desktop_lifecycle_integration",
            ),
        )
        return {
            "schema_version": 1,
            "state": aggregate_state(checks),
            "checks": [check.to_dict() for check in checks],
        }

    def _task_store_readable(self) -> DoctorCheck:
        try:
            count = self._store.count_tasks()
            if isinstance(count, bool) or int(count) < 0:
                raise ValueError("invalid_task_count")
        except Exception:
            return DoctorCheck(
                id="task_store_readable",
                component="task_store",
                state=BLOCKED,
                required=True,
                summary="TaskStore read readiness could not be proven.",
                reason_code="task_store_read_failed",
                remediation_id="restart_task_store",
            )
        return DoctorCheck(
            id="task_store_readable",
            component="task_store",
            state=READY,
            required=True,
            summary="TaskStore accepted a bounded read.",
            reason_code="task_store_readable",
            remediation_id="none",
        )

    def _task_store_storage_path(self) -> DoctorCheck:
        try:
            db_path = str(self._store.db_path)
        except Exception:
            return self._storage_unknown("task_store_path_unavailable")

        if not db_path:
            return self._storage_unknown("task_store_path_unavailable")
        if db_path == ":memory:":
            return self._storage_unknown("task_store_path_non_durable")

        try:
            path = Path(db_path)
            parent = path.parent
            if not parent.exists() or not parent.is_dir():
                return DoctorCheck(
                    id="task_store_storage_path",
                    component="task_store_storage",
                    state=BLOCKED,
                    required=True,
                    summary="Configured TaskStore parent path is unavailable.",
                    reason_code="task_store_parent_unavailable",
                    remediation_id="repair_task_store_path",
                )
            if not path.exists() or not path.is_file():
                return self._storage_unknown("task_store_file_not_proven")
        except (OSError, TypeError, ValueError):
            return self._storage_unknown("task_store_path_check_failed")

        return DoctorCheck(
            id="task_store_storage_path",
            component="task_store_storage",
            state=READY,
            required=True,
            summary="Configured TaskStore file and parent path are present.",
            reason_code="task_store_storage_path_available",
            remediation_id="none",
        )

    def _runtime_status_available(self) -> DoctorCheck:
        try:
            status = self._runtime_status_provider()
            if not isinstance(status, Mapping):
                raise TypeError("runtime_status_not_mapping")
            if status.get("service") != "reverse-agent-platform-v2":
                raise ValueError("runtime_service_mismatch")
        except Exception:
            return DoctorCheck(
                id="runtime_status_available",
                component="runtime_status",
                state=BLOCKED,
                required=True,
                summary="Canonical runtime status could not be read.",
                reason_code="runtime_status_unavailable",
                remediation_id="restart_trusted_host",
            )
        return DoctorCheck(
            id="runtime_status_available",
            component="runtime_status",
            state=READY,
            required=True,
            summary="Canonical runtime status is available.",
            reason_code="runtime_status_available",
            remediation_id="none",
        )

    @staticmethod
    def _not_integrated(
        *,
        check_id: str,
        component: str,
        reason_code: str,
        remediation_id: str,
    ) -> DoctorCheck:
        return DoctorCheck(
            id=check_id,
            component=component,
            state=UNKNOWN,
            required=True,
            summary="Canonical readiness truth is not yet integrated into System Doctor.",
            reason_code=reason_code,
            remediation_id=remediation_id,
        )

    @staticmethod
    def _storage_unknown(reason_code: str) -> DoctorCheck:
        return DoctorCheck(
            id="task_store_storage_path",
            component="task_store_storage",
            state=UNKNOWN,
            required=True,
            summary="TaskStore storage-path readiness could not be proven.",
            reason_code=reason_code,
            remediation_id="verify_task_store_path",
        )
