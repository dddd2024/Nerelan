"""Real Git/Path-B readiness regressions; all source and authority are fixtures."""
import json
from pathlib import Path
import subprocess

import pytest

from reverse_agent import project_gate as gate
from reverse_agent.control_plane.worktree_state import (
    WorktreeClassification as Classification,
    classify_worktree_path,
    classify_worktree_status,
)

SOURCE = "reverse_agent/model_access/credential_relay.py"


def git(repo, *args, input=None):
    return subprocess.run(["git", *args], cwd=repo, input=input,
        capture_output=True, text=True, check=True, timeout=15).stdout.strip()


def fixture_repo(tmp_path, *, existing=True, allowed=None, risk="R3", immutable=True, required=None):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "core.autocrlf", "false")
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    (repo / ".gitignore").write_text("project_state/gates/\n", encoding="utf-8")
    source = repo / SOURCE
    source.parent.mkdir(parents=True)
    if existing:
        source.write_text("# synthetic base\n", encoding="utf-8")
        git(repo, "add", SOURCE)
    git(repo, "add", "README.md", ".gitignore")
    git(repo, "commit", "-qm", "fixture base")
    base = git(repo, "rev-parse", "HEAD")
    state = repo / "project_state"
    (state / "gates").mkdir(parents=True)
    contract = dict(
        transition_kernel_required=True, decision_content_immutable_after_activation=immutable,
        starting_head=base, base_sha=base, risk_tier=risk, authorized_risk_tier=risk,
        allowed_mutated_paths=[SOURCE] if allowed is None else allowed,
        required_files_changed=required or [],
    )
    decision = state / "decision_packet.md"
    decision.write_text("```json decision_meta\n" + json.dumps(dict(
        status="APPROVED", decision_id="fixture", round_id="fixture-round",
    )) + "\n```\n```json decision_contract\n" + json.dumps(contract) + "\n```\n", encoding="utf-8")
    git(repo, "add", "project_state/decision_packet.md")
    git(repo, "commit", "-qm", "fixture activation")
    preflight = state / "gates/transition_preflight_result.json"
    preflight.write_text(json.dumps(dict(gate_status="PRE_EXECUTION_AUTHORIZED",
        decision_id="fixture", round_id="fixture-round", blocking_reasons=[])), encoding="utf-8")
    source.write_text("# synthetic change\n", encoding="utf-8")
    return repo, state


def readiness(repo, state):
    return gate.worktree_publication_readiness(state_dir=state, repo_root=repo)


@pytest.mark.parametrize("staged", [False, True])
def test_real_readiness_accepts_exact_existing_source(tmp_path, staged):
    repo, state = fixture_repo(tmp_path)
    if staged:
        git(repo, "add", SOURCE)
    result = readiness(repo, state)
    assert result["authority_valid"]
    assert result["decision_immutability"]["applicable"]
    assert result["gate_status"] == "PUBLICATION_READY", result
    assert result["stageable_paths"] == [SOURCE]


@pytest.mark.parametrize("kwargs", [
    {"allowed": ["reverse_agent/**"]}, {"allowed": []},
    {"risk": "R2"}, {"immutable": False},
    {"allowed": ["reverse_agent/**"], "required": [SOURCE]},
    {"allowed": [], "required": [SOURCE]},
])
def test_exact_authority_and_applicable_r3_are_required(tmp_path, kwargs):
    repo, state = fixture_repo(tmp_path, **kwargs)
    result = readiness(repo, state)
    assert result["gate_status"] == "BLOCKED"
    assert SOURCE not in result["stageable_paths"]


