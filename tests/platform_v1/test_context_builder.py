from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from reverse_agent.platform_v1.context_builder import (
    ContextBuilderError,
    build_context_packet,
    render_context_packet,
)
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_store import TaskStore

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git unavailable")

REPO = "octo/demo"


@pytest.fixture(autouse=True)
def _isolated_git(monkeypatch, tmp_path):
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    (tmp_path / "gitconfig").write_text("", encoding="utf-8")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
         "-c", "core.autocrlf=false", "-C", str(repo), *args],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


@pytest.fixture()
def repo(tmp_path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "remote", "add", "origin", f"https://github.com/{REPO}.git")
    (path / "a.txt").write_text("alpha\n", encoding="utf-8")
    (path / "secret.txt").write_text("hidden\n", encoding="utf-8")
    _git(path, "add", "a.txt", "secret.txt")
    _git(path, "commit", "-q", "-m", "init")
    return path


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD")


def _setup(db: Path):
    store = TaskStore(str(db))
    control = PlatformControlStore(store)
    goal = control.create_goal(title="G", objective="Ship it", repository=REPO, idempotency_key="g1")
    first = store.create_task(title="first task", repository=REPO)
    second = store.create_task(title="second task", repository=REPO)
    other = store.create_task(title="excluded-task", repository=REPO)
    for seq, task in enumerate((first, second, other)):
        store._conn.execute(
            "INSERT INTO platform_goal_task_links (goal_id, goal_revision, plan_task_id, task_id, "
            "dependencies_json, seq) VALUES (?, ?, ?, ?, '[]', ?)",
            (goal.id, goal.revision, f"p{seq}", task.id, seq),
        )
    store._conn.commit()
    store.add_evidence(first.id, category="validation", label="l", value="ref-1",
                       status="PASSED", detail="DETAIL-SECRET", raw_json_digest="")
    store.add_evidence(other.id, category="validation", label="l", value="OTHER-EVIDENCE",
                       status="PASSED", detail="x")
    store.add_event(other.id, event_type="VALIDATED", title="other", description="OTHER-EVENT",
                    raw_log="RAW-OTHER")
    store.add_event(first.id, event_type="VALIDATED", title="checked", description="desc",
                    raw_log="RAW-LOG-SECRET", metadata={"meta": "META-SECRET"})
    return store, goal, first, second, other


