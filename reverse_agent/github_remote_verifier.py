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


class GitHubEvidenceError(RuntimeError):
    """Raised when trusted GitHub evidence cannot be obtained or verified."""


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
        self,
        *,
        ref: str,
        path: str,
        expected_sha256: str,
    ) -> dict[str, Any]:
        try:
            payload = self._request_json(
                f"/repos/{self.repository}/contents/{path}?ref={ref}"
            )
            if payload.get("encoding") != "base64":
                return {"verified": False, "reason": "unexpected_content_encoding"}
            raw = base64.b64decode(str(payload.get("content") or ""), validate=True)
            observed = hashlib.sha256(raw).hexdigest()
            if observed != expected_sha256:
                return {
                    "verified": False,
                    "reason": f"content_digest_mismatch:{observed}",
                }
            return {"verified": True, "sha256": observed}
        except (
            GitHubEvidenceError,
            TypeError,
            ValueError,
            binascii.Error,
        ) as exc:
            return {"verified": False, "reason": str(exc)}

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
