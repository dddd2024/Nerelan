"""Native progress and usage must survive the real TaskStore callback."""
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_execution import TaskExecutionService
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.codex_executor import build_codex_argv
from pathlib import Path
import os
from reverse_agent.platform_v1.codex_protocol import CodexJsonl
import json


def test_native_completion_and_progress_are_durable_after_reopen(tmp_path):
    path = str(tmp_path / 'events.sqlite3')
    store = TaskStore(path)
    task = store.create_task(title='Observed native task',executor_kind='codex',binding_ref='native')
    service = TaskExecutionService(store=store,router=ExecutorRouter())
    service._store_event_callback(task.id, {'type':'EXECUTOR_PROGRESS','title':'Codex',
        'description':'Observed command','metadata':{'executor_kind':'codex','event':{'item_type':'command_execution','exit_code':0}}})
    service._store_event_callback(task.id, {'type':'EXECUTOR_COMPLETED','title':'Codex response',
        'description':'Observed final answer','metadata':{'executor_kind':'codex','final_text':'Observed final answer',
            'token_usage':{'input_tokens':12,'output_tokens':4,'cached_input_tokens':2},'cost_status':'unknown'}})
    store._conn.close()
    reopened = TaskStore(path)
    try:
        events = reopened.get_events(task.id)
        assert [e.type for e in events][-2:] == ['EXECUTOR_PROGRESS','EXECUTOR_COMPLETED']
        assert events[-1].metadata['token_usage']['input_tokens'] == 12
        assert events[-1].metadata['cost_status'] == 'unknown'
        assert events[-1].metadata['final_text'] == 'Observed final answer'
    finally:
        reopened._conn.close()


def test_native_config_isolation_keeps_windows_sandbox_selected():
    args = build_codex_argv('codex',Path('.'),'gpt-6.1-sol','workspace-write')
    assert '--ignore-user-config' in args
    assert 'approval_policy="never"' in args
    assert ('windows.sandbox="elevated"' in args) == (os.name == 'nt')
    assert '--dangerously-bypass-approvals-and-sandbox' not in args


def test_native_diagnostic_followed_by_actual_terminal_retains_usage():
    events = [{'type':'thread.started','thread_id':'thread'}, {'type':'turn.started'},
              {'type':'error','message':'Authorization: Bearer private-token'},
              {'type':'item.completed','item':{'type':'agent_message','text':'Recovered'}},
              {'type':'turn.completed','usage':{'input_tokens':10,'cached_input_tokens':3,'output_tokens':2}}]
    parser = CodexJsonl()
    parser.feed(('\n'.join(json.dumps(x) for x in events)+'\n').encode())
    result = parser.finish()
    assert result.completed and not result.failed and result.usage['input_tokens']==10
    assert 'private-token' not in repr(result)


def test_native_diagnostic_without_terminal_never_passes():
    parser = CodexJsonl()
    parser.feed(b'{"type":"error","message":"private-token"}\n')
    result = parser.finish()
    assert result.failed and not result.completed
    assert result.failure_classification == 'codex_turn_failed'
    assert 'private-token' not in repr(result)