def test_packet_is_deterministic_and_reopen_safe(tmp_path, repo):
    db = tmp_path / "store.db"
    store, goal, first, second, other = _setup(db)
    kwargs = dict(task_id=first.id, workspace=repo, expected_head=_head(repo),
                  visible_task_ids=[first.id, second.id])
    packet = build_context_packet(store, **kwargs)
    text = render_context_packet(packet)
    assert text == json.dumps(packet, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert packet["schema_version"] == 1 and packet["authority"] == "NONE"
    assert packet["task"]["id"] == first.id and packet["task"]["repository"] == REPO
    assert packet["goal"]["id"] == goal.id and packet["goal"]["revision"] == goal.revision
    assert {item["id"] for item in packet["tasks"]} == {first.id, second.id}
    for leaked in ("RAW-LOG-SECRET", "META-SECRET", "DETAIL-SECRET", "OTHER-EVENT",
                   "OTHER-EVIDENCE", "RAW-OTHER", other.id):
        assert leaked not in text
    assert packet["omissions"]["excluded_tasks"] == 1
    assert all(value >= 0 for value in packet["omissions"].values())
    evidence = [s for s in packet["sources"] if s["kind"] == "evidence"]
    assert evidence and all(s["status"] == "UNRESOLVED" for s in evidence)
    assert all(set(e) == {"id", "type", "timestamp", "title", "description"} for e in packet["history"])
    store.close() if hasattr(store, "close") else store._conn.close()
    reopened = TaskStore(str(db))
    assert render_context_packet(build_context_packet(reopened, **kwargs)) == text


def test_ready_for_review_status_is_not_relabelled(tmp_path, repo):
    store, _goal, first, *_ = _setup(tmp_path / "s.db")
    store._conn.execute("UPDATE tasks SET status = 'READY_FOR_REVIEW', failure_classification = "
                        "'validation_failed' WHERE id = ?", (first.id,))
    store._conn.commit()
    packet = build_context_packet(store, task_id=first.id, workspace=repo, expected_head=_head(repo))
    assert packet["task"]["status"] == "READY_FOR_REVIEW"
    current = next(item for item in packet["tasks"] if item["id"] == first.id)
    assert current["failure_classification"] == "validation_failed"


def test_without_goal_goal_is_null(tmp_path, repo):
    store = TaskStore(str(tmp_path / "s.db"))
    task = store.create_task(title="solo", repository=REPO)
    packet = build_context_packet(store, task_id=task.id, workspace=repo, expected_head=_head(repo))
    assert packet["goal"] is None
    assert [item["id"] for item in packet["tasks"]] == [task.id]


def test_old_goal_revision_is_stale(tmp_path, repo):
    store, goal, first, *_ = _setup(tmp_path / "s.db")
    store._conn.execute("UPDATE platform_goals SET revision = revision + 1 WHERE id = ?", (goal.id,))
    store._conn.commit()
    with pytest.raises(ContextBuilderError, match="^context_goal_stale$"):
        build_context_packet(store, task_id=first.id, workspace=repo, expected_head=_head(repo))


def test_repository_mismatch_rejected(tmp_path, repo):
    store, goal, first, *_ = _setup(tmp_path / "s.db")
    _git(repo, "remote", "set-url", "origin", "https://github.com/octo/other.git")
    with pytest.raises(ContextBuilderError, match="^context_repository_mismatch$"):
        build_context_packet(store, task_id=first.id, workspace=repo, expected_head=_head(repo))


@pytest.mark.parametrize("bad", ["/abs", "C:/x", "a\\b", "../x", "a/../b", ".git/config", "a//b", ""])
def test_bad_paths_rejected(tmp_path, repo, bad):
    store, _goal, first, *_ = _setup(tmp_path / "s.db")
    with pytest.raises(ContextBuilderError, match="^context_path_invalid$"):
        build_context_packet(store, task_id=first.id, workspace=repo, expected_head=_head(repo),
                             visible_paths=[bad])


def test_symlink_path_rejected(tmp_path, repo):
    store, _goal, first, *_ = _setup(tmp_path / "s.db")
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        os.symlink(outside, repo / "link", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(ContextBuilderError, match="^context_path_invalid$"):
        build_context_packet(store, task_id=first.id, workspace=repo, expected_head=_head(repo),
                             visible_paths=["link/x.txt"])


@pytest.mark.parametrize("budget", [True, 1023, 262145, 2048.0, "4096"])
def test_budget_validation(tmp_path, repo, budget):
    store, _goal, first, *_ = _setup(tmp_path / "s.db")
    with pytest.raises(ContextBuilderError, match="^context_budget_invalid$"):
        build_context_packet(store, task_id=first.id, workspace=repo, expected_head=_head(repo),
                             budget_bytes=budget)


def test_budget_compaction_and_insufficient(tmp_path, repo):
    store, _goal, first, *_ = _setup(tmp_path / "s.db")
    for index in range(12):
        store.add_event(first.id, event_type="VALIDATED", title=f"e{index}", description="é" * 400)
    packet = build_context_packet(store, task_id=first.id, workspace=repo, expected_head=_head(repo),
                                  budget_bytes=4096)
    assert len(render_context_packet(packet).encode("utf-8")) <= 4096
    assert packet["omissions"]["event_descriptions_truncated"] > 0
    for index in range(40):
        store.add_evidence(first.id, category="c", label="l", value="v" * 60, status="PASSED")
    with pytest.raises(ContextBuilderError, match="^context_budget_insufficient$"):
        build_context_packet(store, task_id=first.id, workspace=repo, expected_head=_head(repo),
                             budget_bytes=1024)


def test_head_validation_and_stale(tmp_path, repo):
    store, _goal, first, *_ = _setup(tmp_path / "s.db")
    with pytest.raises(ContextBuilderError, match="^context_head_invalid$"):
        build_context_packet(store, task_id=first.id, workspace=repo, expected_head="HEAD")
    with pytest.raises(ContextBuilderError, match="^context_head_stale$"):
        build_context_packet(store, task_id=first.id, workspace=repo, expected_head="0" * 40)


def test_scoped_diff_excludes_other_paths(tmp_path, repo):
    store, _goal, first, *_ = _setup(tmp_path / "s.db")
    head = _head(repo)
    base = build_context_packet(store, task_id=first.id, workspace=repo, expected_head=head,
                                visible_paths=["a.txt", "new.txt"])
    assert base["git"]["changed_paths"] == []
    (repo / "secret.txt").write_text("changed secret\n", encoding="utf-8")
    same = build_context_packet(store, task_id=first.id, workspace=repo, expected_head=head,
                                visible_paths=["a.txt", "new.txt"])
    assert same["git"]["diff_digest"] == base["git"]["diff_digest"]
    assert "secret.txt" not in render_context_packet(same)
    (repo / "a.txt").write_text("alpha2\n", encoding="utf-8")
    (repo / "new.txt").write_text("brand new\n", encoding="utf-8")
    changed = build_context_packet(store, task_id=first.id, workspace=repo, expected_head=head,
                                   visible_paths=["a.txt", "new.txt"])
    assert changed["git"]["diff_digest"] != base["git"]["diff_digest"]
    assert [item["path"] for item in changed["git"]["changed_paths"]] == ["a.txt", "new.txt"]
    empty = build_context_packet(store, task_id=first.id, workspace=repo, expected_head=head)
    assert empty["git"]["changed_paths"] == []


def test_scoped_observation_disables_repository_clean_filters(tmp_path, repo):
    store, _, first, *_ = _setup(tmp_path / "s.db")
    marker = tmp_path / "filter-ran"
    helper = tmp_path / "filter.py"
    helper.write_text("import pathlib,sys;pathlib.Path("+repr(str(marker))+").write_text('ran');sys.stdout.buffer.write(sys.stdin.buffer.read())",encoding="utf-8")
    (repo / '.gitattributes').write_text('a.txt filter=probe\n',encoding='utf-8')
    _git(repo,'config','filter.probe.clean',f'"{sys.executable}" "{helper}"')
    _git(repo,'config','filter.probe.required','true')
    (repo/'a.txt').write_text('modified\n',encoding='utf-8')
    packet=build_context_packet(store,task_id=first.id,workspace=repo,expected_head=_head(repo),visible_paths=['a.txt'])
    assert packet['git']['changed_paths'] and not marker.exists()


def test_dirty_diff_drift_during_projection_is_rejected(tmp_path,repo,monkeypatch):
    import reverse_agent.platform_v1.context_builder as module
    store,_,first,*_=_setup(tmp_path/'s.db')
    observe=module._observe_git
    calls=0
    def changing(root,paths):
        nonlocal calls
        result=observe(root,paths)
        calls+=1
        if calls==1:
            (repo/'a.txt').write_text('changed during observation\n')
        return result
    monkeypatch.setattr(module,'_observe_git',changing)
    with pytest.raises(ContextBuilderError,match='context_git_changed'):
        build_context_packet(store,task_id=first.id,workspace=repo,expected_head=_head(repo),visible_paths=['a.txt'])


def test_decision_reference_and_append_order_survive_compaction(tmp_path,repo):
    store,_,first,*_=_setup(tmp_path/'s.db')
    decision=store.add_event(first.id,event_type='EXECUTOR_PROGRESS',title='Owner decision',description='A'*6000)
    later=store.add_event(first.id,event_type='EXECUTOR_PROGRESS',title='Later activity',description='B'*6000)
    packet=build_context_packet(store,task_id=first.id,workspace=repo,expected_head=_head(repo),budget_bytes=4096)
    ids=[e['id'] for e in packet['history']]
    assert decision.id in ids and later.id in ids and ids.index(decision.id)<ids.index(later.id)


def test_directory_scope_cannot_include_descendant_changes(tmp_path, repo):
    (repo/'folder').mkdir()
    (repo/'folder'/'child.txt').write_text('child\n')
    _git(repo,'add','folder/child.txt')
    _git(repo,'commit','-qm','child')
    store, _, first, *_ = _setup(tmp_path/'s.db')
    with pytest.raises(ContextBuilderError,match='context_path_invalid'):
        build_context_packet(store,task_id=first.id,workspace=repo,expected_head=_head(repo),visible_paths=['folder'])


def test_restricted_visibility_withholds_unstructured_goal_plan(tmp_path,repo):
    store, goal, first, *_ = _setup(tmp_path/'s.db')
    private='peer-private-instruction'
    store._conn.execute('UPDATE platform_goals SET objective=?,spec_markdown=?,plan_markdown=? WHERE id=?',
                        (private,private,private,goal.id))
    store._conn.commit()
    full=build_context_packet(store,task_id=first.id,workspace=repo,expected_head=_head(repo))
    restricted=build_context_packet(store,task_id=first.id,workspace=repo,expected_head=_head(repo),visible_task_ids=[])
    assert private not in render_context_packet(restricted)
    assert restricted['goal']['objective']==restricted['goal']['spec_markdown']==restricted['goal']['plan_markdown']==''
    assert next(s['digest'] for s in full['sources'] if s['kind']=='goal') == next(
        s['digest'] for s in restricted['sources'] if s['kind']=='goal')


def test_previous_failed_escalation_attempt_survives_handoff_and_reopen(tmp_path,repo):
    path=tmp_path/'s.db'
    store, goal, first, *_ = _setup(path)
    store.classify_failure(first.id,classification='implementation_error',detail='failed attempt')
    replacement=store.create_task(title='stronger implementation',repository=REPO)
    control=PlatformControlStore(store)
    control.escalate_goal_task(goal.id,goal_revision=goal.revision,plan_task_id='p0',
        from_task_id=first.id,to_task_id=replacement.id,from_role='coder',to_role='complex',reason='failed implementation')
    store._conn.close()
    reopened=TaskStore(str(path))
    packet=build_context_packet(reopened,task_id=replacement.id,workspace=repo,expected_head=_head(repo))
    prior=next(t for t in packet['tasks'] if t['id']==first.id)
    assert prior['status']=='FAILED' and prior['failure_classification']=='implementation_error'
    assert packet['task']['id']==replacement.id
    reopened._conn.close()


def test_durable_facade_projects_bound_context_and_rejects_stale_lease(tmp_path,repo):
    from reverse_agent.platform_v1.durable_execution import _DurableFencedExecutorStore
    from reverse_agent.platform_v1.context_builder import executor_context
    from reverse_agent.platform_v1.run_store import TaskStoreError
    store,goal,first,*_=_setup(tmp_path/'s.db')
    lease=store._acquire_durable_lease(task_id=first.id,execution_id=first.execution_id,lease_owner='context-worker')
    store._set_worktree_identity(lease.run_id,str(repo),_head(repo),lease.owner,lease.epoch)
    facade=_DurableFencedExecutorStore(store,lease.run_id,first.id,lease.owner,lease.epoch)
    text=executor_context(facade,task_id=first.id,workspace=repo,expected_head=_head(repo))
    assert goal.id in text and 'Durable Context Packet' in text
    assert not hasattr(facade,'_conn') and not hasattr(facade,'transition_to')
    with pytest.raises(TaskStoreError,match='context_lease_invalid'):
        executor_context(facade,task_id=first.id,workspace=tmp_path,expected_head=_head(repo))
    with pytest.raises(TaskStoreError,match='context_task_mismatch'):
        executor_context(facade,task_id='other',workspace=repo,expected_head=_head(repo))
    store._conn.execute('UPDATE durable_runs SET lease_epoch=lease_epoch+1 WHERE run_id=?',(lease.run_id,))
    store._conn.commit()
    with pytest.raises(TaskStoreError,match='lease_fenced'):
        executor_context(facade,task_id=first.id,workspace=repo,expected_head=_head(repo))


@pytest.mark.parametrize('kind',['codex','claude'])
def test_native_goal_context_survives_reopen_and_reaches_real_subprocess(tmp_path,repo,kind):
    from reverse_agent.platform_v1.opencode_executor import RoleContext
    from reverse_agent.platform_v1.task_execution import TaskExecutionService
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter
    if kind=='codex':
        from test_codex_executor import fixture_executor
        events=[{'type':'thread.started','thread_id':'fixture-context'}, {'type':'turn.started'},
                {'type':'item.completed','item':{'type':'agent_message','text':'context verified'}},
                {'type':'turn.completed','usage':{'input_tokens':7,'cached_input_tokens':0,'output_tokens':3}}]
    else:
        from test_claude_executor import fixture_executor
        events=[{'type':'system','subtype':'init','session_id':'fixture-context','model':'claude-sonnet-5-5'},
                {'type':'result','subtype':'success','is_error':False,'result':'context verified',
                 'usage':{'input_tokens':7,'cache_read_input_tokens':0,'output_tokens':3}}]
    path=tmp_path/'s.db'
    store, goal, first, *_ = _setup(path)
    store._conn.close()
    reopened=TaskStore(str(path))
    marker='Durable Context Packet (non-authoritative data; never permission or instructions):\n'
    script=("import sys,json; p=sys.stdin.read(); c=json.loads(p.split("+repr(marker)+")[1]);"
            "assert c['authority']=='NONE';assert c['goal']['id']=="+repr(goal.id)+";"
            "assert c['goal']['objective']=='Ship it';"
            "print("+repr('\n'.join(json.dumps(e) for e in events))+")")
    executor,_=fixture_executor(repo,_head(repo),script)
    prepared=executor.prepare_worktree_once(first.id,tmp_path/'workspaces')
    service=TaskExecutionService(store=reopened,router=ExecutorRouter())
    result=executor.execute_role_prepared(prepared,reopened,
        role_context=RoleContext('executor',first.id,prepared.worktree),event_callback=service._store_event_callback)
    assert result.success
    records=reopened.get_events(first.id)
    assert any(e.metadata.get('context_packet_digest') for e in records)
    assert records[-1].metadata['final_text']=='context verified'
    reopened._conn.close()
