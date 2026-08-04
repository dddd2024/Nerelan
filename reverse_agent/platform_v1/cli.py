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

F18/F20/F26: The live path accepts ONLY target identifiers from stdin
(``repo_dir``, ``repository``, ``issue_number``, ``pr_number``). The
Authority Bundle is loaded internally from ``project_state/decision_packet.md``,
``project_state/gates/command_plan.json``,
``project_state/mainline_merge_intents/active.json``, GitHub Issue, and
GitHub PR. stdin Work Item payloads, ``authority_digest``, and
``test_command`` are rejected.

F19: Test commands are selected by ``command_id`` from the approved Command
Plan. Caller-supplied shell text is never executed.

F27: Live evidence is created only by the trusted factory in
:func:`evidence_adapter._create_trusted_evidence`.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Sequence

from . import acceptance, authority_adapter, evidence_adapter, openhands_adapter, policy_adapter
from .contracts import (
    ExecutionBinding,
    ExecutionEvidence,
    PlatformAcceptanceResult,
    PlatformWorkItem,
)
from .evidence_adapter import EvidenceCollectionError
from .github_adapter import GitHubAdapterError, composite_name


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
    """Evaluate live acceptance by collecting trusted facts through Authority Bundle.

    F18/F20/F26: Accepts ONLY target identifiers from stdin:
    ``repo_dir``, ``repository``, ``issue_number``, ``pr_number``.
    The Authority Bundle is loaded internally from repository state and
    GitHub facts. stdin Work Item payloads, ``authority_digest``, and
    ``test_command`` are rejected.

    v10/F3: The credential-bearing live path never runs candidate repository
    commands. Candidate test success comes only from a verified State Gate
    receipt returned by the production verifier.

    F27: Live evidence is created only by the trusted factory in
    :func:`evidence_adapter._create_trusted_evidence`.
    """

    try:
        data = _read_stdin_json()

        # F18: Reject stdin Work Item payload — authority must come from
        # internal repository state, not caller input.
        if "work_item" in data:
            _print_json({"status": "SCHEMA_ERROR", "error": "stdin_work_item_forbidden"})
            return 10
        # F18: Reject stdin authority_digest — the bundle cross-validates
        # digests internally; caller cannot supply them.
        if "authority_digest" in data:
            _print_json({"status": "SCHEMA_ERROR", "error": "stdin_authority_digest_forbidden"})
            return 10
        # F19: Reject stdin test_command — commands must be selected by
        # command_id from the approved Command Plan.
        if "test_command" in data:
            _print_json({"status": "SCHEMA_ERROR", "error": "stdin_test_command_forbidden"})
            return 10
        # Reject stdin expected_head_sha/expected_branch — these come from
        # the Authority Bundle's PR observations, not from the caller.
        if "expected_head_sha" in data or "expected_branch" in data:
            _print_json({"status": "SCHEMA_ERROR", "error": "stdin_binding_forbidden"})
            return 10

        # F20/F26: Accept ONLY target identifiers from stdin
        repo_dir = str(data.get("repo_dir", "."))
        repository = str(data.get("repository", ""))
        try:
            issue_number = int(data.get("issue_number", 0))
        except (TypeError, ValueError):
            _print_json({"status": "SCHEMA_ERROR", "error": "issue_number_must_be_int"})
            return 10
        try:
            pr_number = int(data.get("pr_number", 0))
        except (TypeError, ValueError):
            _print_json({"status": "SCHEMA_ERROR", "error": "pr_number_must_be_int"})
            return 10
        agent_completion_claim = str(data.get("agent_completion_claim", ""))

        # Validate target identifiers
        if not repository or "/" not in repository:
            _print_json({"status": "SCHEMA_ERROR", "error": "repository_required"})
            return 10
        if issue_number <= 0:
            _print_json({"status": "SCHEMA_ERROR", "error": "issue_number_required"})
            return 10
        if pr_number <= 0:
            _print_json({"status": "SCHEMA_ERROR", "error": "pr_number_required"})
            return 10

        # F20/F26: Load Authority Bundle internally — this cross-validates
        # Decision, Command Plan, merge intent, Issue body SHA-256, and PR
        # metadata. Raises AuthorityBundleError on any mismatch.
        try:
            bundle = authority_adapter.load_authority_bundle(
                repo_dir=repo_dir,
                repository=repository,
                issue_number=issue_number,
                pr_number=pr_number,
            )
        except authority_adapter.AuthorityBundleError as exc:
            _print_json({
                "status": "AUTHORITY_ERROR",
                "code": exc.code,
                "detail": exc.detail,
                "execution_id": f"exec-issue-{issue_number}-authority-error",
            })
            return 50

        # Build a Work Item from the bundle for the acceptance evaluator.
        # The Work Item's approved_issue_body_digest is the SHA-256 of the
        # observed Issue body — never caller-supplied.
        required_workflows_tuple = tuple(
            composite_name(wf, ev) for wf, ev in bundle.required_workflow_keys
        )
        work_item = PlatformWorkItem(
            source_issue_number=bundle.issue_number,
            repository=bundle.repository,
            base_sha=bundle.base_sha,
            allowed_paths=bundle.allowed_paths,
            forbidden_operations=(
                "push_main", "merge", "mark_ready", "auto_merge",
                "release", "deployment", "force_push", "rebase",
                "squash", "tag_or_release", "credential_access",
            ),
            acceptance_criteria=("all_required_workflows_success_on_exact_head",),
            goal="platform_v1_authority_collector_live_acceptance",
            required_checks=required_workflows_tuple,
            approved_issue_body_digest=bundle.issue_body_sha256,
            risk_tier=bundle.risk_tier,
            target_branch=bundle.branch,
        )

        # R2/R3 risk tiers are blocked before any backend invocation.
        # The acceptance evaluator enforces this, but we short-circuit here
        # to avoid spinning up live collectors that cannot be used.
        if bundle.risk_tier in ("R2", "R3"):
            _print_json({
                "status": "BLOCKED_APPROVAL",
                "execution_id": work_item.execution_id,
                "reasons": [f"blocked_approval:risk_tier={bundle.risk_tier}"],
                "live_ready": False,
            })
            return 50

        # F27: Collect trusted live evidence through injectable adapters.
        # The collector owns truth — it does not accept caller-supplied test
        # pass/fail booleans, CI success lists, or shell commands.
        try:
            evidence = evidence_adapter.collect_live_evidence(
                bundle=bundle,
                git_adapter=evidence_adapter.LiveGitAdapter(repo_dir),
                github_adapter=None,  # uses LiveGitHubAdapter
                agent_completion_claim=agent_completion_claim,
                repo_dir=repo_dir,
            )
        except EvidenceCollectionError as exc:
            _print_json({
                "status": "LIVE_COLLECTION_ERROR",
                "execution_id": work_item.execution_id,
                "code": exc.code,
                "detail": exc.detail,
            })
            return 60
        except GitHubAdapterError as exc:
            _print_json({
                "status": "LIVE_COLLECTION_ERROR",
                "execution_id": work_item.execution_id,
                "code": exc.code,
                "detail": exc.detail,
            })
            return 60

        # Build binding with exact head and PR number from the bundle.
        binding = ExecutionBinding(
            work_item=work_item,
            attempt=1,
            expected_head_sha=bundle.pr_head_ref_oid,
            expected_pr_number=bundle.pr_number,
        )
        result = acceptance.evaluate_acceptance(binding, evidence)
        _print_json(result.to_mapping())
        if result.status == "ACCEPTED":
            return 0
        if result.status == "REWORK_REQUIRED":
            return 40
        return 50
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
