"""Nested OpenCode error-diagnostic retention tests (T001).

These tests exercise the real ``OpenCodeExecutor._run_executor_core`` (and one
end-to-end ``execute()``) path via an injected fake ``OwnedCliProcessResult``
and a real in-memory ``TaskStore`` with retained callback events. They verify
that a bounded, allowlisted, redacted diagnostic is retained in the returned
``ExecutorResult``, the persisted ``EXECUTOR_FINISHED`` event metadata and the
persisted ``ExecutorAction`` evidence rows, even when stderr is empty, and that
explicit ``ECONNRESET`` (and equivalent exact codes) classify as
``network_provider_failure`` while policy/entitlement/overload precedence and
the generic fallback stay intact.

No live OpenCode invocation occurs. No auth files are accessed.
"""

import json
import subprocess

import pytest

from reverse_agent.platform_v1.opencode_executor import (
    MAX_EVIDENCE_STRING_LEN,
    OpenCodeExecutor,
    OwnedCliProcessResult,
    _bounded_error_diagnostic,
    _single_error_diagnostic,
)
from reverse_agent.platform_v1.run_store import TaskStore


def _executor() -> OpenCodeExecutor:
    return OpenCodeExecutor(model_id="provider/model", opencode_exe="/fake/opencode")


def _run_core(
    monkeypatch,
    tmp_path,
    *,
    stdout: str,
    stderr: str = "",
    returncode: int = 1,
    collect_changed_files=None,
) -> tuple:
    """Run the real _run_executor_core with an injected OwnedCliProcessResult.

    Returns (result, events, store, task_id)."""
    from reverse_agent.platform_v1 import opencode_executor as oe

    store = TaskStore(":memory:")
    task = store.create_task(
        title="nested error diagnostic", executor_kind="opencode"
    )
    monkeypatch.setattr(
        oe,
        "_run_owned_cli_process",
        lambda argv, *, cwd, env, timeout: OwnedCliProcessResult(
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            timed_out=False,
            cleanup_confirmed=True,
        ),
    )
    monkeypatch.setattr(
        oe, "_collect_changed_files", collect_changed_files or (lambda *a: [])
    )
    events: list[dict] = []
    result = _executor()._run_executor_core(
        task_id=task.id,
        store=store,
        worktree=tmp_path,
        base_sha="controlled",
        execution_id="exec-diag",
        cli_path="/fake/opencode",
        is_cmd=False,
        event_callback=lambda _tid, ev: events.append(ev),
        role_context=oe.RoleContext(
            role="executor", task_id=task.id, workspace=tmp_path
        ),
    )
    return result, events, store, task.id


def _evidence_rows(store, task_id) -> list[dict]:
    return [
        dict(r)
        for r in store._conn.execute(
            "SELECT category, label, value, status, detail "
            "FROM task_evidence WHERE task_id = ? ORDER BY rowid",
            (task_id,),
        ).fetchall()
    ]


def _econnreset_payload() -> dict:
    return {
        "type": "error",
        "error": {
            "name": "APIError",
            "data": {
                "message": (
                    "Trae CN: ECONNRESET: The socket connection was closed "
                    "unexpectedly."
                ),
                "statusCode": 502,
            },
        },
    }


# ---------------------------------------------------------------------------
# Core defect: empty stderr + nested 502 ECONNRESET
# ---------------------------------------------------------------------------


