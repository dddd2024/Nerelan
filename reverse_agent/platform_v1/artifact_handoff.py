"""Explicit approved input identity for dependent Goal tasks.

Git owns artifact contents; the existing TaskStore owns their approved bindings.
An ordering dependency alone never grants access to another task's worktree.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from .run_store import TaskStoreError

CONTRACT_CATEGORY = "ArtifactContract"
ACCEPTED_CATEGORY = "AcceptedArtifact"
INPUT_CATEGORY = "ArtifactInput"


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def normalize_input(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != {"plan_task_id"}:
        raise TaskStoreError("artifact_input_invalid")
    source = value["plan_task_id"]
    if not isinstance(source, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", source):
        raise TaskStoreError("artifact_input_invalid")
    return {"plan_task_id": source}


def validate_plan_inputs(tasks: Sequence[Any]) -> None:
    by_id = {task.id: task for task in tasks}
    for task in tasks:
        selected = task.artifact_input
        if selected is None:
            continue
        source_id = selected["plan_task_id"]
        if source_id == task.id or source_id not in task.dependencies or source_id not in by_id:
            raise TaskStoreError(f"artifact_input_not_dependency:{task.id}")
        if not task.validation_checks or not by_id[source_id].validation_checks:
            raise TaskStoreError(f"artifact_input_requires_functional_checks:{task.id}")


def freeze_handoff_contract(store: Any, task: Any, *, goal: Any, plan_task: Any,
                            base_commit: str) -> dict[str, Any] | None:
    export_required = any(normalize_input(raw.get("artifact_input")) == {"plan_task_id": plan_task.id}
                          for raw in goal.tasks)
    if plan_task.artifact_input is None and not export_required:
        return None
    if not re.fullmatch(r"[0-9a-f]{40}", base_commit):
        raise TaskStoreError("artifact_approved_base_invalid")
    contract = {"version": 1, "task_id": task.id, "repository": task.repository,
                "goal_id": goal.id, "goal_revision": goal.revision,
                "goal_artifact_digest": goal.artifact_digest, "plan_task_id": plan_task.id,
                "base_commit": base_commit, "artifact_input": plan_task.artifact_input,
                "export_required": export_required, "capability": plan_task.capability}
    store._bind_artifact_evidence(task.id, category=CONTRACT_CATEGORY,
                                 label="approved_goal_artifact", document=contract)
    return contract


def _load_evidence(task: Any, category: str, label: str) -> dict[str, Any] | None:
    rows = [row for row in task.evidence_refs if row.get("category") == category
            and row.get("label") == label]
    if not rows:
        return None
    try:
        if len(rows) != 1:
            raise ValueError
        row = rows[0]
        value = json.loads(row["detail"])
        expected_status = "APPROVED" if category == CONTRACT_CATEGORY else "BOUND"
        if (not isinstance(value, dict) or row["value"] != _digest(value)
                or row["raw_json_digest"] != _digest(value) or row["status"] != expected_status):
            raise ValueError
        return value
    except (ValueError, TypeError, KeyError) as exc:
        raise TaskStoreError("artifact_evidence_invalid") from exc


def load_handoff_contract(task: Any) -> dict[str, Any] | None:
    contract = _load_evidence(task, CONTRACT_CATEGORY, "approved_goal_artifact")
    if contract is None:
        return None
    try:
        fields = {"version", "task_id", "repository", "goal_id", "goal_revision", "goal_artifact_digest",
                  "plan_task_id", "base_commit", "artifact_input", "export_required", "capability"}
        if (set(contract) != fields or contract["version"] != 1
                or contract["task_id"] != task.id or contract["repository"] != task.repository
                or type(contract["goal_revision"]) is not int or contract["goal_revision"] < 1
                or not re.fullmatch(r"[0-9a-f]{40}", contract["base_commit"])
                or not re.fullmatch(r"[0-9a-f]{64}", contract["goal_artifact_digest"])
                or not isinstance(contract["goal_id"], str) or not contract["goal_id"]
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", contract["plan_task_id"])
                or type(contract["export_required"]) is not bool
                or contract["capability"] not in {"execute_task", "validate_task"}
                or normalize_input(contract["artifact_input"]) != contract["artifact_input"]):
            raise ValueError
        return contract
    except (ValueError, TypeError, KeyError) as exc:
        raise TaskStoreError("artifact_contract_invalid") from exc


def validation_only_input(task: Any) -> bool:
    """Only the frozen approved input contract selects host-only validation."""
    contract = load_handoff_contract(task)
    return bool(contract is not None and contract["artifact_input"] is not None
                and contract["capability"] == "validate_task")


def _current_goal(store: Any, task: Any, contract: Mapping[str, Any]) -> Any:
    from .control_store import PlatformControlStore
    control = PlatformControlStore(store)
    goal = control.get_goal(contract["goal_id"])
    if (goal.repository != task.repository or goal.revision != contract["goal_revision"]
            or goal.artifact_digest != contract["goal_artifact_digest"]):
        raise TaskStoreError("artifact_goal_binding_changed")
    links = control.list_goal_tasks(goal.id)
    if not any(link["task_id"] == task.id and link["plan_task_id"] == contract["plan_task_id"]
               and link["goal_revision"] == contract["goal_revision"] for link in links):
        raise TaskStoreError("artifact_goal_link_changed")
    planned = [item for item in goal.tasks if item.get("id") == contract["plan_task_id"]]
    if (len(planned) != 1 or normalize_input(planned[0].get("artifact_input")) != contract["artifact_input"]
            or planned[0].get("capability", "execute_task") != contract["capability"]
            or (contract["artifact_input"] is not None
                and contract["artifact_input"]["plan_task_id"] not in planned[0].get("dependencies", []))):
        raise TaskStoreError("artifact_approved_plan_changed")
    return goal


def _matching_functional_contract(task: Any, contract: Mapping[str, Any]) -> None:
    from .functional_validation import load_contract
    functional = load_contract(task)
    if functional is None or any(functional[key] != contract[key] for key in (
            "base_commit", "goal_id", "goal_revision", "goal_artifact_digest", "plan_task_id")):
        raise TaskStoreError("artifact_functional_contract_mismatch")


def _validated_proof(task: Any, identity: str) -> dict[str, Any]:
    from dataclasses import replace
    from .functional_validation import FUNCTIONAL_COMMAND_ID, functional_evidence
    candidate = replace(task, status="VALIDATING", validation_command_id=FUNCTIONAL_COMMAND_ID,
                        validation_exit_code=0, validation_output_digest=identity)
    proof = functional_evidence(candidate)
    if proof.get("verified") is not True or proof.get("result_digest") != identity:
        raise TaskStoreError("artifact_functional_proof_required")
    return proof


def _verify_proof_workspace(task: Any, proof: Mapping[str, Any], root: Path) -> None:
    from reverse_agent.executor_neutral.core import _snapshot_workspace
    from .functional_validation import git_output
    from .repository_workspace import resolve_repository_workspace
    if resolve_repository_workspace(task.repository, source_dir=root).repo_dir != root:
        raise TaskStoreError("artifact_worktree_root_required")
    source = resolve_repository_workspace(task.repository).repo_dir
    if git_output(root, "rev-parse", "--path-format=absolute", "--git-common-dir") != git_output(
            source, "rev-parse", "--path-format=absolute", "--git-common-dir"):
        raise TaskStoreError("artifact_source_object_store_mismatch")
    if (git_output(root, "rev-parse", "HEAD") != proof["head"]
            or git_output(root, "merge-base", proof["base_commit"], proof["head"]) != proof["base_commit"]):
        raise TaskStoreError("artifact_workspace_changed")
    _, tree, _, hygiene = _snapshot_workspace(root, proof["base_commit"])
    if tree != proof["tree"] or hygiene["exit_code"] != 0:
        raise TaskStoreError("artifact_workspace_changed")


def _retention_ref(task: Any) -> str:
    if any(not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", value)
           for value in (task.id, task.execution_id)):
        raise TaskStoreError("artifact_ref_identity_invalid")
    return f"refs/nerelan/accepted-artifacts/{task.id}/{task.execution_id}"


def retain_validated_artifact(store: Any, task_id: str, identity: str, *,
                              worktree: str | Path, lease: Any = None) -> dict[str, Any] | None:
    """Retain the already persisted host proof's tree without changing HEAD/index.

    Git creation precedes the immutable SQLite binding. A crash leaves at most
    the same content-addressed object/ref; it cannot make a consumer accepted.
    Replaying this operation uses the original proof and identical commit bytes.
    """
    from .functional_validation import git_output
    task = store.get_task(task_id)
    contract = load_handoff_contract(task)
    if contract is None or not contract["export_required"]:
        return None
    if lease is not None:
        store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)
    _current_goal(store, task, contract)
    _matching_functional_contract(task, contract)
    proof = _validated_proof(task, identity)
    if proof["base_commit"] != contract["base_commit"]:
        raise TaskStoreError("artifact_approved_base_mismatch")
    if lease is not None and (proof["run_id"] != lease.run_id
            or type(proof["lease_epoch"]) is not int or not 1 <= proof["lease_epoch"] <= lease.epoch):
        raise TaskStoreError("artifact_proof_lease_mismatch")
    root = Path(worktree).resolve(strict=True)
    _verify_proof_workspace(task, proof, root)
    ref = _retention_ref(task)
    previous = _load_evidence(task, ACCEPTED_CATEGORY, task.execution_id)
    if previous is not None and previous.get("result_digest") != identity:
        raise TaskStoreError("artifact_binding_conflict")
    env = {key: value for key, value in os.environ.items() if key in {
        "PATH", "Path", "SystemRoot", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR"}}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME="Nerelan artifact acceptance", GIT_COMMITTER_NAME="Nerelan artifact acceptance",
               GIT_AUTHOR_EMAIL="artifact@nerelan.invalid", GIT_COMMITTER_EMAIL="artifact@nerelan.invalid",
               GIT_AUTHOR_DATE="2000-01-01T00:00:00+00:00", GIT_COMMITTER_DATE="2000-01-01T00:00:00+00:00")
    message = f"Accepted task artifact\n\nTask: {task.id}\nExecution: {task.execution_id}\nResult: {identity}"
    created = subprocess.run(["git", "-C", str(root), "-c", "commit.gpgSign=false",
        "-c", f"core.hooksPath={os.devnull}", "commit-tree",
        proof["tree"], "-p", proof["head"], "-m", message], env=env, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding="utf-8", timeout=15, check=False)
    commit = created.stdout.strip()
    if created.returncode or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise TaskStoreError("artifact_commit_creation_failed")
    binding = {"version": 1, "task_id": task.id, "execution_id": task.execution_id,
        "repository": task.repository, "goal_id": contract["goal_id"], "goal_revision": contract["goal_revision"],
        "goal_artifact_digest": contract["goal_artifact_digest"], "plan_task_id": contract["plan_task_id"],
        "base_commit": proof["base_commit"], "contract_digest": proof["contract_digest"],
        "result_digest": identity, "source_head": proof["head"], "tree": proof["tree"],
        "commit": commit, "ref": ref, "run_id": proof["run_id"], "lease_epoch": proof["lease_epoch"]}
    if previous is not None and previous != binding:
        raise TaskStoreError("artifact_binding_conflict")
    # The explicit zero old value permits creation only, never replacement.
    retained = subprocess.run(["git", "-C", str(root), "-c", f"core.hooksPath={os.devnull}",
        "update-ref", ref, commit, "0" * 40],
        env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=15, check=False)
    if retained.returncode and git_output(root, "rev-parse", "--verify", ref) != commit:
        raise TaskStoreError("artifact_retention_ref_conflict")
    if git_output(root, "rev-parse", f"{ref}^{{tree}}") != proof["tree"]:
        raise TaskStoreError("artifact_retention_tree_mismatch")
    _verify_proof_workspace(task, proof, root)
    store._bind_artifact_evidence(task.id, category=ACCEPTED_CATEGORY, label=task.execution_id,
                                 document=binding, lease=lease)
    return binding


def recover_export_validation(store: Any, task_id: str, *, worktree: str | Path,
                              lease: Any = None) -> str | None:
    """Reuse persisted real checks after a crash in the retention/acceptance gap."""
    from .functional_validation import RESULT_CATEGORY
    task = store.get_task(task_id)
    contract = load_handoff_contract(task)
    if contract is None or not contract["export_required"]:
        return None
    if task.status in {"FAILED", "BLOCKED", "CANCELLED"}:
        raise TaskStoreError("artifact_terminal_task_requires_new_execution")
    results = []
    for row in task.evidence_refs:
        if row.get("category") == RESULT_CATEGORY:
            try:
                result = json.loads(row["detail"])
                if result.get("execution_id") == task.execution_id:
                    results.append(row)
            except (ValueError, TypeError, AttributeError) as exc:
                raise TaskStoreError("artifact_functional_evidence_invalid") from exc
    if not results or results[-1].get("status") != "VERIFIED":
        return None
    identity = results[-1]["value"]
    retain_validated_artifact(store, task_id, identity, worktree=worktree, lease=lease)
    return identity


def load_input_binding(task: Any) -> dict[str, Any] | None:
    contract = load_handoff_contract(task)
    if contract is None or contract["artifact_input"] is None:
        return None
    binding = _load_evidence(task, INPUT_CATEGORY, task.execution_id)
    if binding is None:
        raise TaskStoreError("artifact_input_not_bound")
    try:
        fields = {"version", "task_id", "execution_id", "repository", "goal_id", "goal_revision",
                  "goal_artifact_digest", "plan_task_id", "base_commit", "capability", "run_id",
                  "lease_epoch", "producer", "producer_digest"}
        producer = binding["producer"]
        if (set(binding) != fields or binding["version"] != 1 or binding["task_id"] != task.id
                or binding["execution_id"] != task.execution_id
                or any(binding[key] != contract[key] for key in ("repository", "goal_id", "goal_revision",
                    "goal_artifact_digest", "plan_task_id", "base_commit", "capability"))
                or not isinstance(producer, dict) or binding["producer_digest"] != _digest(producer)
                or producer["plan_task_id"] != contract["artifact_input"]["plan_task_id"]
                or any(producer[key] != contract[key] for key in (
                    "repository", "goal_id", "goal_revision", "goal_artifact_digest", "base_commit"))
                or any(not re.fullmatch(r"[0-9a-f]{40}", producer[key]) for key in ("commit", "tree"))
                or (binding["run_id"] and (type(binding["lease_epoch"]) is not int or binding["lease_epoch"] < 1))
                or (not binding["run_id"] and binding["lease_epoch"] is not None)):
            raise ValueError
        return binding
    except (TypeError, ValueError, KeyError) as exc:
        raise TaskStoreError("artifact_input_binding_invalid") from exc


def _producer_worktree(store: Any, producer: Any, proof: Mapping[str, Any]) -> Path:
    if proof["run_id"]:
        from .functional_validation import accepted_checkpoint_proof
        run = store._get_durable_run(proof["run_id"])
        if run.task_id != producer.id or not accepted_checkpoint_proof(producer, run)["passed"]:
            raise TaskStoreError("artifact_producer_checkpoint_changed")
        return Path(run.worktree_path).resolve(strict=True)
    paths = set()
    for event in producer.events:
        if event.get("type") != "WORKSPACE_READY":
            continue
        metadata = event.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        if (isinstance(metadata, Mapping) and metadata.get("execution_id") == producer.execution_id
                and isinstance(metadata.get("workspace"), str)):
            paths.add(Path(metadata["workspace"]).resolve(strict=True))
    if len(paths) != 1:
        raise TaskStoreError("artifact_producer_worktree_ambiguous")
    return next(iter(paths))


def bind_consumer_input(store: Any, task_id: str, *, lease: Any = None,
                        allow_create: bool = True) -> dict[str, Any] | None:
    """Observe the exact producer and bind one consumer input before dispatch."""
    from .control_store import PlatformControlStore
    from .functional_validation import functional_evidence, git_output
    task = store.get_task(task_id)
    contract = load_handoff_contract(task)
    if contract is None or contract["artifact_input"] is None:
        return None
    if task.executor_kind != "opencode":
        raise TaskStoreError("artifact_input_requires_real_executor")
    if lease is not None:
        store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)
    goal = _current_goal(store, task, contract)
    _matching_functional_contract(task, contract)
    source_id = contract["artifact_input"]["plan_task_id"]
    links = [link for link in PlatformControlStore(store).list_goal_tasks(goal.id)
             if link["plan_task_id"] == source_id]
    if len(links) != 1:
        raise TaskStoreError("artifact_producer_missing")
    producer = store.get_task(links[0]["task_id"])
    producer_contract = load_handoff_contract(producer)
    if producer.status != "READY_FOR_REVIEW" or producer_contract is None or not producer_contract["export_required"]:
        raise TaskStoreError("artifact_producer_not_accepted")
    _current_goal(store, producer, producer_contract)
    _matching_functional_contract(producer, producer_contract)
    proof = functional_evidence(producer)
    if proof.get("verified") is not True:
        raise TaskStoreError("artifact_producer_not_verified")
    accepted = _load_evidence(producer, ACCEPTED_CATEGORY, producer.execution_id)
    if accepted is None:
        raise TaskStoreError("artifact_producer_retention_missing")
    expected = {"version": 1, "task_id": producer.id, "execution_id": producer.execution_id,
        "repository": task.repository, "goal_id": goal.id, "goal_revision": goal.revision,
        "goal_artifact_digest": goal.artifact_digest, "plan_task_id": source_id,
        "base_commit": contract["base_commit"], "contract_digest": proof["contract_digest"],
        "result_digest": proof["result_digest"], "source_head": proof["head"], "tree": proof["tree"],
        "run_id": proof["run_id"], "lease_epoch": proof["lease_epoch"], "ref": _retention_ref(producer)}
    if (set(accepted) != {*expected, "commit"} or any(accepted[key] != value for key, value in expected.items())
            or not isinstance(accepted["commit"], str) or not re.fullmatch(r"[0-9a-f]{40}", accepted["commit"])):
        raise TaskStoreError("artifact_producer_binding_changed")
    root = _producer_worktree(store, producer, proof)
    _verify_proof_workspace(producer, proof, root)
    if (git_output(root, "rev-parse", "--verify", accepted["ref"]) != accepted["commit"]
            or git_output(root, "rev-parse", f"{accepted['commit']}^{{tree}}") != accepted["tree"]
            or git_output(root, "rev-list", "--parents", "-n", "1", accepted["commit"]).split()
                != [accepted["commit"], accepted["source_head"]]):
        raise TaskStoreError("artifact_retained_object_changed")
    previous = _load_evidence(task, INPUT_CATEGORY, task.execution_id)
    if previous is None and not allow_create:
        raise TaskStoreError("artifact_input_not_bound")
    if previous is not None:
        previous = load_input_binding(task)
    run_id = lease.run_id if lease is not None else (previous["run_id"] if previous else "")
    epoch = previous["lease_epoch"] if previous else (lease.epoch if lease is not None else None)
    if lease is not None and (type(epoch) is not int or not 1 <= epoch <= lease.epoch):
        raise TaskStoreError("artifact_input_lease_changed")
    if lease is None and allow_create and run_id:
        raise TaskStoreError("artifact_input_requires_run_lease")
    binding = {key: contract[key] for key in ("version", "task_id", "repository", "goal_id", "goal_revision",
        "goal_artifact_digest", "plan_task_id", "base_commit", "capability")}
    binding.update(execution_id=task.execution_id, run_id=run_id, lease_epoch=epoch,
                   producer=accepted, producer_digest=_digest(accepted))
    if previous is not None and binding != previous:
        raise TaskStoreError("artifact_input_binding_conflict")
    if allow_create:
        store._bind_artifact_evidence(task_id, category=INPUT_CATEGORY, label=task.execution_id,
                                     document=binding, lease=lease)
    return binding


def prepared_original_base(task: Any, prepared_head: str) -> str:
    binding = load_input_binding(task)
    if binding is None:
        return prepared_head
    if prepared_head != binding["producer"]["commit"]:
        raise TaskStoreError("artifact_prepared_input_mismatch")
    return binding["base_commit"]


def check_input_snapshot(task: Any, root: Path, *, head: str, tree: str,
                         require_change: bool = True) -> dict[str, Any] | None:
    from .functional_validation import git_output
    binding = load_input_binding(task)
    if binding is None:
        return None
    source = binding["producer"]
    if git_output(root, "merge-base", source["commit"], head) != source["commit"]:
        raise TaskStoreError("artifact_input_ancestry_changed")
    if binding["capability"] == "validate_task" and tree != source["tree"]:
        raise TaskStoreError("artifact_validation_input_changed")
    if require_change and binding["capability"] == "execute_task" and tree == source["tree"]:
        raise TaskStoreError("artifact_consumer_implementation_missing")
    return binding
