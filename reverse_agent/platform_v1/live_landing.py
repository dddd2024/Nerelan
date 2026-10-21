"""Bounded gh boundary for governed landing; no provider or credential discovery."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .github_adapter import GitHubAdapterError


class LiveLandingGitHubAdapter:
    def __init__(self, workspace):
        self.workspace = str(Path(workspace).resolve())

    def _run(self, args, *, json_output=True, verdict=False, checker=False):
        options = {}
        cwd = self.workspace
        if checker:
            # Run trusted host code, with Git explicitly bound to the retained
            # worktree. Never import the candidate's landing_review.py.
            gitdir = Path(self.workspace) / ".git"
            if gitdir.is_file():
                text = gitdir.read_text(encoding="utf-8").strip()
                if not text.startswith("gitdir: "):
                    raise GitHubAdapterError("landing_gitdir_invalid")
                gitdir = (Path(self.workspace) / text[8:]).resolve()
            options["env"] = dict(os.environ, GIT_DIR=str(gitdir), GIT_WORK_TREE=self.workspace)
            cwd = str(Path(__file__).resolve().parents[2])
        try:
            result = subprocess.run(args, cwd=cwd, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", timeout=45, **options)
        except subprocess.TimeoutExpired as exc:
            raise GitHubAdapterError("landing_command_timeout") from exc
        if result.returncode and not verdict:
            raise GitHubAdapterError("landing_command_failed")
        return json.loads(result.stdout) if json_output else result.stdout

    def _api(self, state, suffix):
        return self._run(["gh", "api", f"repos/{state['repository']}/{suffix}"])

    def _pages(self, state, suffix):
        pages = self._run(["gh", "api", "--paginate", "--slurp",
                           f"repos/{state['repository']}/{suffix}"])
        return [item for page in pages for item in page]

    def observe_pr(self, state):
        pr = self._api(state, f"pulls/{state['pr_number']}")
        main = self._api(state, "git/ref/heads/main")["object"]["sha"]
        comparison = self._api(state, f"compare/{main}...{pr['head']['sha']}")
        files = self._pages(state, f"pulls/{state['pr_number']}/files?per_page=100")
        if len(files) != pr["changed_files"]:
            raise GitHubAdapterError("landing_changed_paths_incomplete")
        return dict(repository=pr["base"]["repo"]["full_name"], base_branch=pr["base"]["ref"],
                    head_sha=pr["head"]["sha"], main_sha=main, draft=pr["draft"],
                    state=pr["state"].upper(), merged=pr["merged"], merge_commit=pr["merge_commit_sha"],
                    behind=comparison["behind_by"] > 0, body=pr.get("body") or "",
                    changed_paths=sorted({p for f in files for p in (f["filename"], f.get("previous_filename", f["filename"]))}))

    def observe_checks(self, state):
        pages = self._run(["gh", "api", "--paginate", "--slurp",
            f"repos/{state['repository']}/commits/{state['head_sha']}/check-runs?per_page=100"])
        checks = {}
        for row in [r for page in pages for r in page["check_runs"]]:
            name = row["name"]
            if row.get("app", {}).get("slug") != "github-actions":
                continue
            if name not in checks or row["id"] > checks[name]["id"]:
                checks[name] = dict(id=row["id"], head_sha=row["head_sha"], status=row["status"],
                    conclusion=row["conclusion"], fresh=bool(row.get("completed_at")))
        return {"checks": checks}

    def reconcile_operation(self, state, operation, claim_id):
        pr = self.observe_pr(state)
        outcome = "UNKNOWN"
        if operation == "merge":
            if pr["merged"] and pr["head_sha"] == state["head_sha"] and pr["merge_commit"] == pr["main_sha"]:
                outcome = "SUCCEEDED"
            # Open does not prove a timed-out merge request cannot still finish.
        elif operation == "mark_ready":
            if not pr["draft"] and pr["head_sha"] == state["head_sha"]:
                outcome = "SUCCEEDED"
        elif operation == "update_branch":
            if pr["head_sha"] != state["head_sha"] and not pr["behind"]:
                commit = self._api(state, f"git/commits/{pr['head_sha']}")
                parents = commit["parents"]
                if len(parents) == 2 and parents[0]["sha"] == state["head_sha"]:
                    main_proof = self._api(state, f"compare/{parents[1]['sha']}...{pr['main_sha']}")
                    if main_proof["status"] in {"ahead", "identical"}:
                        outcome = "SUCCEEDED"
        return dict(identity=state["identity"], operation=operation, claim_id=claim_id,
                    outcome=outcome, merge_commit=pr["merge_commit"], main_sha=pr["main_sha"])

    def reconcile_review_comment(self, state, claim_id):
        comments = self._pages(state, f"issues/{state['pr_number']}/comments?per_page=100")
        found = any(f"<!-- nerelan-operation:{claim_id} -->" in (c.get("body") or "") for c in comments)
        return dict(identity=state["identity"], operation="review_comment", claim_id=claim_id,
                    outcome="SUCCEEDED" if found else "UNKNOWN")

    def post_review_comment(self, state, claim_id, body):
        self._run(["gh", "api", f"repos/{state['repository']}/issues/{state['pr_number']}/comments",
                   "-f", "body=" + body])

    def update_branch(self, state, claim_id):
        self._run(["gh", "api", "--method", "PUT",
                   f"repos/{state['repository']}/pulls/{state['pr_number']}/update-branch",
                   "-f", "expected_head_sha=" + state["head_sha"]])

    def mark_ready(self, state, claim_id):
        self._run(["gh", "pr", "ready", str(state["pr_number"]), "--repo", state["repository"]], json_output=False)

    def invoke_verdict(self, state, claim_id):
        if claim_id == "assessment":
            # Use the existing checker unchanged, including its Git proof of
            # carry-over. Fetch only into the trusted retained producer repository.
            self._run(["git", "fetch", "origin", "main"], json_output=False)
            self._run(["git", "fetch", "origin", f"refs/pull/{state['pr_number']}/head"], json_output=False)
            entries = []
            for suffix, timestamp in (("comments", "created_at"), ("reviews", "submitted_at")):
                kind = "issues" if suffix == "comments" else "pulls"
                for row in self._pages(state, f"{kind}/{state['pr_number']}/{suffix}?per_page=100"):
                    if row.get("state", "").upper() in {"DISMISSED", "PENDING"}:
                        continue
                    entries.append(dict(body=row.get("body") or "", author=row.get("user", {}).get("login", ""),
                                        association=row.get("author_association", ""), created_at=row.get(timestamp) or ""))
            script = ("import json,sys; from reverse_agent.landing_review import ReviewEntry,evaluate_review_with_carry_over; "
                      "v=evaluate_review_with_carry_over(sys.argv[1],[ReviewEntry(**r) for r in json.loads(sys.argv[2])]); "
                      "print(json.dumps(dict(passed=v.accepted,**v.to_dict())))")
            result = self._run([sys.executable, "-c", script, state["head_sha"], json.dumps(entries)], checker=True)
            from reverse_agent.landing_review import strip_code_fences, TRUSTED_ASSOCIATIONS
            prefix = f"Nerelan-R2: CONFIRM {state['head_sha']} "
            result["confirmed_decisions"] = [line[len(prefix):] for row in entries
                if row["association"] in TRUSTED_ASSOCIATIONS and row["created_at"]
                and row["author"] == result.get("reviewer")
                for line in strip_code_fences(row["body"]).splitlines() if line.startswith(prefix)]
            return result
        # This exact command is mandatory immediately before gh pr merge.
        return self._run([sys.executable, "-m", "reverse_agent.landing_review", "verdict",
                          "--repository", state["repository"], "--pr", str(state["pr_number"]), "--head", state["head_sha"]], verdict=True, checker=True)

    def merge_head_matched(self, state, claim_id):
        self._run(["gh", "pr", "merge", str(state["pr_number"]), "--repo", state["repository"],
                   "--merge", "--match-head-commit", state["head_sha"]], json_output=False)


class RoutedLandingGitHubAdapter:
    """Resolve the retained producer worktree anew, never a browser supplied path."""
    def __init__(self, control_store):
        self.control_store = control_store

    def __getattr__(self, name):
        def invoke(state, *args):
            from . import artifact_handoff as artifacts, functional_validation as functional
            from .run_store import TaskStoreError
            for row in self.control_store.list_goal_tasks(state["goal_id"]):
                task = self.control_store.task_store.get_task(row["task_id"])
                record = self.control_store.get_publication(task.id)
                if record and record.pr_number == state["pr_number"]:
                    proof = functional.functional_evidence(task)
                    workspace = artifacts._producer_worktree(self.control_store.task_store, task, proof)
                    return getattr(LiveLandingGitHubAdapter(workspace), name)(state, *args)
            raise TaskStoreError("landing_retained_workspace_required")
        return invoke
