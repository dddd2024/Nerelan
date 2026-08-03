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


# ---------------------------------------------------------------------------
# Shared network-free State Gate receipt payload validator
#
# This single deterministic function is reused by:
#   - the workflow-facing CLI/helper (verify-state-gate-receipt)
#   - GitHubRemoteAcceptanceVerifier.verify_state_gate_receipt()
#
# It performs NO network access.  It fails closed on any field missing,
# extra, or mismatched.
# ---------------------------------------------------------------------------

STATE_GATE_RECEIPT_REQUIRED_FIELDS = frozenset({
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

SUPPORTED_SELECTED_MODES = frozenset({"transition", "path_a_r1", "legacy"})

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class StateGateReceiptValidationError(RuntimeError):
    """Raised when a State Gate receipt payload fails validation."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = list(errors)
        super().__init__(";".join(self.errors))


def compute_state_gate_receipt_digest(receipt: dict[str, Any]) -> str:
    """Compute the canonical content_sha256 of a receipt (excluding content_sha256)."""

    filtered = {k: v for k, v in receipt.items() if k != "content_sha256"}
    canonical = json.dumps(
        filtered, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_state_gate_receipt_payload(
    receipt: dict[str, Any],
    *,
    expected_repository: str,
    expected_pr_number: int,
    expected_workflow_path: str,
    expected_workflow_event: str,
    expected_run_id: int,
    expected_run_attempt: int,
    expected_trusted_base_sha: str,
    expected_candidate_base_sha: str,
    expected_candidate_head_sha: str,
    expected_changed_paths_sha256: str,
    supported_modes: frozenset[str] = SUPPORTED_SELECTED_MODES,
) -> None:
    """Validate a State Gate receipt payload against expected bindings.

    This function is network-free and deterministic.  It raises
    ``StateGateReceiptValidationError`` on any mismatch, missing field, extra
    field, or invalid content digest.  It returns ``None`` on success.
    """

    errors: list[str] = []

    if not isinstance(receipt, dict):
        raise StateGateReceiptValidationError(["receipt_not_object"])

    # 1. Exact field set
    receipt_keys = set(receipt.keys())
    missing = STATE_GATE_RECEIPT_REQUIRED_FIELDS - receipt_keys
    extra = receipt_keys - STATE_GATE_RECEIPT_REQUIRED_FIELDS
    if missing:
        errors.append(f"missing_fields={sorted(missing)}")
    if extra:
        errors.append(f"extra_fields={sorted(extra)}")

    # 2. schema_version and receipt_kind
    if receipt.get("schema_version") != "0.1":
        errors.append(f"schema_version={receipt.get('schema_version')!r} (expected '0.1')")
    if receipt.get("receipt_kind") != "state_gate":
        errors.append(f"receipt_kind={receipt.get('receipt_kind')!r} (expected 'state_gate')")

    # 3. repository
    if receipt.get("repository") != expected_repository:
        errors.append(f"repository={receipt.get('repository')!r} (expected {expected_repository!r})")

    # 4. pr_number
    try:
        if int(receipt.get("pr_number") or 0) != int(expected_pr_number):
            errors.append(f"pr_number={receipt.get('pr_number')!r} (expected {expected_pr_number!r})")
    except (TypeError, ValueError):
        errors.append(f"pr_number={receipt.get('pr_number')!r} (not int)")

    # 5. workflow_path
    if receipt.get("workflow_path") != expected_workflow_path:
        errors.append(f"workflow_path={receipt.get('workflow_path')!r} (expected {expected_workflow_path!r})")

    # 6. workflow_event
    if receipt.get("workflow_event") != expected_workflow_event:
        errors.append(f"workflow_event={receipt.get('workflow_event')!r} (expected {expected_workflow_event!r})")

    # 7. workflow_run_id
    try:
        if int(receipt.get("workflow_run_id") or 0) != int(expected_run_id):
            errors.append(f"workflow_run_id={receipt.get('workflow_run_id')!r} (expected {expected_run_id!r})")
    except (TypeError, ValueError):
        errors.append(f"workflow_run_id={receipt.get('workflow_run_id')!r} (not int)")

    # 8. workflow_run_attempt
    try:
        if int(receipt.get("workflow_run_attempt") or 0) != int(expected_run_attempt):
            errors.append(f"workflow_run_attempt={receipt.get('workflow_run_attempt')!r} (expected {expected_run_attempt!r})")
    except (TypeError, ValueError):
        errors.append(f"workflow_run_attempt={receipt.get('workflow_run_attempt')!r} (not int)")

    # 9. trusted_base_sha
    if receipt.get("trusted_base_sha") != expected_trusted_base_sha:
        errors.append(f"trusted_base_sha={receipt.get('trusted_base_sha')!r} (expected {expected_trusted_base_sha!r})")

    # 10. trusted_verifier_tree_sha == trusted_base_sha
    trusted_base = receipt.get("trusted_base_sha", "")
    if receipt.get("trusted_verifier_tree_sha") != trusted_base:
        errors.append(f"trusted_verifier_tree_sha={receipt.get('trusted_verifier_tree_sha')!r} (expected {trusted_base!r})")

    # 11. authority_revision == trusted_base_sha
    if receipt.get("authority_revision") != trusted_base:
        errors.append(f"authority_revision={receipt.get('authority_revision')!r} (expected {trusted_base!r})")

    # 12. candidate_base_sha
    if receipt.get("candidate_base_sha") != expected_candidate_base_sha:
        errors.append(f"candidate_base_sha={receipt.get('candidate_base_sha')!r} (expected {expected_candidate_base_sha!r})")

    # 13. candidate_head_sha
    if receipt.get("candidate_head_sha") != expected_candidate_head_sha:
        errors.append(f"candidate_head_sha={receipt.get('candidate_head_sha')!r} (expected {expected_candidate_head_sha!r})")

    # 14. changed_paths_sha256 == expected (exact equality, not format-only)
    changed_paths = receipt.get("changed_paths_sha256", "")
    if changed_paths != expected_changed_paths_sha256:
        errors.append(f"changed_paths_sha256={changed_paths!r} (expected {expected_changed_paths_sha256!r})")

    # 15. selected_mode in supported set
    selected_mode = receipt.get("selected_mode", "")
    if selected_mode not in supported_modes:
        errors.append(f"unsupported selected_mode={selected_mode!r}")

    # 16. authority_identity == trusted_base_verifier
    if receipt.get("authority_identity") != "trusted_base_verifier":
        errors.append(f"authority_identity={receipt.get('authority_identity')!r} (expected 'trusted_base_verifier')")

    # 17. authority_result == SUCCESS
    if receipt.get("authority_result") != "SUCCESS":
        errors.append(f"authority_result={receipt.get('authority_result')!r} (expected 'SUCCESS')")

    # 18. candidate_tests_result == SUCCESS
    if receipt.get("candidate_tests_result") != "SUCCESS":
        errors.append(f"candidate_tests_result={receipt.get('candidate_tests_result')!r} (expected 'SUCCESS')")

    # 19. final_gate_result == PASS
    if receipt.get("final_gate_result") != "PASS":
        errors.append(f"final_gate_result={receipt.get('final_gate_result')!r} (expected 'PASS')")

    # 20. content_sha256 == canonical recomputation
    expected_digest = compute_state_gate_receipt_digest(receipt)
    if receipt.get("content_sha256") != expected_digest:
        errors.append(f"content_sha256={receipt.get('content_sha256')!r} (expected {expected_digest!r})")

    if errors:
        raise StateGateReceiptValidationError(errors)


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

    _RECEIPT_REQUIRED_FIELDS = STATE_GATE_RECEIPT_REQUIRED_FIELDS

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
        """Compute the canonical content_sha256 of a receipt (minus content_sha256).

        Delegates to the shared module-level function so there is exactly one
        digest computation implementation.
        """

        return compute_state_gate_receipt_digest(receipt)

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
        expected_changed_paths_sha256: str,
    ) -> dict[str, Any]:
        """Verify a State Gate workflow run and its receipt artifact.

        For ``pull_request_target`` events, the run's ``head_sha`` is the
        base-context head (NOT the candidate head).  The candidate head SHA
        is only verified via the receipt artifact.

        After remote run/artifact observation, this method delegates receipt
        payload validation to the shared
        ``validate_state_gate_receipt_payload`` function so that both the
        workflow-facing CLI and the remote verifier enforce identical
        semantics.

        ``expected_changed_paths_sha256`` is MANDATORY for production use.
        The receipt's own ``changed_paths_sha256`` is NOT used as a fallback
        expected digest — that would be self-trust, not independent binding.

        Fails closed on any missing, duplicate, expired, or mismatched field.
        """

        if not expected_changed_paths_sha256:
            return {
                "verified": False,
                "reason": "expected_changed_paths_sha256_required",
            }

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

            # 4. Validate receipt payload via the shared network-free validator.
            # The expected changed-path digest is mandatory and supplied by
            # the caller — the receipt's own digest is NOT used as a fallback.
            try:
                validate_state_gate_receipt_payload(
                    receipt,
                    expected_repository=expected_repository,
                    expected_pr_number=expected_pr_number,
                    expected_workflow_path=expected_workflow_path,
                    expected_workflow_event=expected_event,
                    expected_run_id=run_id,
                    expected_run_attempt=expected_run_attempt,
                    expected_trusted_base_sha=trusted_base_sha,
                    expected_candidate_base_sha=locked_base_sha,
                    expected_candidate_head_sha=accepted_candidate_head,
                    expected_changed_paths_sha256=expected_changed_paths_sha256,
                )
            except StateGateReceiptValidationError as exc:
                return {
                    "verified": False,
                    "reason": f"receipt_mismatch:{exc.errors}",
                }

            return {"verified": True, "run": run, "receipt": receipt}
        except (GitHubEvidenceError, TypeError, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}
