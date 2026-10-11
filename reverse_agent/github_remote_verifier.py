"""Fail-closed GitHub evidence verifier for mainline landing validation.

The production implementation uses only read-only GitHub REST endpoints.  It
never accepts locally asserted workflow, pull-request, approval, or authority
facts as remote evidence.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import http.client
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Callable


OWNER_LANDING_ATTESTATION_MARKER = "OWNER_LANDING_MERGE_ATTESTATION"
OWNER_LANDING_ATTESTATION_BLOCK = "owner_landing_merge_attestation"
READY_ATTESTATION_WAIT_SECONDS = 180
READY_ATTESTATION_MAX_POLLS = 18
READY_ATTESTATION_POLL_SECONDS = 10
_READY_COMMENTS_MAX_BYTES = 2 * 1024 * 1024


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

    def _request_json(
        self, path: str, *, timeout: float = 30,
        deadline: float | None = None, clock: Callable[[], float] = time.monotonic,
    ) -> Any:
        if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                or not math.isfinite(timeout) or not 0 < timeout <= 30):
            raise GitHubEvidenceError("github_request_timeout_invalid")
        if deadline is not None:
            if (isinstance(deadline, bool) or not isinstance(deadline, (int, float))
                    or not math.isfinite(deadline)):
                raise GitHubEvidenceError("github_request_deadline_invalid")
            remaining = deadline - clock()
            if remaining <= 0:
                raise GitHubEvidenceError("ready_attestation_wait_timeout")
            timeout = min(timeout, remaining)
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
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise GitHubEvidenceError(f"github_http_status:{response.status}")
                if deadline is None:
                    raw = response.read()
                else:
                    # Readiness-only deadline and body bound. urllib timeouts
                    # are per blocking phase, not a whole-request wall clock;
                    # the workflow step also has a hard three-minute timeout.
                    chunks: list[bytes] = []
                    size = 0
                    while True:
                        remaining = deadline - clock()
                        if remaining <= 0:
                            raise GitHubEvidenceError("ready_attestation_wait_timeout")
                        if callable(getattr(response, "isclosed", None)) and response.isclosed():
                            if getattr(response, "length", None) not in (None, 0):
                                raise GitHubEvidenceError("ready_comments_response_incomplete")
                            break
                        sock = getattr(getattr(getattr(response, "fp", None), "raw", None), "_sock", None)
                        if sock is None or not callable(getattr(response, "read1", None)):
                            raise GitHubEvidenceError("ready_comments_deadline_transport_unsupported")
                        sock.settimeout(min(timeout, remaining))
                        chunk = response.read1(65536)
                        if not chunk:
                            if getattr(response, "length", None) not in (None, 0):
                                raise GitHubEvidenceError("ready_comments_response_incomplete")
                            break
                        size += len(chunk)
                        if size > _READY_COMMENTS_MAX_BYTES:
                            raise GitHubEvidenceError("ready_comments_response_too_large")
                        chunks.append(chunk)
                    raw = b"".join(chunks)
                    if clock() >= deadline:
                        raise GitHubEvidenceError("ready_attestation_wait_timeout")
                return json.loads(raw.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, http.client.HTTPException) as exc:
            raise GitHubEvidenceError(f"github_api_failure:{type(exc).__name__}") from exc

    def verify_workflow_run(
        self,
        *,
        run_id: int,
        expected_head_sha: str,
        expected_workflow_file: str,
        expected_event: str,
        expected_run_attempt: int = 1,
        required_completed_job: str | None = None,
    ) -> dict[str, Any]:
        # The formal landing job belongs to the Ready State Gate run it is
        # checking. Only that premerge path may verify the completed ordinary
        # state-gate job while the whole run is still executing. Every other
        # caller retains whole-run completed/SUCCESS verification.
        if required_completed_job is not None and (
            required_completed_job != "state-gate"
            or expected_workflow_file != ".github/workflows/state-gate.yml"
            or expected_event != "pull_request"
        ):
            return {"verified": False, "reason": "invalid_completed_job_scope"}
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
                "status": run.get("status") == "completed"
                or (required_completed_job is not None and run.get("status") == "in_progress"),
                "conclusion": run.get("conclusion") == "success"
                if run.get("status") == "completed"
                else required_completed_job is not None
                and run.get("conclusion") in (None, ""),
            }
            if not all(checks.values()):
                return {"verified": False, "reason": f"workflow_mismatch:{checks}"}
            if required_completed_job is not None:
                jobs = self._request_json(
                    f"/repos/{self.repository}/actions/runs/{int(run_id)}"
                    f"/attempts/{int(expected_run_attempt)}/jobs?per_page=100"
                )
                rows = jobs.get("jobs") if isinstance(jobs, dict) else None
                count = jobs.get("total_count") if isinstance(jobs, dict) else None
                if (
                    not isinstance(rows, list)
                    or isinstance(count, bool)
                    or not isinstance(count, int)
                    or count != len(rows)
                    or count > 100
                ):
                    return {"verified": False, "reason": "workflow_jobs_incomplete"}
                matches = [
                    job for job in rows
                    if isinstance(job, dict) and job.get("name") == required_completed_job
                ]
                if len(matches) != 1 or not (
                    matches[0].get("run_id") == int(run_id)
                    and matches[0].get("status") == "completed"
                    and matches[0].get("conclusion") == "success"
                ):
                    return {"verified": False, "reason": "workflow_completed_job_mismatch"}
                return {"verified": True, "run": run, "completed_job": matches[0]}
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
        self, *, pr_number: int, request_timeout: float | None = None,
        deadline: float | None = None, clock: Callable[[], float] = time.monotonic,
        strict_absence: bool = False,
    ) -> list[dict[str, Any]]:
        """Return every OWNER_LANDING_MERGE_ATTESTATION payload on a PR.

        Runtime identity fields are always appended from the live GitHub
        comment and never trusted from user-written payload bytes.  Duplicate
        or later-timestamp validation is the caller's responsibility so that
        every active-matching candidate can be counted deterministically.
        """

        try:
            path = f"/repos/{self.repository}/issues/{int(pr_number)}/comments?per_page=100"
            # Preserve ordinary callers' immediate, default-30s call shape.
            if request_timeout is None and deadline is None:
                comments = self._request_json(path)
            else:
                comments = self._request_json(path, timeout=30 if request_timeout is None else request_timeout,
                                              deadline=deadline, clock=clock)
        except GitHubEvidenceError as exc:
            raise GitHubEvidenceError(
                f"load_owner_landing_attestation_failed:{exc}"
            ) from exc
        if strict_absence:
            if not isinstance(comments, list) or any(not isinstance(comment, dict) for comment in comments):
                raise GitHubEvidenceError("ready_comments_response_invalid")
            if len(comments) >= 100:
                raise GitHubEvidenceError("ready_comments_response_truncated")
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
            blocks = list(pattern.finditer(body)) if strict_absence else []
            match = blocks[0] if blocks else pattern.search(body)
            if strict_absence and len(blocks) != 1:
                raise GitHubEvidenceError("ready_attestation_marker_malformed")
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

    def wait_for_owner_landing_merge_attestation(
        self, *, pr_number: int, expected_head_sha: str, expected_base_sha: str,
        current_state_gate_run_id: int,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> dict[str, Any]:
        """Wait only for true absence, never for invalid evidence to become valid.

        This opt-in workflow handshake is availability, not landing acceptance.
        Formal preflight must freshly reload and validate every canonical fact.
        """
        if (type(pr_number) is not int or pr_number <= 0
                or type(current_state_gate_run_id) is not int or current_state_gate_run_id <= 0
                or not isinstance(expected_head_sha, str) or re.fullmatch(r"[0-9a-f]{40}", expected_head_sha) is None
                or not isinstance(expected_base_sha, str) or re.fullmatch(r"[0-9a-f]{40}", expected_base_sha) is None):
            raise GitHubEvidenceError("ready_attestation_wait_identity_invalid")
        # Reuse existing canonical fields, digest and Owner set; no new schema.
        from .mainline_landing import (
            _OWNER_LANDING_ATTESTATION_FIELDS, FALSE_NONE_ALLOWED_OWNERS,
            owner_landing_content_digest,
        )
        started = clock()
        deadline = started + READY_ATTESTATION_WAIT_SECONDS
        for attempt in range(1, READY_ATTESTATION_MAX_POLLS + 1):
            remaining = deadline - clock()
            if remaining <= 0:
                raise GitHubEvidenceError("ready_attestation_wait_timeout")
            attestations = self.load_owner_landing_merge_attestations(
                pr_number=pr_number, request_timeout=min(30, remaining), deadline=deadline,
                clock=clock, strict_absence=True)
            if clock() >= deadline:
                raise GitHubEvidenceError("ready_attestation_wait_timeout")
            if not isinstance(attestations, list):
                raise GitHubEvidenceError("ready_attestation_response_invalid")
            if attestations:
                candidates = [att for att in attestations if isinstance(att, dict)
                              and att.get("source_pr") == pr_number
                              and att.get("accepted_exact_head_sha") == expected_head_sha
                              and att.get("authorization_status") == "active"]
                if len(candidates) != 1:
                    raise GitHubEvidenceError("ready_attestation_not_unique_or_stale")
                att = candidates[0]
                if (set(att) != _OWNER_LANDING_ATTESTATION_FIELDS
                        or att.get("schema_version") != 1
                        or att.get("repository") != self.repository
                        or self.repository != "dddd2024/Nerelan"
                        or att.get("locked_base_sha") != expected_base_sha
                        or type(att.get("ready_state_gate_run_id")) is not int
                        or att["ready_state_gate_run_id"] != current_state_gate_run_id
                        or att.get("_remote_author") not in FALSE_NONE_ALLOWED_OWNERS
                        or att.get("superseded_by")
                        or att.get("mainline_merge_intent_required") is not False
                        or att.get("active_pr_binding_mode") != "none"
                        or att.get("content_digest") != owner_landing_content_digest(att)):
                    raise GitHubEvidenceError("ready_attestation_binding_invalid")
                return {"evidence_available": True, "poll_attempts": attempt,
                        "elapsed_seconds": clock() - started,
                        "ready_run_id": current_state_gate_run_id}
            if attempt == READY_ATTESTATION_MAX_POLLS:
                raise GitHubEvidenceError("ready_attestation_poll_limit")
            remaining = deadline - clock()
            if remaining <= 0:
                raise GitHubEvidenceError("ready_attestation_wait_timeout")
            sleeper(min(READY_ATTESTATION_POLL_SECONDS, remaining))
        raise GitHubEvidenceError("ready_attestation_poll_limit")

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
        """Return committed raw bytes at an exact ref via the contents API."""

        try:
            payload = self._request_json(
                f"/repos/{self.repository}/contents/{path}?ref={ref}"
            )
        except (GitHubEvidenceError, TypeError, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}
        if payload.get("encoding") != "base64":
            return {"verified": False, "reason": "unexpected_content_encoding"}
        content = payload.get("content")
        if not isinstance(content, str):
            return {"verified": False, "reason": "invalid_content_type"}
        try:
            raw = _decode_github_contents_base64(content)
        except (binascii.Error, ValueError) as exc:
            return {"verified": False, "reason": str(exc)}
        return {"verified": True, "bytes": raw}
