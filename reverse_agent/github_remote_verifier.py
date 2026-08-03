"""Fail-closed GitHub evidence verifier for mainline landing validation.

The production implementation uses only read-only GitHub REST endpoints.  It
never accepts locally asserted workflow, pull-request, approval, or authority
facts as remote evidence.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
import os
import re
import urllib.error
import urllib.request
import zipfile
from typing import Any


class GitHubEvidenceError(RuntimeError):
    """Raised when trusted GitHub evidence cannot be obtained or verified."""


def _decode_github_contents_base64(content: str) -> bytes:
    normalized = content.translate(str.maketrans("", "", " \t\r\n"))
    try:
        return base64.b64decode(normalized, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("invalid_base64_content") from exc


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
            content = payload.get("content")
            if not isinstance(content, str):
                return {"verified": False, "reason": "invalid_content_type"}
            raw = _decode_github_contents_base64(content)
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

    # ------------------------------------------------------------------
    # State Gate Receipt verification (pull_request_target)
    # ------------------------------------------------------------------

    _RECEIPT_REQUIRED_FIELDS = frozenset({
        "schema_version",
        "receipt_kind",
        "repository",
        "pr_number",
        "workflow_path",
        "workflow_event",
        "workflow_run_id",
        "workflow_run_attempt",
        "trusted_base_sha",
        "trusted_verifier_tree_sha",
        "candidate_head_sha",
        "candidate_base_sha",
        "changed_paths_sha256",
        "selected_mode",
        "authority_identity",
        "authority_revision",
        "authority_result",
        "candidate_tests_result",
        "final_gate_result",
        "generated_at",
        "content_sha256",
    })

    def _list_run_artifacts(self, run_id: int) -> list[dict[str, Any]]:
        """List artifacts for a workflow run."""

        payload = self._request_json(
            f"/repos/{self.repository}/actions/runs/{int(run_id)}/artifacts?per_page=100"
        )
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list):
            raise GitHubEvidenceError("invalid_artifacts_response")
        return artifacts

    def _download_artifact_json(self, artifact_id: int) -> dict[str, Any]:
        """Download a workflow artifact (ZIP) and extract the first JSON file."""

        url = f"{self.api_url}/repos/{self.repository}/actions/artifacts/{int(artifact_id)}/zip"
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "reverse-agent-mainline-validator",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if response.status != 200:
                    raise GitHubEvidenceError(f"artifact_http_status:{response.status}")
                zip_bytes = response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise GitHubEvidenceError(f"artifact_download_failed:{type(exc).__name__}") from exc
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
                names = archive.namelist()
                json_names = [n for n in names if n.endswith(".json")]
                if len(json_names) != 1:
                    raise GitHubEvidenceError(
                        f"expected_one_json_in_artifact:observed={len(json_names)}"
                    )
                raw = archive.read(json_names[0])
                payload = json.loads(raw.decode("utf-8"))
        except (zipfile.BadZipFile, json.JSONDecodeError, OSError) as exc:
            raise GitHubEvidenceError(f"artifact_extract_failed:{type(exc).__name__}") from exc
        if not isinstance(payload, dict):
            raise GitHubEvidenceError("artifact_json_not_object")
        return payload

    @staticmethod
    def _compute_receipt_digest(receipt: dict[str, Any]) -> str:
        """Compute the canonical content_sha256 of a receipt (minus content_sha256)."""

        filtered = {
            k: v for k, v in receipt.items() if k != "content_sha256"
        }
        canonical = json.dumps(
            filtered, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def verify_state_gate_receipt(
        self,
        *,
        run_id: int,
        expected_repository: str,
        expected_workflow_path: str,
        expected_event: str,
        expected_run_attempt: int = 1,
        trusted_base_sha: str,
        accepted_candidate_head: str,
        locked_base_sha: str,
        expected_pr_number: int,
    ) -> dict[str, Any]:
        """Verify a State Gate workflow run and its receipt artifact.

        For ``pull_request_target`` events, the run's ``head_sha`` is the
        base-context head (NOT the candidate head).  The candidate head SHA
        is only verified via the receipt artifact.

        Fails closed on any missing, duplicate, expired, or mismatched field.
        """

        try:
            # 1. Verify the workflow run itself
            run = self._request_json(
                f"/repos/{self.repository}/actions/runs/{int(run_id)}"
            )
            observed_repository = str(
                ((run.get("repository") or {}).get("full_name")) or ""
            )
            run_checks = {
                "repository": observed_repository == expected_repository,
                "path": run.get("path") == expected_workflow_path,
                "event": run.get("event") == expected_event,
                "run_id": int(run.get("id") or 0) == int(run_id),
                "run_attempt": int(run.get("run_attempt") or 0)
                == int(expected_run_attempt),
                "status": run.get("status") == "completed",
                "conclusion": run.get("conclusion") == "success",
            }
            # For pull_request_target, run.head_sha is the base context head,
            # NOT the candidate head.  Verify it matches the trusted base SHA.
            if expected_event == "pull_request_target":
                run_checks["trusted_base_sha"] = (
                    run.get("head_sha") == trusted_base_sha
                )
            else:
                run_checks["head_sha"] = run.get("head_sha") == accepted_candidate_head

            if not all(run_checks.values()):
                return {
                    "verified": False,
                    "reason": f"run_mismatch:{run_checks}",
                }

            # 2. List artifacts and find exactly one matching receipt
            artifacts = self._list_run_artifacts(run_id)
            expected_prefix = f"state-gate-receipt-pr{int(expected_pr_number)}-"
            matching = [
                a for a in artifacts
                if isinstance(a, dict)
                and str(a.get("name", "")).startswith(expected_prefix)
                and str(a.get("name", "")).endswith(f"-{accepted_candidate_head}")
            ]
            if len(matching) == 0:
                return {
                    "verified": False,
                    "reason": "receipt_artifact_missing",
                }
            if len(matching) > 1:
                return {
                    "verified": False,
                    "reason": f"receipt_artifact_duplicate:count={len(matching)}",
                }

            # 3. Download and parse the receipt
            artifact_id = int(matching[0].get("id") or 0)
            receipt = self._download_artifact_json(artifact_id)

            # 4. Verify receipt fields
            receipt_keys = set(receipt.keys())
            missing_fields = self._RECEIPT_REQUIRED_FIELDS - receipt_keys
            extra_fields = receipt_keys - self._RECEIPT_REQUIRED_FIELDS
            if missing_fields or extra_fields:
                return {
                    "verified": False,
                    "reason": f"receipt_field_mismatch:"
                    f"missing={sorted(missing_fields)}"
                    f"extra={sorted(extra_fields)}",
                }

            receipt_checks = {
                "repository": receipt.get("repository") == expected_repository,
                "pr_number": int(receipt.get("pr_number") or 0)
                == int(expected_pr_number),
                "workflow_path": receipt.get("workflow_path")
                == expected_workflow_path,
                "workflow_event": receipt.get("workflow_event") == expected_event,
                "workflow_run_id": int(receipt.get("workflow_run_id") or 0)
                == int(run_id),
                "workflow_run_attempt": int(receipt.get("workflow_run_attempt") or 0)
                == int(expected_run_attempt),
                "candidate_head_sha": receipt.get("candidate_head_sha")
                == accepted_candidate_head,
                "candidate_base_sha": receipt.get("candidate_base_sha")
                == locked_base_sha,
                "trusted_base_sha": receipt.get("trusted_base_sha")
                == trusted_base_sha,
                "final_gate_result": receipt.get("final_gate_result") == "PASS",
                "authority_result": receipt.get("authority_result") == "SUCCESS",
                "candidate_tests_result": receipt.get("candidate_tests_result")
                == "SUCCESS",
                "selected_mode_supported": receipt.get("selected_mode")
                in {"transition", "path_a_r1", "legacy"},
                "changed_paths_sha256_format": bool(
                    re.fullmatch(
                        r"[0-9a-f]{64}",
                        str(receipt.get("changed_paths_sha256") or ""),
                    )
                ),
                "trusted_verifier_tree_sha_matches_base": receipt.get(
                    "trusted_verifier_tree_sha"
                )
                == trusted_base_sha,
                "authority_identity_exact": receipt.get("authority_identity")
                == "trusted_base_verifier",
                "authority_revision_nonempty": bool(
                    str(receipt.get("authority_revision") or "").strip()
                ),
            }

            # 5. Verify receipt content digest
            expected_digest = self._compute_receipt_digest(receipt)
            receipt_checks["content_sha256"] = (
                receipt.get("content_sha256") == expected_digest
            )

            if not all(receipt_checks.values()):
                return {
                    "verified": False,
                    "reason": f"receipt_mismatch:{receipt_checks}",
                }

            return {"verified": True, "run": run, "receipt": receipt}
        except (GitHubEvidenceError, TypeError, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}
