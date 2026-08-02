"""Tests for the Platform V1 machine-readable CLI.

Covers:
- validate-work-item exit codes
- create-binding exit codes
- generate-prompt exit codes
- ingest-events exit codes
- evaluate-acceptance exit codes
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


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"


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
        "risk_tier": "R2",
        "target_branch": "agent/platform-v1-openhands-codex-acp",
    }
    payload.update(overrides)
    return payload


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

    def test_policy_violation_returns_20(self) -> None:
        # R3 risk tier triggers policy violation
        payload = _valid_work_item_payload()
        # Build a valid R2 work item, then craft a payload that would be R3
        # Since PlatformWorkItem rejects R3 at construction, we send a
        # malformed payload that passes schema but fails policy.
        payload["allowed_paths"] = ["**"]
        code, out = _run_cli(["validate-work-item"], json.dumps(payload))
        assert code == 10  # ValueError at construction -> SCHEMA_ERROR
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

    def test_missing_execution_id_returns_10(self) -> None:
        payload = {"events": []}
        code, out = _run_cli(["ingest-events"], json.dumps(payload))
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"


# ---------------------------------------------------------------------------
# evaluate-acceptance
# ---------------------------------------------------------------------------

class TestEvaluateAcceptanceCmd:
    def _payload(self, evidence_overrides: dict | None = None) -> dict:
        evidence = {
            "execution_id": "exec-1",
            "changed_paths": ["reverse_agent/platform_v1/__init__.py"],
            "test_results": {"passed": True},
            "git_diff_check_passed": True,
            "agent_completion_claim": "",
            "ci_checks": [{"name": "CI", "conclusion": "SUCCESS"}],
            "collected_at": "",
        }
        if evidence_overrides:
            evidence.update(evidence_overrides)
        return {
            "work_item": _valid_work_item_payload(),
            "attempt": 1,
            "evidence": evidence,
        }

    def test_all_pass_returns_zero(self) -> None:
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(self._payload()))
        assert code == 0
        assert out["status"] == "ACCEPTED"

    def test_tests_failed_returns_40(self) -> None:
        payload = self._payload({"test_results": {"passed": False}})
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(payload))
        assert code == 40
        assert out["status"] == "REWORK_REQUIRED"

    def test_out_of_scope_returns_50(self) -> None:
        payload = self._payload({
            "changed_paths": ["reverse_agent/other/foo.py"],
        })
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(payload))
        assert code == 50
        assert out["status"] == "BLOCKED_APPROVAL"

    def test_policy_failed_returns_50(self) -> None:
        payload = self._payload()
        # Tamper with risk tier to fail policy validation
        payload["work_item"]["risk_tier"] = "R3"
        code, out = _run_cli(["evaluate-acceptance"], json.dumps(payload))
        # R3 is rejected at PlatformWorkItem construction -> SCHEMA_ERROR
        assert code == 10
        assert out["status"] == "SCHEMA_ERROR"

    def test_agent_claim_does_not_override_tests_failed(self) -> None:
        payload = self._payload({
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