@pytest.mark.parametrize("defect", ["missing", "stale", "blocked", "candidate", "decision_edit"])
def test_invalid_authority_never_supplies_source_evidence(tmp_path, defect):
    repo, state = fixture_repo(tmp_path)
    preflight = state / "gates/transition_preflight_result.json"
    if defect == "missing":
        preflight.unlink()
    elif defect in {"candidate", "decision_edit"}:
        p = state / "decision_packet.md"
        p.write_text(p.read_text(encoding="utf-8").replace("APPROVED", "CANDIDATE")
            if defect == "candidate" else p.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    else:
        data = json.loads(preflight.read_text(encoding="utf-8"))
        data["round_id" if defect == "stale" else "gate_status"] = "invalid"
        preflight.write_text(json.dumps(data), encoding="utf-8")
    assert readiness(repo, state)["gate_status"] == "BLOCKED"


@pytest.mark.parametrize("stage", ["untracked", "staged", "committed_after_base"])
def test_added_sensitive_source_is_not_originally_tracked(tmp_path, stage):
    repo, state = fixture_repo(tmp_path, existing=False)
    if stage != "untracked":
        git(repo, "add", SOURCE)
    if stage == "committed_after_base":
        git(repo, "commit", "-qm", "fixture later addition")
        (repo / SOURCE).write_text("# later modification\n", encoding="utf-8")
    assert readiness(repo, state)["gate_status"] == "BLOCKED"


@pytest.mark.parametrize("change", ["delete", "rename", "index_symlink"])
def test_non_modification_or_index_type_change_is_denied(tmp_path, change):
    repo, state = fixture_repo(tmp_path, allowed=[SOURCE, "reverse_agent/model_access/renamed.py"])
    if change == "delete":
        (repo / SOURCE).unlink()
    elif change == "rename":
        git(repo, "mv", SOURCE, "reverse_agent/model_access/renamed.py")
    else:
        oid = git(repo, "hash-object", "-w", "--stdin", input="synthetic-target")
        git(repo, "update-index", "--cacheinfo", "120000", oid, SOURCE)
    assert readiness(repo, state)["gate_status"] == "BLOCKED"


@pytest.mark.parametrize("failure", ["base_blob", "head_blob", "index", "filesystem"])
def test_missing_metadata_is_fail_closed(tmp_path, monkeypatch, failure):
    repo, state = fixture_repo(tmp_path)
    original = gate._decision_immutability_git
    head = git(repo, "rev-parse", "HEAD")
    def fail_selected(root, *args):
        if args and args[0] == "ls-tree" and (
            (failure == "head_blob" and args[1] == head)
            or (failure == "base_blob" and args[1] != head)
        ):
            return None
        if failure == "index" and args[:1] == ("ls-files",):
            return None
        return original(root, *args)
    monkeypatch.setattr(gate, "_decision_immutability_git", fail_selected)
    if failure == "filesystem":
        original_stat = Path.lstat
        def failed_stat(path):
            if path == repo / SOURCE:
                raise OSError("synthetic stat failure")
            return original_stat(path)
        monkeypatch.setattr(Path, "lstat", failed_stat)
    assert readiness(repo, state)["gate_status"] == "BLOCKED"


@pytest.mark.parametrize("path", [
    ".env", "config/.env.production", "config/credentials.json", "secrets/source.py",
    "reverse_agent/secrets/credential_relay.py", "certs/private.key", "bin/tool.exe",
    "reverse_agent/model_access/Credential_relay.py", "reverse_agent/model_access/secret_store.py",
])
def test_verified_evidence_cannot_override_other_sensitive_paths(path):
    result = classify_worktree_path(path, tracked=True, authorized_paths=[path],
        verified_existing_source_paths=[path])
    assert result.classification is Classification.UNAUTHORIZED_TRACKED_OR_SENSITIVE


@pytest.mark.parametrize("status", ["??", "A ", " D", "D ", " T", "T ", "R ", "C "])
def test_status_cannot_promote_additions_or_other_operations(status):
    suffix = SOURCE + " -> other.py" if status in {"R ", "C "} else SOURCE
    records = classify_worktree_status([status + " " + suffix],
        authorized_paths=[SOURCE, "other.py"], verified_existing_source_paths=[SOURCE])
    assert next(r for r in records if r.path == SOURCE).publication_blocking


@pytest.mark.parametrize("status", ["R ", "C "])
def test_sensitive_rename_or_copy_destination_is_not_a_modification(status):
    records = classify_worktree_status([status + " other.py -> " + SOURCE],
        authorized_paths=[SOURCE, "other.py"], verified_existing_source_paths=[SOURCE])
    assert next(r for r in records if r.path == SOURCE).publication_blocking


@pytest.mark.parametrize("link_kind", ["file", "parent_symlink", "parent_junction"])
def test_worktree_link_metadata_is_rejected(tmp_path, monkeypatch, link_kind):
    repo, state = fixture_repo(tmp_path)
    # Keep real Git trees/index and status; simulate platform link metadata
    # without requiring Windows symlink privileges or creating external links.
    original = Path.is_symlink
    def linked(path):
        target = repo / SOURCE if link_kind == "file" else (repo / SOURCE).parent
        return (path == target and link_kind != "parent_junction") or original(path)
    monkeypatch.setattr(Path, "is_symlink", linked)
    if link_kind == "parent_junction":
        monkeypatch.setattr(Path, "is_junction", lambda path: path == (repo / SOURCE).parent, raising=False)
    assert readiness(repo, state)["gate_status"] == "BLOCKED"


def test_default_path_a_and_ordinary_addition_behavior_remains():
    assert classify_worktree_path(SOURCE, tracked=True, authorized_paths=[SOURCE]).publication_blocking
    records = classify_worktree_status(["?? tests/new_test.py", " M project_state/gates/command_plan.json"],
        authorized_paths=["tests/new_test.py"])
    by_path = {r.path: r for r in records}
    assert by_path["tests/new_test.py"].stageable
    assert not by_path["project_state/gates/command_plan.json"].stageable