def test_econnreset_retains_sanitized_reason_in_result_event_and_evidence(
    monkeypatch, tmp_path
) -> None:
    payload = _econnreset_payload()
    stdout = json.dumps(payload) + "\n"
    result, events, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout=stdout, stderr=""
    )

    assert result.success is False
    assert result.failure_classification == "network_provider_failure"
    assert result.process_exit_code == 1
    # Keep the legacy prefix while carrying the cause to durable failure_detail.
    assert result.error.startswith("opencode_nonzero:exit=1:network_provider_failure ")
    assert "ECONNRESET" in result.error
    assert "status=502" in result.error
    # stderr was empty, so the sanitized reason must survive in the summary.
    assert "ECONNRESET" in result.validation_output_summary
    assert "status=502" in result.validation_output_summary
    assert "APIError" in result.validation_output_summary

    # Persisted EXECUTOR_FINISHED event carries the diagnostic.
    finished = [
        e for e in events
        if e.get("title") == "OpenCode nonzero exit"
    ]
    assert len(finished) == 1
    meta = finished[0]["metadata"]
    assert meta["failure_classification"] == "network_provider_failure"
    assert meta["stderr_summary"] == ""  # stderr genuinely empty
    assert "ECONNRESET" in meta["error_diagnostic"]
    assert "502" in meta["error_diagnostic"]
    assert "ECONNRESET" in finished[0]["description"]

    # Persisted evidence row carries the diagnostic in its value.
    rows = _evidence_rows(store, task_id)
    assert rows, "expected evidence rows for the error event"
    serialized = json.dumps(rows)
    assert "ECONNRESET" in serialized
    assert "status=502" in serialized
    # No raw arbitrary nested dict is stringified into evidence.
    assert "data" not in serialized


def test_econnreset_classifies_as_network_provider_failure() -> None:
    ex = _executor()
    classification = ex._classify_exit(1, [_econnreset_payload()])
    assert classification == "network_provider_failure"


@pytest.mark.parametrize(
    "code", ["ECONNRESET", "ECONNREFUSED", "ECONNABORTED", "ETIMEDOUT"]
)
def test_explicit_network_codes_classify_as_network_provider_failure(
    code: str,
) -> None:
    ex = _executor()
    ev = {
        "type": "error",
        "error": {"name": "APIError", "data": {"message": code + ": boom", "statusCode": 502}},
    }
    assert ex._classify_exit(1, [ev]) == "network_provider_failure"


def test_non_error_text_mentioning_econnreset_does_not_reclassify() -> None:
    ex = _executor()
    ev = {"type": "text", "data": "the docs mention ECONNRESET and invalid_api_key"}
    assert ex._classify_exit(1, [ev]) == "executor_nonzero"


# ---------------------------------------------------------------------------
# Nested unknown 502 stays generic but reports bounded useful detail
# ---------------------------------------------------------------------------


def test_unknown_502_stays_generic_but_reports_bounded_detail(
    monkeypatch, tmp_path
) -> None:
    payload = {
        "type": "error",
        "error": {
            "name": "APIError",
            "data": {
                "message": "upstream returned an unknown gateway error",
                "statusCode": 502,
            },
        },
    }
    stdout = json.dumps(payload) + "\n"
    result, events, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout=stdout, stderr=""
    )

    # No ECONNRESET -> stays generic (502 is not auto-network/quota/auth).
    assert result.failure_classification == "executor_nonzero"
    assert result.error.startswith("opencode_nonzero:exit=1:executor_nonzero ")
    assert "unknown gateway error" in result.error
    # Classification stays generic while the actual cause reaches durable consumers.
    assert "unknown gateway error" in result.validation_output_summary
    assert "status=502" in result.validation_output_summary
    rows = _evidence_rows(store, task_id)
    assert "unknown gateway error" in json.dumps(rows)


# ---------------------------------------------------------------------------
# Ordinary text / tool controls remain generic
# ---------------------------------------------------------------------------


def test_ordinary_text_and_tool_events_remain_generic(
    monkeypatch, tmp_path
) -> None:
    stdout = (
        json.dumps({"type": "text", "part": {"type": "text", "text": "hello"}})
        + "\n"
        + json.dumps({"type": "tool", "action": "read", "path": "a.txt"})
        + "\n"
    )
    result, events, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout=stdout, stderr=""
    )
    assert result.failure_classification == "executor_nonzero"
    # No error envelope and empty stderr -> empty summary, no diagnostic.
    assert result.validation_output_summary == ""
    finished = [e for e in events if e.get("title") == "OpenCode nonzero exit"]
    assert finished[0]["metadata"]["error_diagnostic"] == ""


# ---------------------------------------------------------------------------
# Unknown / empty payload safe
# ---------------------------------------------------------------------------


def test_empty_error_envelope_is_safe(monkeypatch, tmp_path) -> None:
    stdout = json.dumps({"type": "error", "error": {}}) + "\n"
    result, events, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout=stdout, stderr=""
    )
    assert result.failure_classification == "executor_nonzero"
    assert result.validation_output_summary == ""
    assert result.error == "opencode_nonzero:exit=1:executor_nonzero"


