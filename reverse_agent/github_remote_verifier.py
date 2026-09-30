"""Fail-closed GitHub evidence verifier for mainline landing validation.

The production implementation uses only read-only GitHub REST endpoints.  It
never accepts locally asserted workflow, pull-request, approval, or authority
facts as remote evidence.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


OWNER_LANDING_ATTESTATION_MARKER = "OWNER_LANDING_MERGE_ATTESTATION"
OWNER_LANDING_ATTESTATION_BLOCK = "owner_landing_merge_attestation"


class GitHubEvidenceError(RuntimeError):
    """Raised when trusted GitHub evidence cannot be obtained or verified."""


def _decode_github_contents_base64(content: str) -> bytes:
    normalized = content.translate(str.maketrans("", "", " \t\r\n"))
    try:
        return base64.b64decode(normalized, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("invalid_base64_content") from exc


def _source_oid(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _source_component(value: Any) -> bool:
    if not isinstance(value, str) or not value or len(value) > 255:
        return False
    if value in {".", ".."} or value.casefold() == ".git":
        return False
    if any(c in value for c in "/\\:") or any(ord(c) < 32 or ord(c) == 127 for c in value):
        return False
    try:
        return len(value.encode("utf-8", errors="strict")) <= 255
    except UnicodeError:
        return False


def _source_object_oid(kind: str, raw: bytes) -> str:
    return hashlib.sha1(f"{kind} {len(raw)}\0".encode("ascii") + raw).hexdigest()


def _verified_source_tree(payload: Any, expected_sha: str) -> dict[str, dict[str, Any]]:
    """Verify a complete nonrecursive tree against Git's canonical encoding."""
    if not isinstance(payload, dict) or payload.get("sha") != expected_sha:
        raise GitHubEvidenceError("tree_identity_mismatch")
    if payload.get("truncated") is not False:
        raise GitHubEvidenceError("source_tree_incomplete")
    entries = payload.get("tree")
    if not isinstance(entries, list) or len(entries) > 10000:
        raise GitHubEvidenceError("invalid_source_tree_entries")
    kinds = {"040000": "tree", "100644": "blob", "100755": "blob", "120000": "blob", "160000": "commit"}
    by_name: dict[str, dict[str, Any]] = {}
    encoded: list[tuple[bytes, bytes]] = []
    for entry in entries:
        if not isinstance(entry, dict) or not _source_component(entry.get("path")):
            raise GitHubEvidenceError("invalid_source_tree_entry")
        name, mode, oid = entry["path"], entry.get("mode"), entry.get("sha")
        if name in by_name:
            raise GitHubEvidenceError("duplicate_source_tree_entry")
        if not isinstance(mode, str) or mode not in kinds or entry.get("type") != kinds[mode] or not _source_oid(oid):
            raise GitHubEvidenceError("invalid_source_tree_entry")
        by_name[name] = entry
        name_bytes = name.encode("utf-8")
        sort_key = name_bytes + (b"/" if mode == "040000" else b"")
        raw = mode.lstrip("0").encode("ascii") + b" " + name_bytes + b"\0" + bytes.fromhex(oid)
        encoded.append((sort_key, raw))
    raw_tree = b"".join(raw for _, raw in sorted(encoded))
    if _source_object_oid("tree", raw_tree) != expected_sha:
        raise GitHubEvidenceError("source_tree_digest_mismatch")
    return by_name


