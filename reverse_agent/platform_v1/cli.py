"""Machine-readable CLI for Platform V1.

Exit codes:
  0 — success
  10 — schema/validation error
  20 — policy violation
  30 — backend/publication error
  40 — acceptance rework required (REWORK_REQUIRED)
  41 — fixture validated (FIXTURE_VALIDATED — not live-ready)
  50 — acceptance blocked (BLOCKED_APPROVAL / FAILED_TERMINAL)
  60 — live collection error (Git/GitHub/test failure)

F10: The ``evaluate-acceptance`` command processes fixture evidence only and
returns ``FIXTURE_VALIDATED`` (exit 41) when all checks pass — never
``ACCEPTED`` or the live-success exit code. The separate
``evaluate-live-acceptance`` command collects trusted facts itself through
injectable adapters and does not accept a raw evidence object.

F11: The live path requires mandatory exact binding (repository, base SHA,
exact head SHA, PR number, target branch, authority digest, required
workflows) — no optional defaults.

F12: Required workflows come from the approved Work Item, not from evidence.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Sequence

from . import acceptance, evidence_adapter, openhands_adapter, policy_adapter
from .contracts import (
    ExecutionBinding,
    ExecutionEvidence,
    PlatformAcceptanceResult,
    PlatformWorkItem,
)
from .evidence_adapter import EvidenceCollectionError
from .github_adapter import GitHubAdapterError


def _print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, sort_keys=True, separators=(",", ":")))


def _read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_validate_work_item(args: Sequence[str]) -> int:
    """Validate a Work Item against the platform policy."""

    try:
        data = _read_stdin_json()
        work_item = PlatformWorkItem.from_mapping(data)
        policy_adapter.validate_work_item(work_item)
        _print_json({
            "status": "VALID",
            "execution_id": work_item.execution_id,
            "branch_name": work_item.branch_name,
            "pr_marker": work_item.pr_marker,
            "digest": work_item.digest,
        })
        return 0
    except policy_adapter.PolicyViolation as exc:
        _print_json({"status": "POLICY_VIOLATION", "code": exc.code, "detail": exc.detail})
        return 20
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        _print_json({"status": "SCHEMA_ERROR", "error": str(exc)})
        return 10


def cmd_create_binding(args: Sequence[str]) -> int:
    """Create an execution binding from a Work Item."""

    try:
        data = _read_stdin_json()
        work_item = PlatformWorkItem.from_mapping(data)
        attempt = int(data.get("attempt", 1))
        binding = ExecutionBinding(work_item=work_item, attempt=attempt)
        policy_adapter.validate_binding(binding)
        _print_json({
            "status": "BOUND",
            "execution_id": binding.execution_id,
            "branch_name": binding.branch_name,
            "pr_marker": binding.pr_marker,
            "attempt": binding.attempt,
            "is_retry": binding.is_retry,
        })
        return 0
    except policy_adapter.PolicyViolation as exc:
        _print_json({"status": "POLICY_VIOLATION", "code": exc.code, "detail": exc.detail})
        return 20
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        _print_json({"status": "SCHEMA_ERROR", "error": str(exc)})
        return 10


def cmd_generate_prompt(args: Sequence[str]) -> int:
    """Generate a bounded task prompt from a Work Item."""

    try:
        data = _read_stdin_json()
        work_item = PlatformWorkItem.from_mapping(data)
        policy_adapter.validate_work_item(work_item)
        prompt = policy_adapter.generate_task_prompt(work_item)
        _print_json({"status": "OK", "prompt": prompt})
        return 0
    except policy_adapter.PolicyViolation as exc:
        _print_json({"status": "POLICY_VIOLATION", "code": exc.code, "detail": exc.detail})
        return 20
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        _print_json({"status": "SCHEMA_ERROR", "error": str(exc)})
        return 10


def cmd_ingest_events(args: Sequence[str]) -> int:
    """Ingest OpenHands events and produce untrusted evidence."""

    try:
        data = _read_stdin_json()
        events = data.get("events", [])
        execution_id = data["execution_id"]
        repository = data["repository"]
        base_sha = data["base_sha"]
        head_sha = data["head_sha"]
        pr_number = int(data["pr_number"])
        required_workflows = data.get("required_workflows", [])
        evidence = openhands_adapter.ingest_events(
            events,
            execution_id,
            repository,
            base_sha,
            head_sha,
            pr_number,
            required_workflows,
        )
        _print_json({
            "status": "OK",
            "evidence": {
                "execution_id": evidence.execution_id,
                "repository": evidence.repository,
                "base_sha": evidence.base_sha,
                "head_sha": evidence.head_sha,
                "pr_number": evidence.pr_number,
                "changed_paths": list(evidence.changed_paths),
                "agent_completion_claim": evidence.agent_completion_claim,
                "collection_mode": evidence.collection_mode,
                "provenance": evidence.provenance,
            },
        })
        return 0
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        _print_json({"status": "SCHEMA_ERROR", "error": str(exc)})
        return 10


def cmd_evaluate_acceptance(args: Sequence[str]) -> int:
    """Evaluate acceptance from binding and fixture evidence.

    F10: This command processes fixture evidence only. ``from_mapping`` forces
    ``collection_mode=fixture`` and ``provenance=caller_asserted`` regardless
    of caller-supplied labels. When all checks pass, the result is
    ``FIXTURE_VALIDATED`` (exit 41) — never ``ACCEPTED`` or the live-success
    exit code.

    For live acceptance, use ``evaluate-live-acceptance`` instead.
    """

    try:
        data = _read_stdin_json()
        work_item = PlatformWorkItem.from_mapping(data["work_item"])
        attempt = int(data.get("attempt", 1))
        binding = ExecutionBinding(work_item=work_item, attempt=attempt)
        # F9: from_mapping always forces fixture/caller_asserted
        evidence = ExecutionEvidence.from_mapping(data["evidence"])
        result = acceptance.evaluate_acceptance(binding, evidence)
        _print_json(result.to_mapping())
        if result.status == "ACCEPTED":
            return 0
        if result.status == "FIXTURE_VALIDATED":
            return 41
        if result.status == "REWORK_REQUIRED":
            return 40
        return 50  # BLOCKED_APPROVAL or FAILED_TERMINAL
    except policy_adapter.PolicyViolation as exc:
        _print_json({"status": "POLICY_VIOLATION", "code": exc.code, "detail": exc.detail})
        return 20
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        _print_json({"status": "SCHEMA_ERROR", "error": str(exc)})
        return 10


def cmd_evaluate_live_acceptance(args: Sequence[str]) -> int:
    """Evaluate live acceptance by collecting trusted facts.

    F10: This command does NOT accept a raw evidence object. It receives only
    execution targets (work item, PR number, expected head SHA, etc.) and
    collects trusted facts itself through injectable adapters.

    F11: All binding parameters are mandatory — no optional defaults.

    F12: Required workflows come from the Work Item, not from the caller.

    The ``--adapters`` argument optionally accepts a JSON file path for
    test-injected adapters (not used in production).
    """

    try:
        data = _read_stdin_json()
        work_item = PlatformWorkItem.from_mapping(data["work_item"])
        # F12: required workflows come from the Work Item, NOT from evidence
        required_workflows = work_item.required_checks_as_workflows()
        pr_number = int(data["pr_number"])
        expected_head_sha = str(data["expected_head_sha"])
        expected_branch = str(data.get("expected_branch", work_item.target_branch))
        authority_digest = str(data.get("authority_digest", work_item.digest))
        repo_dir = str(data.get("repo_dir", "."))
        test_command = str(data.get("test_command", ""))
        agent_completion_claim = str(data.get("agent_completion_claim", ""))

        # F11: mandatory exact binding — all fields required
        if not pr_number or pr_number <= 0:
            _print_json({"status": "SCHEMA_ERROR", "error": "pr_number_required"})
            return 10
        if not expected_head_sha:
            _print_json({"status": "SCHEMA_ERROR", "error": "expected_head_sha_required"})
            return 10
        if not expected_branch:
            _print_json({"status": "SCHEMA_ERROR", "error": "expected_branch_required"})
            return 10
        if not authority_digest:
            _print_json({"status": "SCHEMA_ERROR", "error": "authority_digest_required"})
            return 10

        # Collect live evidence through injectable adapters
        try:
            evidence = evidence_adapter.collect_live_evidence(
                execution_id=work_item.execution_id,
                repository=work_item.repository,
                base_sha=work_item.base_sha,
                expected_head_sha=expected_head_sha,
                pr_number=pr_number,
                required_workflows=required_workflows,
                expected_branch=expected_branch,
                authority_digest=authority_digest,
                work_item=work_item,
                git_adapter=evidence_adapter.LiveGitAdapter(repo_dir),
                github_adapter=None,  # uses LiveGitHubAdapter
                test_command_runner=evidence_adapter.LiveCommandRunner(repo_dir) if test_command else None,
                test_command=test_command,
                agent_completion_claim=agent_completion_claim,
            )
        except EvidenceCollectionError as exc:
            _print_json({"status": "LIVE_COLLECTION_ERROR", "code": exc.code, "detail": exc.detail})
            return 60
        except GitHubAdapterError as exc:
            _print_json({"status": "LIVE_COLLECTION_ERROR", "code": exc.code, "detail": exc.detail})
            return 60

        # F11: validate exact binding
        try:
            evidence.validate_exact_binding(
                work_item,
                expected_head_sha=expected_head_sha,
                expected_pr_number=pr_number,
                expected_branch=expected_branch,
                authority_digest=authority_digest,
            )
        except Exception as exc:
            _print_json({"status": "BINDING_ERROR", "error": str(exc)})
            return 50

        # Evaluate acceptance
        binding = ExecutionBinding(
            work_item=work_item,
            attempt=int(data.get("attempt", 1)),
            expected_head_sha=expected_head_sha,
            expected_pr_number=pr_number,
        )
        result = acceptance.evaluate_acceptance(binding, evidence)
        _print_json(result.to_mapping())
        if result.status == "ACCEPTED":
            return 0
        if result.status == "REWORK_REQUIRED":
            return 40
        return 50
    except policy_adapter.PolicyViolation as exc:
        _print_json({"status": "POLICY_VIOLATION", "code": exc.code, "detail": exc.detail})
        return 20
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        _print_json({"status": "SCHEMA_ERROR", "error": str(exc)})
        return 10


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_COMMANDS = {
    "validate-work-item": cmd_validate_work_item,
    "create-binding": cmd_create_binding,
    "generate-prompt": cmd_generate_prompt,
    "ingest-events": cmd_ingest_events,
    "evaluate-acceptance": cmd_evaluate_acceptance,
    "evaluate-live-acceptance": cmd_evaluate_live_acceptance,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in ("-h", "--help"):
        print("Usage: python -m reverse_agent.platform_v1.cli <command> [options]")
        print(f"Commands: {', '.join(sorted(_COMMANDS))}")
        return 0
    command = args[0]
    handler = _COMMANDS.get(command)
    if handler is None:
        _print_json({"status": "UNKNOWN_COMMAND", "command": command})
        return 10
    return handler(args[1:])


if __name__ == "__main__":
    sys.exit(main())