def test_empty_stdout_nonzero_is_safe(monkeypatch, tmp_path) -> None:
    result, events, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout="", stderr=""
    )
    assert result.failure_classification == "executor_nonzero"
    assert result.validation_output_summary == ""


# ---------------------------------------------------------------------------
# Precedence: policy_refusal and existing statuses stay ahead of ECONNRESET
# ---------------------------------------------------------------------------


def test_policy_refusal_precedence_over_econnreset(monkeypatch, tmp_path) -> None:
    payload = {
        "type": "error",
        "error": {
            "code": "content_policy_violation",
            "message": "ECONNRESET forbidden by content filter",
            "data": {"statusCode": 403},
        },
    }
    stdout = json.dumps(payload) + "\n"
    result, events, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout=stdout, stderr=""
    )
    assert result.failure_classification == "policy_refusal"
    # Diagnostic still retained alongside the precedence-preserving class.
    assert "ECONNRESET" in result.validation_output_summary
    assert "content_policy_violation" in result.validation_output_summary


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (429, "api_error_429"),
        (401, "auth_provider_route_failure"),
        (403, "auth_provider_route_failure"),
        (503, "provider_overloaded"),
        (529, "provider_overloaded"),
    ],
)
def test_existing_statuses_precede_econnreset(
    monkeypatch, tmp_path, status: int, expected: str
) -> None:
    payload = {
        "type": "error",
        "error": {
            "name": "APIError",
            "data": {
                "message": "ECONNRESET during a status-%d response" % status,
                "statusCode": status,
            },
        },
    }
    stdout = json.dumps(payload) + "\n"
    result, _events, _store, _tid = _run_core(
        monkeypatch, tmp_path, stdout=stdout, stderr=""
    )
    assert result.failure_classification == expected


def test_quota_exhausted_precedence_over_econnreset(monkeypatch, tmp_path) -> None:
    payload = {
        "type": "error",
        "error": {
            "name": "APIError",
            "data": {
                "message": "ECONNRESET: your quota has been exhausted",
                "statusCode": 429,
            },
        },
    }
    stdout = json.dumps(payload) + "\n"
    result, _e, _s, _t = _run_core(monkeypatch, tmp_path, stdout=stdout, stderr="")
    assert result.failure_classification == "quota_exhausted"


# ---------------------------------------------------------------------------
# Secret confinement: body / headers / prompts never persisted
# ---------------------------------------------------------------------------


def test_secrets_in_body_headers_prompt_never_persisted(
    monkeypatch, tmp_path
) -> None:
    body_sentinel = "private-body-marker"
    header_sentinel = "private-header-marker"
    prompt_sentinel = "private-prompt-marker"
    labelled_secret = "sk-realsecret12345678"
    token_secret = "leakedtokenvalue12345"
    payload = {
        "type": "error",
        "error": {
            "name": "APIError",
            "data": {
                "message": (
                    "reset: %s and token: %s" % (labelled_secret, token_secret)
                ),
                "statusCode": 502,
                "body": body_sentinel + " " + labelled_secret,
                "headers": {"Authorization": "Bearer " + header_sentinel},
                "prompt": prompt_sentinel + " " + labelled_secret,
            },
        },
    }
    stdout = json.dumps(payload) + "\n"
    result, events, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout=stdout, stderr=""
    )

    bundle = json.dumps(
        {
            "summary": result.validation_output_summary,
            "error": result.error,
            "events": events,
            "evidence": _evidence_rows(store, task_id),
        }
    )
    # Non-allowlisted fields never reach any durable surface.
    for sentinel in (body_sentinel, header_sentinel, prompt_sentinel):
        assert sentinel not in bundle, sentinel
    # Labelled secrets inside the allowed message are redacted before truncation.
    assert labelled_secret not in bundle
    assert token_secret not in bundle
    # The message still carries a useful redacted reason.
    assert "reset" in result.validation_output_summary
    assert "status=502" in result.validation_output_summary
    assert "[REDACTED]" in result.validation_output_summary


