"""Failed trees are recovery evidence, never accepted artifact inputs."""
from pathlib import Path
import re
import json
from datetime import datetime
import subprocess

from .artifact_handoff import _load_evidence
from .functional_validation import digest, git_output, load_contract, functional_feedback
from .run_store import TaskStoreError
from reverse_agent.executor_neutral.core import _snapshot_workspace

FAILED = "FailedAttemptTree"
FIXUP = "ContractFixup"
KINDS = {"target_mismatch", "patch_hygiene"}
OVERLOAD_KIND = "provider_overloaded"
OVERLOAD_FEEDBACK = ("The provider was at capacity and your previous turn was cut off. Your workspace "
                     "already contains that attempt's changes: continue from them, do not start over.")


def attempt_worktree(store, task):
    """The failed execution's own worktree (event or durable run), or None."""
    paths = set()
    for event in store.get_events(task.id):
        metadata = event.metadata if isinstance(event.metadata, dict) else {}
        if (event.type == "WORKSPACE_READY" and metadata.get("execution_id") == task.execution_id
                and isinstance(metadata.get("workspace"), str)):
            paths.add(metadata["workspace"])
    rows = store._conn.execute("SELECT worktree_path FROM durable_runs WHERE task_id=? AND execution_id=?",
                               (task.id, task.execution_id)).fetchall()
    paths.update(row["worktree_path"] for row in rows if row["worktree_path"])
    if len(paths) != 1:
        return None
    path = Path(next(iter(paths)))
    return path.resolve() if path.is_dir() else None


