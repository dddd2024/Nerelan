"""Agents write their progress notes and summary in the Owner's language."""
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.claude_executor import ClaudeCodeExecutor
from reverse_agent.platform_v1.codex_executor import CodexExecutor
from reverse_agent.platform_v1.opencode_executor import build_prompt, build_role_prompt, output_language_rule
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.opencode_executor import RoleContext

CHINESE = "Simplified Chinese"


def test_default_asks_for_simplified_chinese_prose_and_english_code(monkeypatch):
    monkeypatch.delenv("REVERSE_AGENT_AGENT_LANGUAGE", raising=False)
    rule = output_language_rule()
    assert CHINESE in rule and "简体中文" in rule
    assert "Keep code, identifiers, file paths, commands, commit messages, code comments and handoff files in English" in rule


@pytest.mark.parametrize("value", ["en", "EN", "english", "off", ""])
def test_english_leaves_the_prompt_unchanged(monkeypatch, value):
    monkeypatch.setenv("REVERSE_AGENT_AGENT_LANGUAGE", value)
    assert output_language_rule() == ""
    assert "OUTPUT LANGUAGE" not in build_prompt("task", "/ws")


def test_rule_sits_outside_the_authority_block_and_before_the_task(monkeypatch):
    monkeypatch.delenv("REVERSE_AGENT_AGENT_LANGUAGE", raising=False)
    for prompt in (build_prompt("fix it", "/ws"),
                   build_role_prompt("fix it", "/ws", RoleContext("coder", "t", "/ws")),
                   build_role_prompt("fix it", "/ws", RoleContext("reviewer", "t", "/ws"))):
        footer, rule, task = (prompt.index("END AUTHORITY CONSTRAINTS"), prompt.index("OUTPUT LANGUAGE"),
                              prompt.index("USER TASK\nfix it"))
        assert footer < rule < task
        assert prompt.count("OUTPUT LANGUAGE") == 1


@pytest.mark.parametrize("executor_class, kind", [(CodexExecutor, "codex"), (ClaudeCodeExecutor, "claude_code")])
@pytest.mark.parametrize("language, expected", [(None, True), ("en", False)])
def test_native_executors_carry_the_same_rule(tmp_path, monkeypatch, executor_class, kind, language, expected):
    if language is None:
        monkeypatch.delenv("REVERSE_AGENT_AGENT_LANGUAGE", raising=False)
    else:
        monkeypatch.setenv("REVERSE_AGENT_AGENT_LANGUAGE", language)
    executor = object.__new__(executor_class)
    executor._model_id = "offline"
    executor._binding_resolution = None
    store = TaskStore(str(tmp_path / "tasks.db"))
    task = store.create_task(title="add one line to README")
    workspace = tmp_path / task.id
    workspace.mkdir()
    prepared = SimpleNamespace(executor_kind=kind, worktree=workspace, base_sha="a" * 40, execution_id=f"exec-{task.id}")
    seen = {}

    def stream(prepared_arg, prompt, *args, **kwargs):
        seen["prompt"] = prompt
        return 1

    turn = SimpleNamespace(failed=True, failure_classification=f"{kind}_turn_failed", failure_detail="offline",
                           failure_reset_at="", usage=None, final_text="", changed=False)
    monkeypatch.setattr(executor, "_verify_workspace", lambda *a: None)
    monkeypatch.setattr(executor, "_parser", lambda *a: SimpleNamespace(turn=turn, finish=lambda: turn))
    monkeypatch.setattr(executor, "_stream", stream)
    try:
        executor.execute_role_prepared(prepared, store, role_context=RoleContext("executor", task.id, workspace))
    except Exception:
        pass  # the offline turn fails; only the prompt it was given matters here
    prompt = seen["prompt"]
    assert ("OUTPUT LANGUAGE" in prompt) is expected
    assert prompt.index("add one line to README") > (prompt.index("OUTPUT LANGUAGE") if expected else 0)