# ---------------------------------------------------------------------------
# Bounding: oversized message and NUL control bytes
# ---------------------------------------------------------------------------


def test_oversized_message_and_nul_are_bounded(monkeypatch, tmp_path) -> None:
    payload = {
        "type": "error",
        "error": {
            "name": "APIError",
            "data": {
                "message": "E" * 500 + "\x00\x01trailing",
                "statusCode": 502,
            },
        },
    }
    stdout = json.dumps(payload) + "\n"
    result, events, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout=stdout, stderr=""
    )
    diag = result.validation_output_summary
    assert diag
    assert "name=APIError" in diag
    assert "status=502" in diag
    # NUL control bytes stripped (matches existing _bounded_value behavior).
    assert "\x00" not in diag
    # The whole diagnostic surface is bounded by MAX_EVIDENCE_STRING_LEN.
    assert len(diag) <= MAX_EVIDENCE_STRING_LEN
    for row in _evidence_rows(store, task_id):
        assert len(str(row.get("value", ""))) <= MAX_EVIDENCE_STRING_LEN


# ---------------------------------------------------------------------------
# End-to-end via the real execute() path
# ---------------------------------------------------------------------------


def test_execute_path_retains_econnreset_diagnostic(tmp_path) -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    store = TaskStore(":memory:")
    store.create_task(
        title="econnreset e2e", executor_kind="opencode", model_profile_ref="m"
    )
    task_id = store.list_tasks()[0].id
    executor = OpenCodeExecutor(
        model_id="m", opencode_exe="/fake/opencode", timeout=30
    )
    payload = _econnreset_payload()
    stdout = json.dumps(payload) + "\n"
    original_run = exec_mod.subprocess.run
    original_owned = exec_mod._run_owned_cli_process

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(
            args=argv, returncode=0, stdout="", stderr=""
        )

    exec_mod.subprocess.run = fake_run
    exec_mod._run_owned_cli_process = (
        lambda argv, *, cwd, env, timeout: OwnedCliProcessResult(
            returncode=1, stdout=stdout, stderr="", timed_out=False,
            cleanup_confirmed=True,
        )
    )
    events: list[dict] = []
    try:
        result = executor.execute(
            task_id,
            store,
            workspace_root=str(tmp_path),
            event_callback=lambda _tid, ev: events.append(ev),
        )
        assert result.success is False
        assert result.failure_classification == "network_provider_failure"
        assert result.error.startswith("opencode_nonzero:exit=1:network_provider_failure ")
        assert "ECONNRESET" in result.error
        assert "ECONNRESET" in result.validation_output_summary
        finished = [e for e in events if e.get("title") == "OpenCode nonzero exit"]
        assert finished and "ECONNRESET" in finished[0]["metadata"]["error_diagnostic"]
    finally:
        exec_mod.subprocess.run = original_run
        exec_mod._run_owned_cli_process = original_owned


# ---------------------------------------------------------------------------
# Helper-level unit tests for the allowlist (not tautological)
# ---------------------------------------------------------------------------


def test_single_error_diagnostic_allowlist_excludes_body_headers_prompt() -> None:
    payload = {
        "name": "APIError",
        "code": "econnreset",
        "data": {
            "message": "socket closed",
            "statusCode": 502,
            "body": {"message": "should-not-appear"},
            "headers": {"authorization": "should-not-appear"},
            "prompt": "should-not-appear",
            "stack": "should-not-appear",
        },
    }
    diag = _single_error_diagnostic(payload, MAX_EVIDENCE_STRING_LEN)
    assert "name=APIError" in diag
    assert "code=econnreset" in diag
    assert "message=socket closed" in diag
    assert "status=502" in diag
    assert "should-not-appear" not in diag
    assert "body" not in diag
    assert "headers" not in diag
    assert "prompt" not in diag
    assert "stack" not in diag


def test_bounded_error_diagnostic_uses_first_real_error_envelope() -> None:
    events = [
        {"type": "text", "data": "noise ECONNRESET"},
        {"type": "error", "error": {"name": "APIError", "data": {
            "message": "ECONNRESET", "statusCode": 502,
        }}},
        {"type": "error", "error": {"name": "Other", "data": {
            "message": "second", "statusCode": 500,
        }}},
    ]
    diag = _bounded_error_diagnostic(events)
    assert "ECONNRESET" in diag
    assert "status=502" in diag
    assert "second" not in diag


