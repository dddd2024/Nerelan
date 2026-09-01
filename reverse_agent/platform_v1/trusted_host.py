"""Combined trusted host for Platform V1.

A single Python process that exposes:
  - Model Control API on 127.0.0.1:8765
  - Task API on 127.0.0.1:8766

Both services share a single :class:`~reverse_agent.model_access.store.
ModelProfileStore`, and the Task API is wired to a
:class:`~reverse_agent.model_access.credential_relay.
CredentialRelayManager` so that api_key Bindings obtain execution-scoped
leases before OpenCode launch.

No DB, no management API, no plugin system, no model catalog.  Only the
existing public GET/PUT/DELETE routes on both ports, plus the private
credential relay used internally during execution.
"""

from __future__ import annotations

from collections.abc import Callable
from http.server import ThreadingHTTPServer
import json
import os
import subprocess
import threading
import time
from typing import Any

from ..model_access.contracts import ExecutionSnapshot
from ..model_access.credential_relay import (
    CredentialRelayManager,
    ExecutionLease,
    _normalize_model_id,
)
from ..model_access.os_vault import default_vault_adapter
from ..model_access.account_auth import AccountAuthManager, ServerFactory
from ..model_access.service import _handler_factory as _model_control_handler_factory
from ..model_access.store import ModelProfileStore
from .github_adapter import LiveGitHubAdapter
from .opencode_executor import (
    ExecutionLeaseHandle,
    execute_opencode_auth_list_probe,
    start_opencode_account_auth_server,
)
from .run_store import TaskStore
from .task_runtime import ExecutorRouter
from .task_service import _handler_factory as _task_handler_factory
from .durable_execution import DurableExecutionService
from .autonomy import AutonomyService
from .capability_registry import CapabilityRegistry
from .control_store import PlatformControlStore
from .goal_service import GoalService
from .publication_controller import PublicationController
from .unattended_coordinator import UnattendedCoordinator


class CombinedTrustedHost:
    """One-process host for Model Control + Task API + credential relay."""

    _PLATFORM_VAULT: Any = object()

    def __init__(self, **kwargs: Any) -> None:
        raise RuntimeError("DO_NOT_USE_THIS_SENTINEL")