class GitHubRemoteAcceptanceVerifier:
    """Verify exact GitHub objects against a fixed repository identity."""

    def __init__(
        self,
        *,
        repository: str,
        token: str,
        api_url: str = "https://api.github.com",
    ) -> None:
        if not re.fullmatch(r"[^/\s]+/[^/\s]+", repository):
            raise GitHubEvidenceError("invalid_repository_identity")
        if not token:
            raise GitHubEvidenceError("missing_github_token")
        self.repository = repository
        self.token = token
        self.api_url = api_url.rstrip("/")

    @classmethod
    def from_env(cls) -> "GitHubRemoteAcceptanceVerifier":
        repository = os.environ.get("GITHUB_REPOSITORY", "")
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
        return cls(repository=repository, token=token)

    def _request_json(self, path: str) -> Any:
        request = urllib.request.Request(
            f"{self.api_url}{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "reverse-agent-mainline-validator",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise GitHubEvidenceError(f"github_http_status:{response.status}")
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            raise GitHubEvidenceError(f"github_api_failure:{type(exc).__name__}") from exc

    def verify_workflow_run(
        self,
        *,
        run_id: int,
        expected_head_sha: str,
        expected_workflow_file: str,
        expected_event: str,
        expected_run_attempt: int = 1,
    ) -> dict[str, Any]:
        try:
            run = self._request_json(
                f"/repos/{self.repository}/actions/runs/{int(run_id)}"
            )
            observed_repository = str(
                ((run.get("repository") or {}).get("full_name")) or ""
            )
            checks = {
                "repository": observed_repository == self.repository,
                "path": run.get("path") == expected_workflow_file,
                "event": run.get("event") == expected_event,
                "head_sha": run.get("head_sha") == expected_head_sha,
                "run_attempt": int(run.get("run_attempt") or 0)
                == int(expected_run_attempt),
                "status": run.get("status") == "completed",
                "conclusion": run.get("conclusion") == "success",
            }
            if not all(checks.values()):
                return {"verified": False, "reason": f"workflow_mismatch:{checks}"}
            return {"verified": True, "run": run}
        except (GitHubEvidenceError, TypeError, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}

    def verify_pr(
        self,
        *,
        pr_number: int,
        expected_head_sha: str,
        expected_base_sha: str,
        expected_merge_commit_sha: str | None = None,
        require_merged: bool | None = None,
    ) -> dict[str, Any]:
        try:
            pr = self._request_json(
                f"/repos/{self.repository}/pulls/{int(pr_number)}"
            )
            base = pr.get("base") or {}
            head = pr.get("head") or {}
            base_repository = base.get("repo") or {}
            checks = {
                "repository": base_repository.get("full_name") == self.repository,
                "head": head.get("sha") == expected_head_sha,
                "base": base.get("sha") == expected_base_sha,
            }
            if expected_merge_commit_sha is not None:
                checks["merge_commit"] = (
                    pr.get("merge_commit_sha") == expected_merge_commit_sha
                )
            if require_merged is not None:
                checks["merged"] = bool(pr.get("merged")) is require_merged
            if not all(checks.values()):
                return {"verified": False, "reason": f"pr_mismatch:{checks}"}
            return {"verified": True, "pr": pr}
        except (GitHubEvidenceError, TypeError, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}

    def verify_issue_comment(
        self,
        *,
        comment_id: int,
        expected_issue: int,
        allowed_authors: tuple[str, ...],
        expected_body_sha256: str,
        required_text: tuple[str, ...],
    ) -> dict[str, Any]:
        try:
            comment = self._request_json(
                f"/repos/{self.repository}/issues/comments/{int(comment_id)}"
            )
            body = str(comment.get("body") or "")
            issue_suffix = f"/issues/{int(expected_issue)}"
            checks = {
                "issue": str(comment.get("issue_url") or "").endswith(issue_suffix),
                "author": str((comment.get("user") or {}).get("login") or "")
                in allowed_authors,
                "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()
                == expected_body_sha256,
                "bindings": all(value in body for value in required_text),
            }
            if not all(checks.values()):
                return {"verified": False, "reason": f"comment_mismatch:{checks}"}
            return {"verified": True, "comment": comment}
        except (GitHubEvidenceError, TypeError, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}

    def verify_ref_file_sha256(
        self, *, ref: str, path: str, expected_sha256: str,
    ) -> dict[str, Any]:
        """Compare a pinned regular Git file to an independently supplied digest."""
        if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            return {"verified": False, "reason": "invalid_expected_sha256"}
        result = self.load_ref_file_bytes(ref=ref, path=path)
        if not result["verified"]:
            return result
        observed = hashlib.sha256(result["bytes"]).hexdigest()
        if observed != expected_sha256:
            return {"verified": False, "reason": f"content_digest_mismatch:{observed}"}
        return {
            "verified": True, "sha256": observed,
            "source_identity": result["source_identity"],
        }

    def load_merge_attestation(
        self,
        *,
        pr_number: int,
        expected_head_sha: str,
    ) -> dict[str, Any]:
        """Load exactly one matching external attestation from PR comments."""

        try:
            comments = self._request_json(
                f"/repos/{self.repository}/issues/{int(pr_number)}/comments?per_page=100"
            )
            matches: list[dict[str, Any]] = []
            pattern = re.compile(
                r"```json\s+mainline_merge_approval_attestation\s*\n"
                r"(?P<payload>\{.*?\})\s*\n```",
                re.DOTALL,
            )
            for comment in comments if isinstance(comments, list) else []:
                body = str(comment.get("body") or "")
                if "MAINLINE_MERGE_APPROVAL_ATTESTATION" not in body:
                    continue
                match = pattern.search(body)
                if not match:
                    continue
                payload = json.loads(match.group("payload"))
                if (
                    payload.get("source_pr") == int(pr_number)
                    and payload.get("accepted_exact_head_sha") == expected_head_sha
                    and payload.get("authorization_status") == "active"
                ):
                    payload["_remote_comment_id"] = int(comment.get("id") or 0)
                    payload["_remote_author"] = str(
                        (comment.get("user") or {}).get("login") or ""
                    )
                    payload["_remote_comment_created_at"] = str(
                        comment.get("created_at") or ""
                    )
                    payload["_remote_comment_updated_at"] = str(
                        comment.get("updated_at") or ""
                    )
                    matches.append(payload)
            if len(matches) != 1:
                raise GitHubEvidenceError(
                    f"expected_one_active_attestation:observed={len(matches)}"
                )
            return matches[0]
        except (GitHubEvidenceError, json.JSONDecodeError, TypeError, ValueError) as exc:
            if isinstance(exc, GitHubEvidenceError):
                raise
            raise GitHubEvidenceError(f"invalid_attestation_comment:{type(exc).__name__}") from exc

    # ------------------------------------------------------------------
    # False/none (no-legacy-intent) post-merge landing evidence (Issue #156)
    # ------------------------------------------------------------------

    def resolve_merged_pull_request(self, *, merge_commit_sha: str) -> dict[str, Any]:
        """Resolve exactly one associated PR for an exact merge commit.

        This is deterministic identity resolution only: the commit-associated
        pull-request list endpoint never returns a ``merged`` boolean key, so
        merged-state truth is intentionally NOT asserted here.  Resolution
        fails closed on ambiguity, malformed payloads, repository mismatch,
        a missing ``merged_at``, a non-matching ``merge_commit_sha``, or an
        open PR; the authoritative merged-state verification remains the
        caller's full ``verify_pr(..., require_merged=True)`` check.
        """

        try:
            pulls = self._request_json(
                f"/repos/{self.repository}/commits/{merge_commit_sha}/pulls?per_page=100"
            )
            if not isinstance(pulls, list) or len(pulls) != 1:
                observed = len(pulls) if isinstance(pulls, list) else "invalid"
                raise GitHubEvidenceError(f"expected_one_merged_pr:observed={observed}")
            pr = pulls[0]
            if not isinstance(pr, dict) or not isinstance(pr.get("number"), int):
                raise GitHubEvidenceError("resolved_pr_shape_invalid")
            reflected = str(((pr.get("base") or {}).get("repo") or {}).get("full_name") or "")
            if reflected != self.repository:
                raise GitHubEvidenceError(
                    f"resolved_pr_repository_mismatch:{reflected}"
                )
            if not str(pr.get("merged_at") or ""):
                raise GitHubEvidenceError("resolved_pr_missing_merged_at")
            if str(pr.get("merge_commit_sha") or "") != merge_commit_sha:
                raise GitHubEvidenceError(
                    f"resolved_pr_merge_commit_mismatch:observed={pr.get('merge_commit_sha')}"
                )
            if str(pr.get("state") or "") != "closed":
                raise GitHubEvidenceError(
                    f"resolved_pr_not_closed:observed={pr.get('state')}"
                )
            return pr
        except (GitHubEvidenceError, TypeError, ValueError) as exc:
            raise GitHubEvidenceError(f"resolve_merged_pr_failed:{exc}") from exc

    def load_owner_landing_merge_attestations(
        self, *, pr_number: int
    ) -> list[dict[str, Any]]:
        """Return every OWNER_LANDING_MERGE_ATTESTATION payload on a PR.

        Runtime identity fields are always appended from the live GitHub
        comment and never trusted from user-written payload bytes.  Duplicate
        or later-timestamp validation is the caller's responsibility so that
        every active-matching candidate can be counted deterministically.
        """

        try:
            comments = self._request_json(
                f"/repos/{self.repository}/issues/{int(pr_number)}/comments?per_page=100"
            )
        except GitHubEvidenceError as exc:
            raise GitHubEvidenceError(
                f"load_owner_landing_attestation_failed:{exc}"
            ) from exc
        pattern = re.compile(
            r"```json\s+owner_landing_merge_attestation\s*\n"
            r"(?P<payload>\{.*?\})\s*\n```",
            re.DOTALL,
        )
        matches: list[dict[str, Any]] = []
        for comment in comments if isinstance(comments, list) else []:
            body = str(comment.get("body") or "")
            if OWNER_LANDING_ATTESTATION_MARKER not in body:
                continue
            match = pattern.search(body)
            if not match:
                continue
            try:
                payload = json.loads(match.group("payload"))
            except json.JSONDecodeError as exc:
                raise GitHubEvidenceError("invalid_owner_landing_attestation_json") from exc
            if not isinstance(payload, dict):
                raise GitHubEvidenceError("invalid_owner_landing_attestation_shape")
            payload["_remote_comment_id"] = int(comment.get("id") or 0)
            payload["_remote_author"] = str(
                (comment.get("user") or {}).get("login") or ""
            )
            payload["_remote_comment_created_at"] = str(
                comment.get("created_at") or ""
            )
            payload["_remote_comment_updated_at"] = str(
                comment.get("updated_at") or ""
            )
            payload["_remote_comment_body"] = body
            matches.append(payload)
        return matches

    def verify_pull_request_review(
        self,
        *,
        review_id: int,
        pr_number: int,
        allowed_authors: tuple[str, ...],
        expected_commit_sha: str,
    ) -> dict[str, Any]:
        try:
            review = self._request_json(
                f"/repos/{self.repository}/pulls/{int(pr_number)}/reviews/{int(review_id)}"
            )
        except (GitHubEvidenceError, TypeError, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}
        checks = {
            "pull_request": str(review.get("pull_request_url") or "").endswith(
                f"/pulls/{int(pr_number)}"
            ),
            "author": str((review.get("user") or {}).get("login") or "")
            in allowed_authors,
            "commit_id": str(review.get("commit_id") or "") == expected_commit_sha,
        }
        if not all(checks.values()):
            return {"verified": False, "reason": f"review_mismatch:{checks}"}
        return {"verified": True, "review": review}

    def verify_check_run_contexts(
        self,
        *,
        head_sha: str,
        required_contexts: tuple[str, ...] | list[str],
    ) -> dict[str, Any]:
        """Verify exact required status-check contexts on one exact head.

        Only exact-name completed success runs satisfy a required context.  A
        Draft ``landing-state-gate-draft-inert`` run never satisfies the formal
        ``landing-state-gate`` context because the names differ.
        """

        try:
            payload = self._request_json(
                f"/repos/{self.repository}/commits/{head_sha}/check-runs?per_page=100"
            )
        except (GitHubEvidenceError, TypeError, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}
        runs = payload.get("check_runs") if isinstance(payload, dict) else []
        if not isinstance(runs, list):
            return {"verified": False, "reason": "invalid_check_runs_payload"}
        by_name: dict[str, dict[str, bool]] = {}
        for run in runs:
            if not isinstance(run, dict):
                continue
            name = str(run.get("name") or "")
            if not name:
                continue
            entry = by_name.setdefault(name, {"completed": False, "success": False})
            if str(run.get("status") or "") == "completed":
                entry["completed"] = True
                if str(run.get("conclusion") or "") == "success":
                    entry["success"] = True
        contexts: dict[str, bool] = {}
        for required in required_contexts:
            entry = by_name.get(str(required))
            contexts[str(required)] = bool(entry and entry.get("success"))
        if not all(contexts.values()):
            missing = [name for name, ok in contexts.items() if not ok]
            return {
                "verified": False,
                "reason": f"check_contexts_missing:{missing}",
                "contexts": contexts,
                "check_runs": runs,
            }
        return {"verified": True, "contexts": contexts, "check_runs": runs}

    def verify_repository_ruleset(
        self,
        *,
        ruleset_id: int,
        required_status_contexts: tuple[str, ...] | list[str],
        allowed_merge_methods: tuple[str, ...] | list[str],
    ) -> dict[str, Any]:
        """Verify the live repository Ruleset agrees with the attested policy.

        The attested Ruleset id must exist, be active, and require exactly the
        same status-check contexts and the exact ``merge`` pull-request merge
        method declared by the landing authority.  No comment text is trusted.
        """

        try:
            ruleset = self._request_json(
                f"/repos/{self.repository}/rulesets/{int(ruleset_id)}"
            )
        except (GitHubEvidenceError, TypeError, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}
        checks = {
            "id": int(ruleset.get("id") or 0) == int(ruleset_id),
            "enforcement": ruleset.get("enforcement") == "active",
            "source_type": ruleset.get("source_type") == "Repository",
        }
        rules = ruleset.get("rules") if isinstance(ruleset.get("rules"), list) else []
        status_checks_rule: Any = None
        pull_request_rule: Any = None
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            if rule.get("type") == "required_status_checks":
                status_checks_rule = rule
            if rule.get("type") == "pull_request":
                pull_request_rule = rule
        if isinstance(status_checks_rule, dict):
            params = status_checks_rule.get("parameters")
            params = params if isinstance(params, dict) else {}
            contexts_raw = params.get("required_status_checks")
            contexts: list[str] = []
            if isinstance(contexts_raw, list):
                for item in contexts_raw:
                    if isinstance(item, dict) and isinstance(item.get("context"), str):
                        contexts.append(item.get("context"))
            expected = set(str(context) for context in required_status_contexts)
            checks["status_checks"] = set(contexts) == expected
        else:
            checks["status_checks"] = False
        if isinstance(pull_request_rule, dict):
            params = pull_request_rule.get("parameters")
            params = params if isinstance(params, dict) else {}
            methods = params.get("allowed_merge_methods")
            expected = set(str(method) for method in allowed_merge_methods)
            checks["merge_methods"] = (
                isinstance(methods, list)
                and len(methods) > 0
                and set(methods) == expected
            )
        else:
            checks["merge_methods"] = False
        if not all(checks.values()):
            return {"verified": False, "reason": f"ruleset_mismatch:{checks}"}
        return {"verified": True, "ruleset": ruleset}

    def load_ref_file_bytes(self, *, ref: str, path: str) -> dict[str, Any]:
        """Read a regular file through a pinned commit/tree/blob chain.

        The authenticated GitHub commit-to-root linkage and the caller's prior
        approval of that commit are trusted inputs. No candidate code executes.
        Object integrity is not proof of workflow execution or source approval.
        """
        try:
            return self._load_exact_git_file(ref=ref, path=path)
        except (GitHubEvidenceError, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}

    def _load_exact_git_file(self, *, ref: str, path: str) -> dict[str, Any]:
        if not isinstance(ref, str) or not re.fullmatch(r"[0-9a-f]{40}", ref):
            raise GitHubEvidenceError("immutable_commit_required")
        if not isinstance(self.repository, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9-]{0,99}/[A-Za-z0-9_.-]{1,100}", self.repository
        ) or self.repository.split("/")[-1] in {".", ".."}:
            raise GitHubEvidenceError("invalid_repository_identity")
        if not isinstance(path, str) or not path or len(path) > 4096:
            raise GitHubEvidenceError("invalid_source_path")
        parts = path.split("/")
        if len(parts) > 32 or any(not _source_component(part) for part in parts):
            raise GitHubEvidenceError("invalid_source_path")
        # Paths are matched as data in trees, never interpolated into URLs.
        prefix = f"/repos/{self.repository}/git"
        commit = self._request_json(f"{prefix}/commits/{ref}")
        if not isinstance(commit, dict) or commit.get("sha") != ref:
            raise GitHubEvidenceError("commit_identity_mismatch")
        root = commit.get("tree")
        if not isinstance(root, dict) or not _source_oid(root.get("sha")):
            raise GitHubEvidenceError("invalid_commit_tree")
        root_sha = tree_sha = root["sha"]
        tree_chain: list[str] = []
        for index, component in enumerate(parts):
            tree = self._request_json(f"{prefix}/trees/{tree_sha}")
            entries = _verified_source_tree(tree, tree_sha)
            tree_chain.append(tree_sha)
            entry = entries.get(component)
            if entry is None:
                raise GitHubEvidenceError("source_path_missing")
            final = index == len(parts) - 1
            if not final:
                if entry["mode"] != "040000" or entry["type"] != "tree":
                    raise GitHubEvidenceError("source_component_not_tree")
                tree_sha = entry["sha"]
                continue
            if entry["mode"] not in {"100644", "100755"} or entry["type"] != "blob":
                raise GitHubEvidenceError("source_not_regular_file")
            size = entry.get("size")
            if type(size) is not int or not 0 <= size <= 1024 * 1024:
                raise GitHubEvidenceError("invalid_source_size")
            blob_sha = entry["sha"]
            blob = self._request_json(f"{prefix}/blobs/{blob_sha}")
            if not isinstance(blob, dict) or blob.get("sha") != blob_sha:
                raise GitHubEvidenceError("blob_identity_mismatch")
            if blob.get("encoding") != "base64":
                raise GitHubEvidenceError("unexpected_content_encoding")
            content = blob.get("content")
            if not isinstance(content, str):
                raise GitHubEvidenceError("invalid_content_type")
            # Bounded processing AFTER the existing transport has decoded JSON.
            if len(content) > 2 * 1024 * 1024:
                raise GitHubEvidenceError("source_encoding_too_large")
            raw = _decode_github_contents_base64(content)
            normalized = content.translate(str.maketrans("", "", " \t\r\n"))
            if base64.b64encode(raw).decode("ascii") != normalized:
                raise GitHubEvidenceError("invalid_base64_content")
            if type(blob.get("size")) is not int or blob["size"] != size or len(raw) != size:
                raise GitHubEvidenceError("source_size_mismatch")
            if _source_object_oid("blob", raw) != blob_sha:
                raise GitHubEvidenceError("source_blob_digest_mismatch")
            return {
                "verified": True, "bytes": raw,
                "source_identity": {
                    "repository": self.repository, "commit_sha": commit["sha"],
                    "root_tree_sha": root_sha, "tree_chain": tree_chain,
                    "path": path, "blob_sha": blob_sha, "mode": entry["mode"],
                    "size": size,
                },
            }
        raise GitHubEvidenceError("source_path_missing")