def test_bounded_error_diagnostic_empty_when_no_real_errors() -> None:
    assert _bounded_error_diagnostic([]) == ""
    assert _bounded_error_diagnostic(
        [{"type": "text", "data": "ECONNRESET noise"}]
    ) == ""


@pytest.mark.parametrize(("provider_message", "local_unapproved"), [
    ("Trae CN: ECONNRESET: The socket connection was closed unexpectedly.", False),
    ("ECONNRESET while handling unapproved retry from upstream", False),
    ("ECONNRESET fixture", True),
])
def test_nested_reason_reaches_real_durable_failure_detail(
    monkeypatch, tmp_path, provider_message, local_unapproved
) -> None:
    from dataclasses import replace
    from types import SimpleNamespace
    from reverse_agent.platform_v1.durable_execution import DurableExecutionService
    from reverse_agent.platform_v1.opencode_executor import PreparedWorkspaceContext
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter

    # Give the fenced production context a real, fixture-owned Git identity.
    for args in (("init",), ("config", "user.name", "Fixture"),
                 ("config", "user.email", "fixture@example.invalid")):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "fixture.txt").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "--", "fixture.txt"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=tmp_path, check=True, capture_output=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    # Reuse only the fake CLI seam; execute the real durable dispatch and sink.
    payload = _econnreset_payload()
    payload["error"]["data"]["message"] = provider_message
    result, _, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout=json.dumps(payload) + "\n"
    )
    service = DurableExecutionService(
        store=store, router=ExecutorRouter(),
        execution_authority_sha="fixture-authority", planning_sha="fixture-planning",
    )
    lease = service._acquire_or_find_lease(task_id, "fixture-owner", "", str(tmp_path))
    try:
        store._set_worktree_identity(lease.run_id, str(tmp_path), head, lease.owner, lease.epoch)
        store._set_repository_base_sha(lease.run_id, head, lease.owner, lease.epoch)
        store._accept_checkpoint(lease.run_id, "PRE_PLANNER", "fixture", 1, lease.owner, lease.epoch)
        run = store._get_durable_run(lease.run_id)
        prepared = PreparedWorkspaceContext(
            worktree=tmp_path, base_sha=head, execution_id=run.execution_id,
            cli_path="/fake/opencode", is_cmd=False, opencode_exe="/fake/opencode",
        )
        executor = _executor()
        if local_unapproved:
            # Local policy failure control: only the executor-result seam is
            # injected; the fenced durable classification/persistence is real.
            result = replace(result, error="host_validation_command_unapproved",
                             failure_classification="deterministic_validation_failure")
            executor = SimpleNamespace(execute_role_prepared=lambda *a, **kw: result)
        outcome = service._dispatch_opencode_durable_single(
            task_id=task_id, run=run, lease=lease, executor=executor,
            prepared=prepared, workspace_root=str(tmp_path),
            idempotency_key="fixture-nested-error", request_digest="fixture",
        )
        persisted = store.get_task(task_id)
        assert not outcome.success
        assert persisted.status == "FAILED"
        if local_unapproved:
            assert persisted.failure_classification == "blocked"
            assert persisted.failure_detail == "host_validation_command_unapproved"
        else:
            assert persisted.failure_classification == "network_provider_failure", persisted.failure_detail
            assert persisted.failure_detail.startswith("opencode_nonzero:exit=1:network_provider_failure ")
            assert "ECONNRESET" in persisted.failure_detail
            assert "status=502" in persisted.failure_detail
        assert outcome.failure_detail == persisted.failure_detail
    finally:
        store._release_durable_lease(lease.run_id, lease.owner, lease.epoch)


