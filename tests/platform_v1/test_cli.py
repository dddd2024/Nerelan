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

import pytest

from reverse_agent.platform_v1.cli import main
from reverse_agent.platform_v1.contracts import PlatformWorkItem


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
VALID_HEAD_SHA = "e702a3c5f50b9373e0af8087a76268d4a01cd9b1"
VALID_ISSUE_BODY_DIGEST = "a" * 40


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
        "ci_checks": [{"name": "CI", "conclusion": "SUCCESS"}],
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

    def test_all_pass_returns_zero(self) -> None:
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(self._payload()))
        assert code == 0
        assert out["status"] == "ACCEPTED"
        assert out["live_ready"] is False  # fixture evidence

    def test_all_pass_live_returns_zero_and_live_ready(self) -> None:
        code, out = _run_cli(
            ["evaluate-acceptance"],
            json.dumps(self._payload(evidence_overrides={"collection_mode": "live"})),
        )
        assert code == 0
        assert out["status"] == "ACCEPTED"
        assert out["live_ready"] is True

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