def retain_interrupted_tree(store, task_id, *, worktree):
    """Keep an overload-interrupted attempt's tree as unaccepted recovery evidence."""
    task = store.get_task(task_id)
    contract = load_contract(task)
    if contract is None or task.status != "FAILED":
        raise TaskStoreError("interrupted_snapshot_unavailable")
    root = Path(worktree).resolve(strict=True)
    from .repository_workspace import resolve_repository_workspace
    source = resolve_repository_workspace(task.repository).repo_dir
    if (git_output(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
            != git_output(source, "rev-parse", "--path-format=absolute", "--git-common-dir")):
        raise TaskStoreError("failed_snapshot_repository_mismatch")
    base = contract["base_commit"]
    head = git_output(root, "rev-parse", "HEAD")
    if git_output(root, "merge-base", base, head) != base:
        raise TaskStoreError("failed_snapshot_base_mismatch")
    _, tree, changed, hygiene = _snapshot_workspace(root, base)
    if any(not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", value) for value in (task.id, task.execution_id)):
        raise TaskStoreError("failed_snapshot_identity_invalid")
    ref = f"refs/nerelan/failed-attempts/{task.id}/{task.execution_id}"
    document = {"task_id": task.id, "execution_id": task.execution_id, "repository": task.repository,
        "binding_ref": task.binding_ref, "executor_kind": task.executor_kind,
        "base_commit": base, "head": head, "tree": tree, "ref": ref,
        "contract_digest": digest(contract), "result_digest": "",
        "failure_kind": OVERLOAD_KIND, "failure_classification": task.failure_classification,
        "feedback": OVERLOAD_FEEDBACK, "changed_paths": list(changed), "hygiene": hygiene}
    previous = _load_evidence(task, FAILED, task.execution_id)
    if previous is not None:
        if previous != document:
            raise TaskStoreError("failed_snapshot_conflict")
        return previous
    found = subprocess.run(["git", "-C", str(root), "show-ref", "--verify", "--hash", ref],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if found.returncode == 0:
        if found.stdout.strip() != tree:
            raise TaskStoreError("failed_snapshot_ref_mismatch")
    else:
        git_output(root, "update-ref", ref, tree, "0" * 40)
    store._bind_artifact_evidence(task.id, category=FAILED, label=task.execution_id, document=document)
    return document


def retain_failed_tree(store, task_id, result, *, worktree, lease=None):
    task = store.get_task(task_id)
    contract = load_contract(task)
    if (contract is None or result.get("passed") is not False
            or result.get("task_id") != task.id or result.get("execution_id") != task.execution_id
            or result.get("contract_digest") != digest(contract)):
        raise TaskStoreError("failed_snapshot_result_mismatch")
    root = Path(worktree).resolve(strict=True)
    from .repository_workspace import resolve_repository_workspace
    source = resolve_repository_workspace(task.repository).repo_dir
    if (resolve_repository_workspace(task.repository, source_dir=root).repo_dir != root
            or git_output(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
            != git_output(source, "rev-parse", "--path-format=absolute", "--git-common-dir")):
        raise TaskStoreError("failed_snapshot_repository_mismatch")
    base = contract["base_commit"]
    head = git_output(root, "rev-parse", "HEAD")
    if git_output(root, "merge-base", base, head) != base:
        raise TaskStoreError("failed_snapshot_base_mismatch")
    _, tree, changed, hygiene = _snapshot_workspace(root, base)
    if any(not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", value) for value in (task.id, task.execution_id)):
        raise TaskStoreError("failed_snapshot_identity_invalid")
    ref = f"refs/nerelan/failed-attempts/{task.id}/{task.execution_id}"
    document = {"task_id": task.id, "execution_id": task.execution_id, "repository": task.repository,
        "binding_ref": task.binding_ref, "executor_kind": task.executor_kind,
        "base_commit": base, "head": head, "tree": tree, "ref": ref,
        "contract_digest": digest(contract), "result_digest": digest(result),
        "failure_kind": result.get("failure_kind"), "feedback": functional_feedback(result),
        "changed_paths": list(changed), "hygiene": hygiene}
    previous = _load_evidence(task, FAILED, task.execution_id)
    if previous is not None and previous != document:
        raise TaskStoreError("failed_snapshot_conflict")
    # Compare-and-create: a different existing ref must never be overwritten.
    found = subprocess.run(["git", "-C", str(root), "show-ref", "--verify", "--hash", ref],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if found.returncode == 0:
        if found.stdout.strip() != tree:
            raise TaskStoreError("failed_snapshot_ref_mismatch")
    else:
        git_output(root, "update-ref", ref, tree, "0" * 40)
    store._bind_artifact_evidence(task.id, category=FAILED, label=task.execution_id,
                                  document=document, lease=lease)
    return document


def failed_snapshot(task, *, root):
    contract = load_contract(task)
    value = _load_evidence(task, FAILED, task.execution_id)
    if value is None or contract is None:
        raise TaskStoreError("failed_snapshot_missing")
    if (value.get("task_id") != task.id or value.get("execution_id") != task.execution_id
            or value.get("repository") != task.repository or value.get("binding_ref") != task.binding_ref
            or value.get("executor_kind") != task.executor_kind
            or value.get("base_commit") != contract["base_commit"]
            or value.get("contract_digest") != digest(contract)
            or value.get("ref") != f"refs/nerelan/failed-attempts/{task.id}/{task.execution_id}"):
        raise TaskStoreError("failed_snapshot_identity_mismatch")
    if value.get("failure_kind") == OVERLOAD_KIND:
        # No validation ran: the interrupted attempt is bound to its own failure instead.
        if (task.status != "FAILED" or value.get("result_digest") != ""
                or value.get("failure_classification") != task.failure_classification):
            raise TaskStoreError("failed_snapshot_stale")
        if (git_output(root, "rev-parse", value["ref"]) != value["tree"]
                or git_output(root, "cat-file", "-t", value["tree"]) != "tree"):
            raise TaskStoreError("failed_snapshot_ref_mismatch")
        return value
    from .functional_validation import RESULT_CATEGORY
    results = [row for row in task.evidence_refs if row.get("category") == RESULT_CATEGORY]
    if not results or results[-1].get("value") != value["result_digest"]:
        raise TaskStoreError("failed_snapshot_stale")
    result = json.loads(results[-1]["detail"])
    if (digest(result) != value["result_digest"] or results[-1].get("raw_json_digest") != digest(result)
            or result.get("task_id") != task.id or result.get("execution_id") != task.execution_id
            or result.get("contract_digest") != digest(contract) or result.get("passed") is not False
            or result.get("tree_before") != value["tree"] or result.get("failure_kind") != value["failure_kind"]):
        raise TaskStoreError("failed_snapshot_result_mismatch")
    if (git_output(root, "rev-parse", value["ref"]) != value["tree"]
            or git_output(root, "cat-file", "-t", value["tree"]) != "tree"):
        raise TaskStoreError("failed_snapshot_ref_mismatch")
    return value


def recovery_input(task):
    return _load_evidence(task, FIXUP, task.execution_id)


def restore_failed_tree(store, task_id, *, worktree, lease=None):
    task = store.get_task(task_id)
    binding = recovery_input(task)
    if binding is None:
        return
    if lease is not None:
        store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)
    source = store.get_task(binding["source_task_id"])
    root = Path(worktree).resolve(strict=True)
    snapshot = failed_snapshot(source, root=root)
    original, current = load_contract(source), load_contract(task)
    if (binding.get("snapshot_digest") != digest(snapshot)
            or binding.get("task_id") != task.id or binding.get("execution_id") != task.execution_id
            or task.binding_ref != source.binding_ref or task.executor_kind != source.executor_kind
            or original is None or current is None
            or {k: v for k, v in current.items() if k != "task_id"}
               != {k: v for k, v in original.items() if k != "task_id"}):
        raise TaskStoreError("failed_snapshot_recovery_mismatch")
    previous = _load_evidence(task, "FailedTreeRestored", task.execution_id)
    if previous is not None:
        if previous != binding:
            raise TaskStoreError("failed_snapshot_restore_conflict")
        return  # Never overwrite work already executed after restoration.
    base = snapshot["base_commit"]
    _, tree, _, _ = _snapshot_workspace(root, base)
    if git_output(root, "rev-parse", "HEAD") != base:
        raise TaskStoreError("failed_snapshot_destination_head_changed")
    if tree != git_output(root, "rev-parse", f"{base}^{{tree}}"):
        # A crash after apply but before binding may only reuse the exact failed tree.
        if tree != snapshot["tree"]:
            raise TaskStoreError("failed_snapshot_destination_changed")
    else:
        patch = subprocess.check_output(["git", "-C", str(root), "diff", "--binary", base, snapshot["tree"], "--"], timeout=60)
        if patch:
            subprocess.run(["git", "-C", str(root), "apply", "--whitespace=nowarn", "-"], input=patch, check=True,
                           capture_output=True, timeout=60)
    if _snapshot_workspace(root, base)[1] != snapshot["tree"]:
        raise TaskStoreError("failed_snapshot_restore_mismatch")
    store._bind_artifact_evidence(task.id, category="FailedTreeRestored", label=task.execution_id,
                                  document=binding, lease=lease)


def record_attempt_disposition(store, task, *, reused, snapshot_digest):
    """Immutable per-execution observation; unknown measurements stay unknown."""
    current = store.get_task(task.id)
    if current.execution_id != task.execution_id:
        raise TaskStoreError("attempt_disposition_execution_changed")
    task = current
    if _load_evidence(task, "AttemptDisposition", task.execution_id) is not None:
        return
    from .usage_ledger import task_token_records
    record = next((r for r in task_token_records(store) if r["task_id"] == task.id), {})
    elapsed = [e.metadata.get("duration_ms") for e in store.get_events(task.id)
               if e.type == "EXECUTOR_COMPLETED"]
    duration = next((v for v in reversed(elapsed) if type(v) is int and v >= 0), None)
    elapsed_source = "executor_completed.duration_ms" if duration is not None else None
    if duration is None:
        events = store.get_events(task.id)
        starts = [e.timestamp for e in events if e.type == "EXECUTOR_RUNNING"]
        ends = [e.timestamp for e in events if e.type == "EXECUTOR_COMPLETED"]
        if starts and ends:
            try:
                measured = (datetime.fromisoformat(ends[-1].replace("Z", "+00:00"))
                            - datetime.fromisoformat(starts[0].replace("Z", "+00:00"))).total_seconds()
                if measured >= 0:
                    duration = round(measured * 1000)
                    elapsed_source = "executor_event_timestamps"
            except (ValueError, TypeError):
                pass
    store._bind_artifact_evidence(task.id, category="AttemptDisposition", label=task.execution_id,
        document={"task_id": task.id, "execution_id": task.execution_id,
                  "disposition": "reused" if reused else "discarded", "snapshot_digest": snapshot_digest,
                  "tokens": record.get("tokens"), "token_source": record.get("source"),
                  "elapsed_ms": duration, "elapsed_source": elapsed_source, "discarded_tokens": None if reused else record.get("tokens"),
                  "discarded_elapsed_ms": None if reused else duration})