def test_short_control_bytes_and_split_secret_are_sanitized(monkeypatch, tmp_path) -> None:
    secret = "short-fixture-value"
    payload = {"type": "error", "error": {"name": "APIError", "data": {
        "message": "socket\x01 closed\x1b\n api_\x01key: " + secret + "\x7f",
        "statusCode": 502,
    }}}
    diagnostic = _single_error_diagnostic(payload["error"], MAX_EVIDENCE_STRING_LEN)
    assert all(ord(ch) >= 32 and ord(ch) != 127 for ch in diagnostic)
    assert secret not in diagnostic
    result, events, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout=json.dumps(payload) + "\n"
    )
    finished = next(e for e in events if e.get("title") == "OpenCode nonzero exit")
    surfaces = [result.error, result.validation_output_summary,
                finished["metadata"]["error_diagnostic"], finished["description"]]
    surfaces += [row["value"] for row in _evidence_rows(store, task_id)]
    assert surfaces and all("socket closed" in value for value in surfaces)
    for value in surfaces:
        assert secret not in value
        assert "[REDACTED]" in value
        assert all(ord(ch) >= 32 and ord(ch) != 127 for ch in value)
    assert len(finished["metadata"]["error_diagnostic"]) <= MAX_EVIDENCE_STRING_LEN


def test_resume_path_keeps_typed_class_over_unapproved_provider_text(
    monkeypatch, tmp_path
) -> None:
    """Review regression: the resume path must apply the same guard.

    A provider diagnostic containing 'unapproved' appended after the typed
    opencode_nonzero class must not reclassify the durable task as 'blocked'
    when the run resumes from a PRE_PLANNER crash state.
    """
    from dataclasses import replace
    from types import SimpleNamespace
    from reverse_agent.platform_v1.durable_execution import DurableExecutionService
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter

    for args in (("init",), ("config", "user.name", "Fixture"),
                 ("config", "user.email", "fixture@example.invalid")):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "fixture.txt").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "--", "fixture.txt"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=tmp_path, check=True, capture_output=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    result, _, store, task_id = _run_core(
        monkeypatch, tmp_path, stdout=json.dumps(_econnreset_payload()) + "\n"
    )
    crafted = replace(
        result,
        error="opencode_nonzero:exit=1:provider_overloaded "
              "message=ECONNRESET while handling unapproved retry from upstream",
        failure_classification="provider_overloaded",
    )
    service = DurableExecutionService(
        store=store, router=ExecutorRouter(),
        execution_authority_sha="fixture-authority", planning_sha="fixture-planning",
    )
    monkeypatch.setattr(service.router, "create_executor",
                        lambda **k: SimpleNamespace(execute_role_prepared=lambda *a, **kw: crafted))
    lease = service._acquire_or_find_lease(task_id, "fixture-owner", "", str(tmp_path))
    try:
        store._set_worktree_identity(lease.run_id, str(tmp_path), head, lease.owner, lease.epoch)
        store._set_repository_base_sha(lease.run_id, head, lease.owner, lease.epoch)
        store._accept_checkpoint(lease.run_id, "PRE_PLANNER", "fixture", 1, lease.owner, lease.epoch)
        run = store._get_durable_run(lease.run_id)
        # Fake only the CLI seam: reconstruction would resolve a real OpenCode
        # CLI, which CI hosts do not install. Everything after reconstruction
        # (dispatch, classification, fencing, terminalize) stays real.
        from reverse_agent.platform_v1.opencode_executor import (
            OpenCodeExecutor, PreparedWorkspaceContext,
        )
        monkeypatch.setattr(
            OpenCodeExecutor, "reconstruct_prepared_context", classmethod(
                lambda cls, **kw: PreparedWorkspaceContext(
                    worktree=tmp_path, base_sha=head, execution_id=run.execution_id,
                    cli_path="/fake/opencode", is_cmd=False, opencode_exe="/fake/opencode",
                )))
        outcome = service._resume_single_pre_planner(
            task_id=task_id, workspace_root=str(tmp_path.parent), run=run, lease=lease,
            task=store.get_task(task_id), executor_kind="opencode", role_attempt=1,
            prepared_path=None, review_status="",
        )
        persisted = store.get_task(task_id)
        assert not outcome.success
        assert persisted.failure_classification == "provider_overloaded", persisted.failure_detail
        assert persisted.failure_detail.startswith("opencode_nonzero:exit=1:provider_overloaded ")
        assert "unapproved" in persisted.failure_detail
    finally:
        store._release_durable_lease(lease.run_id, lease.owner, lease.epoch)
