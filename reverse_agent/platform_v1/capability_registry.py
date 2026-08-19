"""Small, inspectable registry of mature platform capabilities and Packs.

This is deliberately metadata, not a package manager or plugin runtime.  It
advertises the existing trusted adapters and can load bounded JSON manifests
from an owner-selected directory without executing third-party code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .control_store import reject_sensitive_keys, sha256_json
from .run_store import TaskStoreError


@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    kind: str
    provider: str
    version: str
    description: str
    operations: tuple[str, ...]
    maturity: str
    available: bool = True
    source: str = "builtin"


BUILTIN_CAPABILITIES = (
    Capability(
        "spec-kit-planning", "Spec Kit planning", "planner", "GitHub Spec Kit", "compatible",
        "Persistent Goal to Specification, Plan and Tasks artifacts.", ("plan_goal",), "stable",
    ),
    Capability(
        "langgraph-orchestration", "LangGraph orchestration", "orchestrator", "LangGraph", "pinned",
        "Sequential and parallel team topology with durable checkpoints.",
        ("execute_task", "resume_task", "reconcile_task"), "stable",
    ),
    Capability(
        "opencode-executor", "OpenCode executor", "executor", "OpenCode", "pinned",
        "Repository execution through bounded ACP/OpenCode adapters.", ("execute_task", "resume_task"), "stable",
    ),
    Capability(
        "deterministic-verifier", "Deterministic verifier", "verifier", "reverse-agent", "1",
        "Allowlisted validation commands and exact evidence digests.", ("validate_task",), "stable",
    ),
    Capability(
        "github-draft-publication", "GitHub Draft publication", "publisher", "GitHub", "api",
        "Idempotent branch push and Draft PR creation; merge is excluded.", ("open_draft_pr",), "guarded",
    ),
    Capability(
        "agent-canvas", "Agent Canvas", "frontend", "OpenHands", "pinned",
        "Human-readable task, evidence and product setup surface.", ("view_platform",), "stable",
    ),
)


class CapabilityRegistry:
    def __init__(self, *, pack_dir: str | Path | None = None) -> None:
        self.pack_dir = Path(pack_dir).resolve() if pack_dir else None

    def list(self) -> tuple[Capability, ...]:
        capabilities = list(BUILTIN_CAPABILITIES)
        if self.pack_dir and self.pack_dir.is_dir():
            for manifest_path in sorted(self.pack_dir.glob("*.json")):
                capabilities.append(self._load_manifest(manifest_path))
        ids = [item.id for item in capabilities]
        if len(ids) != len(set(ids)):
            raise TaskStoreError("duplicate_capability_id")
        return tuple(capabilities)

    def response(self) -> dict[str, Any]:
        items = [asdict(capability) for capability in self.list()]
        return {"capabilities": items, "total": len(items), "digest": sha256_json(items)}

    def supports_operation(self, operation: str) -> bool:
        return any(operation in capability.operations and capability.available for capability in self.list())

    @staticmethod
    def _load_manifest(path: Path) -> Capability:
        try:
            if path.stat().st_size > 64 * 1024:
                raise TaskStoreError(f"capability_manifest_too_large:{path.name}")
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TaskStoreError(f"invalid_capability_manifest:{path.name}") from exc
        if not isinstance(payload, Mapping):
            raise TaskStoreError(f"invalid_capability_manifest:{path.name}")
        reject_sensitive_keys(payload)
        identifier = str(payload.get("id", "")).strip()
        operations = tuple(str(value).strip() for value in payload.get("operations", ()) if str(value).strip())
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", identifier) or not operations:
            raise TaskStoreError(f"invalid_capability_manifest:{path.name}")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]{1,62}", operation) for operation in operations):
            raise TaskStoreError(f"invalid_capability_operation:{identifier}")
        return Capability(
            id=identifier,
            name=str(payload.get("name", identifier)).strip(),
            kind=str(payload.get("kind", "pack")).strip(),
            provider=str(payload.get("provider", "owner-pack")).strip(),
            version=str(payload.get("version", "1")).strip(),
            description=str(payload.get("description", "")).strip(),
            operations=operations,
            maturity=str(payload.get("maturity", "experimental")).strip(),
            available=bool(payload.get("available", True)),
            source=f"pack:{path.name}",
        )
