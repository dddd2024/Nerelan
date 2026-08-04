"""Tests for the Platform V1 machine-readable CLI.

Covers:
- validate-work-item exit codes (R0 valid; R2 blocked_approval)
- create-binding exit codes
- generate-prompt exit codes
- ingest-events exit codes (with new required binding parameters)
- evaluate-acceptance exit codes (evidence binding must match)
- stable error codes for policy/schema errors
- unknown command handling
- help output
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from reverse_agent.platform_v1.cli import main
from reverse_agent.platform_v1.authority_adapter import AuthorityBundle, PRE_MERGE_WORKFLOW_KEYS
from reverse_agent.platform_v1.contracts import PlatformWorkItem
from reverse_agent.platform_v1.evidence_adapter import _create_trusted_evidence


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
VALID_HEAD_SHA = "e702a3c5f50b9373e0af8087a76268d4a01cd9b1"
VALID_ISSUE_BODY_DIGEST = "a" * 64  # F25: SHA-256, 64 hex chars


def _live_bundle(risk_tier: str) -> AuthorityBundle:
    return AuthorityBundle(
        decision_id="decision_test",
        round_id="round_test",
        decision_content_sha256="a" * 64,
        command_plan_sha256="b" * 64,
        allowed_command_ids=(),
        allowed_commands=(),
        issue_number=100,
        issue_body_sha256=VALID_ISSUE_BODY_DIGEST,
        issue_state="OPEN",
        issue_labels=("work-item", "r2", "owner-accepted"),
        repository="dddd2024/reverse-agent",
        pr_number=97,
        branch="agent/platform-v1-openhands-codex-acp",
        base_sha=VALID_BASE_SHA,
        risk_tier=risk_tier,
        intent_id="intent_test",
        intent_decision_content_sha256="a" * 64,
        intent_command_plan_sha256="b" * 64,
        allowed_paths=("reverse_agent/platform_v1/**",),
        required_workflow_keys=PRE_MERGE_WORKFLOW_KEYS,
        pr_state="OPEN",
        pr_is_draft=True,
        pr_head_ref_name="agent/platform-v1-openhands-codex-acp",
        pr_head_ref_oid=VALID_HEAD_SHA,
        pr_base_ref_name="main",
        pr_base_ref_oid=VALID_BASE_SHA,
    )


def _run_cli(args: list[str], stdin_data: str = "") -> tuple[int, dict]:
    """Run the CLI with stdin and return (exit_code, parsed_json)."""

    stdin_buf = io.StringIO(stdin_data)
    stdout_buf = io.StringIO()
    old_stdin, old_stdout = __import__("sys").stdin, __import__("sys").stdout
    try:
        __import__("sys").stdin = stdin_buf
        with redirect_stdout(stdout_buf):
            code = main(args)
    finally:
        __import__("sys").stdin = old_stdin
        __import__("sys").stdout = old_stdout
    out = stdout_buf.getvalue().strip()
    try:
        parsed = json.loads(out) if out else {}
    except json.JSONDecodeError:
        parsed = {"_raw": out}
    return code, parsed


def _valid_work_item_payload(**overrides) -> dict:
    payload = {
        "source_issue_number": 96,
        "repository": "dddd2024/reverse-agent",
        "base_sha": VALID_BASE_SHA,
        "allowed_paths": ["reverse_agent/platform_v1/**", "tests/platform_v1/**"],
        "forbidden_operations": ["push_main", "merge"],
        "acceptance_criteria": ["pytest passes"],
        "goal": "test goal",
        "required_checks": ["pytest"],
        "approved_issue_body_digest": VALID_ISSUE_BODY_DIGEST,
        # R0 so the work item passes policy and the CLI commands succeed.
        # Tests that need R2 override this explicitly.
        "risk_tier": "R0",
        "target_branch": "agent/platform-v1-openhands-codex-acp",
    }
    payload.update(overrides)
    return payload


def _evidence_payload_for(work_item_payload: dict, **evidence_overrides) -> dict:
    """Build an evidence payload whose execution_id matches the work item.

    The evidence binding requires execution_id, repository, and base_sha to
    match the work item. We construct the work item first to read its
    execution_id, then seed the evidence with it.
    """

    work_item = PlatformWorkItem.from_mapping(work_item_payload)
    evidence = {
        "execution_id": work_item.execution_id,
        "repository": work_item.repository,
        "base_sha": work_item.base_sha,
        "head_sha": VALID_HEAD_SHA,
        "pr_number": 97,
        "required_workflows": ["CI"],
        "changed_paths": ["reverse_agent/platform_v1/__init__.py"],
        "test_results": {"passed": True},
        "git_diff_check_passed": True,
        "agent_completion_claim": "",
        "ci_checks": [{"name": "CI", "status": "completed", "conclusion": "success"}],
        "collected_at": "",
        "collection_mode": "fixture",
        "provenance": "caller_asserted",
    }
    evidence.update(evidence_overrides)
    return evidence


# ---------------------------------------------------------------------------
# validate-work-item
# ---------------------------------------------------------------------------

class TestValidateWorkItemCmd:
    def test_valid_work_item_returns_zero(self) -> None:
        code, out = _run_cli(["validate-work-item"], json.dumps(_valid_work_item_payload()))
        assert code == 0
        assert out["status"] == "VALID"
        assert out["execution_id"].startswith("exec-issue-96-")
        assert out["branch_name"] == "agent/platform-v1-openhands-codex-acp"
        assert "digest" in out

    def test_schema_error_returns_10(self) -> None:
        code, out = _run_cli(["validate-work-item"], "{not valid json")
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"

    def test_R2_returns_20_blocked_approval(self) -> None:
        # R2 is valid at construction but blocked by policy.
        payload = _valid_work_item_payload(risk_tier="R2")
        code, out = _run_cli(["validate-work-item"], json.dumps(payload))
        assert code == 20
        assert out["status"] == "POLICY_VIOLATION"
        assert out["code"] == "blocked_approval"
        assert out["detail"] == "R2"

    def test_broad_path_returns_10_schema_error(self) -> None:
        # broad path is rejected at construction -> SCHEMA_ERROR
        payload = _valid_work_item_payload()
        payload["allowed_paths"] = ["**"]
        code, out = _run_cli(["validate-work-item"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"


# ---------------------------------------------------------------------------
# create-binding
# ---------------------------------------------------------------------------

class TestCreateBindingCmd:
    def test_valid_binding_returns_zero(self) -> None:
        code, out = _run_cli(["create-binding"], json.dumps(_valid_work_item_payload()))
        assert code == 0
        assert out["status"] == "BOUND"
        assert out["attempt"] == 1
        assert out["is_retry"] is False

    def test_retry_attempt_returns_zero(self) -> None:
        payload = _valid_work_item_payload()
        payload["attempt"] = 2
        code, out = _run_cli(["create-binding"], json.dumps(payload))
        assert code == 0
        assert out["attempt"] == 2
        assert out["is_retry"] is True

    def test_third_attempt_rejected(self) -> None:
        payload = _valid_work_item_payload()
        payload["attempt"] = 3
        code, out = _run_cli(["create-binding"], json.dumps(payload))
        # ValueError at construction -> SCHEMA_ERROR (exit 10)
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"

    def test_R2_returns_20_blocked_approval(self) -> None:
        payload = _valid_work_item_payload(risk_tier="R2")
        code, out = _run_cli(["create-binding"], json.dumps(payload))
        assert code == 20
        assert out["status"] == "POLICY_VIOLATION"
        assert out["code"] == "blocked_approval"


# ---------------------------------------------------------------------------
# generate-prompt
# ---------------------------------------------------------------------------

class TestGeneratePromptCmd:
    def test_valid_work_item_returns_zero(self) -> None:
        code, out = _run_cli(["generate-prompt"], json.dumps(_valid_work_item_payload()))
        assert code == 0
        assert out["status"] == "OK"
        assert "prompt" in out
        assert "execution_id" in out["prompt"]
        assert "test goal" in out["prompt"]
        assert "pytest" in out["prompt"]

    def test_R2_returns_20_blocked_approval(self) -> None:
        payload = _valid_work_item_payload(risk_tier="R2")
        code, out = _run_cli(["generate-prompt"], json.dumps(payload))
        assert code == 20
        assert out["status"] == "POLICY_VIOLATION"
        assert out["code"] == "blocked_approval"

    def test_prompt_does_not_contain_credential_values(self) -> None:
        code, out = _run_cli(["generate-prompt"], json.dumps(_valid_work_item_payload()))
        prompt = out["prompt"]
        # The prompt may instruct the agent not to access secrets, but it
        # must never contain actual credential values or env-var names.
        forbidden_tokens = [
            "GITHUB_TOKEN=",
            "CODEX_API_KEY=",
            "OPENAI_API_KEY=",
            "ANTHROPIC_API_KEY=",
            "LLM_API_KEY=",
            "ghp_",
            "sk-",
            "Bearer ",
            "password=",
            "api_key=",
            "secret=",
        ]
        for token in forbidden_tokens:
            assert token not in prompt, f"prompt must not contain credential pattern {token!r}"


# ---------------------------------------------------------------------------
# ingest-events
# ---------------------------------------------------------------------------

class TestIngestEventsCmd:
    def test_valid_events_returns_zero(self) -> None:
        payload = {
            "execution_id": "exec-1",
            "repository": "dddd2024/reverse-agent",
            "base_sha": VALID_BASE_SHA,
            "head_sha": VALID_HEAD_SHA,
            "pr_number": 97,
            "required_workflows": ["CI"],
            "events": [
                {"type": "workspace.file_write", "path": "a.py"},
                {"type": "agent.completion_claim", "claim": "done"},
            ],
        }
        code, out = _run_cli(["ingest-events"], json.dumps(payload))
        assert code == 0
        assert out["status"] == "OK"
        assert "a.py" in out["evidence"]["changed_paths"]
        assert out["evidence"]["agent_completion_claim"] == "done"
        assert out["evidence"]["repository"] == "dddd2024/reverse-agent"
        assert out["evidence"]["base_sha"] == VALID_BASE_SHA
        assert out["evidence"]["head_sha"] == VALID_HEAD_SHA
        assert out["evidence"]["pr_number"] == 97
        assert out["evidence"]["collection_mode"] == "fixture"
        assert out["evidence"]["provenance"] == "agent_event_stream"

    def test_missing_execution_id_returns_10(self) -> None:
        payload = {
            "events": [],
            "repository": "dddd2024/reverse-agent",
            "base_sha": VALID_BASE_SHA,
            "head_sha": VALID_HEAD_SHA,
            "pr_number": 97,
            "required_workflows": ["CI"],
        }
        code, out = _run_cli(["ingest-events"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"

    def test_missing_repository_returns_10(self) -> None:
        payload = {
            "execution_id": "exec-1",
            "base_sha": VALID_BASE_SHA,
            "head_sha": VALID_HEAD_SHA,
            "pr_number": 97,
            "required_workflows": ["CI"],
            "events": [],
        }
        code, out = _run_cli(["ingest-events"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"


# ---------------------------------------------------------------------------
# evaluate-acceptance
# ---------------------------------------------------------------------------

class TestEvaluateAcceptanceCmd:
    def _payload(self, work_item_overrides: dict | None = None, evidence_overrides: dict | None = None) -> dict:
        work_item_payload = _valid_work_item_payload()
        if work_item_overrides:
            work_item_payload.update(work_item_overrides)
        evidence = _evidence_payload_for(work_item_payload)
        if evidence_overrides:
            evidence.update(evidence_overrides)
        return {
            "work_item": work_item_payload,
            "attempt": 1,
            "evidence": evidence,
        }

    def test_all_pass_fixture_returns_41(self) -> None:
        # F9: fixture evidence returns FIXTURE_VALIDATED (exit 41), not ACCEPTED (exit 0)
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(self._payload()))
        assert code == 41
        assert out["status"] == "FIXTURE_VALIDATED"
        assert out["live_ready"] is False

    def test_stdin_collection_mode_live_still_returns_fixture(self) -> None:
        # F9: stdin collection_mode=live cannot produce live_ready
        code, out = _run_cli(
            ["evaluate-acceptance"],
            json.dumps(self._payload(evidence_overrides={"collection_mode": "live"})),
        )
        assert code == 41
        assert out["status"] == "FIXTURE_VALIDATED"
        assert out["live_ready"] is False

    def test_stdin_trusted_provenance_still_returns_fixture(self) -> None:
        # F9: stdin trusted provenance cannot produce live_ready
        code, out = _run_cli(
            ["evaluate-acceptance"],
            json.dumps(self._payload(evidence_overrides={
                "collection_mode": "live",
                "provenance": "trusted_git_github_collector",
            })),
        )
        assert code == 41
        assert out["status"] == "FIXTURE_VALIDATED"
        assert out["live_ready"] is False

    def test_tests_failed_returns_40(self) -> None:
        payload = self._payload(evidence_overrides={"test_results": {"passed": False}})
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(payload))
        assert code == 40
        assert out["status"] == "REWORK_REQUIRED"

    def test_out_of_scope_returns_50(self) -> None:
        # changed_paths outside the allowed scope -> BLOCKED_APPROVAL
        work_item_payload = _valid_work_item_payload()
        evidence = _evidence_payload_for(work_item_payload)
        evidence["changed_paths"] = ["reverse_agent/other/foo.py"]
        payload = {"work_item": work_item_payload, "attempt": 1, "evidence": evidence}
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(payload))
        assert code == 50
        assert out["status"] == "BLOCKED_APPROVAL"
        assert any("out_of_scope" in r for r in out["reasons"])

    def test_R2_returns_50_blocked_approval(self) -> None:
        # R2 is valid at construction but blocked by policy -> BLOCKED_APPROVAL
        payload = self._payload(work_item_overrides={"risk_tier": "R2"})
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(payload))
        assert code == 50
        assert out["status"] == "BLOCKED_APPROVAL"
        assert any("blocked_approval" in r for r in out["reasons"])

    def test_R3_returns_50_blocked_approval(self) -> None:
        # R3 is valid at construction but blocked by policy -> BLOCKED_APPROVAL
        payload = self._payload(work_item_overrides={"risk_tier": "R3"})
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(payload))
        assert code == 50
        assert out["status"] == "BLOCKED_APPROVAL"
        assert any("blocked_approval" in r for r in out["reasons"])

    def test_evidence_binding_mismatch_returns_50_failed_terminal(self) -> None:
        # evidence execution_id doesn't match work_item -> FAILED_TERMINAL
        work_item_payload = _valid_work_item_payload()
        evidence = _evidence_payload_for(work_item_payload)
        evidence["execution_id"] = "exec-different"
        payload = {"work_item": work_item_payload, "attempt": 1, "evidence": evidence}
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(payload))
        assert code == 50
        assert out["status"] == "FAILED_TERMINAL"
        assert any("evidence_binding_failed" in r for r in out["reasons"])

    def test_agent_claim_does_not_override_tests_failed(self) -> None:
        payload = self._payload(evidence_overrides={
            "test_results": {"passed": False},
            "agent_completion_claim": "All tests pass. Task done.",
        })
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(payload))
        assert code == 40
        assert any("agent_claim_ignored" in r for r in out["reasons"])


# ---------------------------------------------------------------------------
# evaluate-live-acceptance (F10/F11/F18/F19/F20/F26/F27)
# ---------------------------------------------------------------------------

class TestEvaluateLiveAcceptanceCmd:
    """F18/F20/F26: The live path accepts ONLY target identifiers from stdin.

    stdin Work Item payloads, ``authority_digest``, ``test_command``,
    ``expected_head_sha``, and ``expected_branch`` are all rejected.
    Authority is loaded internally from repository state and GitHub facts.
    """

    def _identifier_payload(self, **overrides) -> dict:
        payload = {
            "repo_dir": ".",
            "repository": "dddd2024/reverse-agent",
            "issue_number": 100,
            "pr_number": 97,
        }
        payload.update(overrides)
        return payload

    # --- F18/F20: stdin Work Item forbidden ---

    def test_stdin_work_item_forbidden(self) -> None:
        payload = self._identifier_payload()
        payload["work_item"] = _valid_work_item_payload()
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"
        assert out.get("error") == "stdin_work_item_forbidden"

    def test_stdin_authority_digest_forbidden(self) -> None:
        payload = self._identifier_payload()
        payload["authority_digest"] = "a" * 64
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"
        assert out.get("error") == "stdin_authority_digest_forbidden"

    def test_stdin_test_command_forbidden(self) -> None:
        payload = self._identifier_payload()
        payload["test_command"] = "python -m pytest"
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"
        assert out.get("error") == "stdin_test_command_forbidden"

    def test_stdin_expected_head_sha_forbidden(self) -> None:
        payload = self._identifier_payload()
        payload["expected_head_sha"] = VALID_HEAD_SHA
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"
        assert out.get("error") == "stdin_binding_forbidden"

    def test_stdin_expected_branch_forbidden(self) -> None:
        payload = self._identifier_payload()
        payload["expected_branch"] = "agent/platform-v1-openhands-codex-acp"
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"
        assert out.get("error") == "stdin_binding_forbidden"

    # --- Target identifier validation ---

    def test_missing_repository_returns_schema_error(self) -> None:
        payload = self._identifier_payload(repository="")
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"
        assert out.get("error") == "repository_required"

    def test_missing_issue_number_returns_schema_error(self) -> None:
        payload = self._identifier_payload()
        del payload["issue_number"]
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"
        assert out.get("error") == "issue_number_required"

    def test_zero_issue_number_returns_schema_error(self) -> None:
        payload = self._identifier_payload(issue_number=0)
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"
        assert out.get("error") == "issue_number_required"

    def test_missing_pr_number_returns_schema_error(self) -> None:
        payload = self._identifier_payload()
        del payload["pr_number"]
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"

    def test_zero_pr_number_returns_schema_error(self) -> None:
        payload = self._identifier_payload(pr_number=0)
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"
        assert out.get("error") == "pr_number_required"

    def test_non_integer_issue_number_returns_schema_error(self) -> None:
        payload = self._identifier_payload(issue_number="abc")
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"
        assert out.get("error") == "issue_number_must_be_int"

    # --- F10: raw evidence object not accepted ---

    def test_raw_evidence_object_not_accepted(self) -> None:
        # F10: The live path must not accept a raw evidence object.
        # Even if the caller provides an "evidence" key with all-success
        # values and collection_mode=live, the command must NOT return
        # ACCEPTED. It collects its own evidence through injectable adapters.
        payload = self._identifier_payload()
        payload["evidence"] = {
            "execution_id": "exec-forged",
            "collection_mode": "live",
            "provenance": "trusted_git_github_collector",
            "test_results": {"passed": True},
            "ci_checks": [{"name": "CI", "status": "completed", "conclusion": "success"}],
            "git_diff_check_passed": True,
        }
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        # The command must NOT return 0 (ACCEPTED) — it ignores the evidence
        # key and tries to collect real evidence via the Authority Bundle.
        assert code != 0
        assert out.get("status") != "ACCEPTED"

    # --- Authority loading (will fail without real GitHub access) ---

    def test_valid_identifiers_trigger_authority_loading(self) -> None:
        # With valid identifiers but no real GitHub access (or repository
        # state mismatch), the command must NOT return ACCEPTED.
        # It should return AUTHORITY_ERROR or LIVE_COLLECTION_ERROR.
        payload = self._identifier_payload()
        code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code != 0
        assert out.get("status") != "ACCEPTED"

    def test_actual_r2_cli_returns_blocked_approval_before_collection(self) -> None:
        payload = self._identifier_payload()
        with patch(
            "reverse_agent.platform_v1.cli.authority_adapter.load_authority_bundle",
            return_value=_live_bundle("R2"),
        ), patch(
            "reverse_agent.platform_v1.cli.evidence_adapter.collect_live_evidence",
        ) as collect:
            code, out = _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        assert code == 50
        assert out["status"] == "BLOCKED_APPROVAL"
        collect.assert_not_called()

    def test_production_live_cli_never_constructs_live_command_runner(self) -> None:
        payload = self._identifier_payload()
        evidence = _create_trusted_evidence(
            execution_id="exec-test",
            repository="dddd2024/reverse-agent",
            base_sha=VALID_BASE_SHA,
            head_sha=VALID_HEAD_SHA,
            pr_number=97,
            required_workflows=(
                "CI", "Decision Preflight", "State Gate (pull_request_target)",
            ),
            changed_paths=("reverse_agent/platform_v1/cli.py",),
            test_results={"passed": True, "source": "verified_state_gate_receipt"},
            git_diff_check_passed=True,
            ci_checks=(
                {"name": "CI", "status": "COMPLETED", "conclusion": "SUCCESS"},
                {"name": "Decision Preflight", "status": "COMPLETED", "conclusion": "SUCCESS"},
                {"name": "State Gate (pull_request_target)", "status": "COMPLETED", "conclusion": "SUCCESS"},
            ),
        )
        with patch(
            "reverse_agent.platform_v1.cli.authority_adapter.load_authority_bundle",
            return_value=_live_bundle("R0"),
        ), patch(
            "reverse_agent.platform_v1.cli.evidence_adapter.collect_live_evidence",
            return_value=evidence,
        ) as collect, patch(
            "reverse_agent.platform_v1.cli.evidence_adapter.LiveCommandRunner",
            side_effect=AssertionError("candidate runner must not be constructed"),
        ) as runner:
            _run_cli(["evaluate-live-acceptance"], json.dumps(payload))
        collect.assert_called_once()
        runner.assert_not_called()


# ---------------------------------------------------------------------------
# unknown command / help
# ---------------------------------------------------------------------------

class TestCliMisc:
    def test_unknown_command_returns_10(self) -> None:
        code, out = _run_cli(["nonexistent-command"])
        assert code == 10
        assert out["status"] == "UNKNOWN_COMMAND"

    def test_no_args_prints_help(self) -> None:
        code, out = _run_cli([])
        assert code == 0
        assert "_raw" in out
        assert "Usage" in out["_raw"]

    def test_help_flag_prints_help(self) -> None:
        code, out = _run_cli(["--help"])
        assert code == 0
        assert "_raw" in out
        assert "Usage" in out["_raw"]
