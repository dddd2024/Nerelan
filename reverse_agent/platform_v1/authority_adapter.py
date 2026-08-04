"""Authority Bundle loader and cross-validator for Platform V1 live path.

F20/F26: The live CLI must not accept a raw Work Item or authority digest
from stdin. Instead, it loads an immutable Authority Bundle internally from:

- ``project_state/decision_packet.md`` (Decision meta + contract)
- ``project_state/gates/command_plan.json`` (generated Command Plan)
- ``project_state/mainline_merge_intents/active.json`` (active merge intent)
- GitHub Issue (body, state, labels)
- GitHub PR (state, draft, head/base SHA, branch)

The bundle cross-validates every digest and binding. If any check fails,
``AuthorityBundleError`` is raised and live execution is blocked.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from ..project_state import extract_markdown_json_block
from .contracts import PlatformWorkItem
from .github_adapter import composite_name


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class AuthorityBundleError(Exception):
    """Raised when Authority Bundle loading or cross-validation fails."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SHA1_HEX_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

_ISO_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)


def _parse_strict_iso_timestamp(value: str) -> bool:
    """Return True iff ``value`` is a strict, timezone-aware ISO timestamp."""

    if not _ISO_TIMESTAMP_RE.match(value):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None

# Canonical required (workflowName, event) keys for the active merge intent.
# This is the historical four-workflow policy, kept for validating immutable
# archive files.  Active intents from v8 onward use PRE_MERGE_WORKFLOW_KEYS.
CANONICAL_WORKFLOW_KEYS: tuple[tuple[str, str], ...] = (
    ("CI", "pull_request"),
    ("Decision Preflight", "pull_request"),
    ("State Gate", "pull_request_target"),
    ("State Gate", "push"),
)

# Pre-merge evidence policy: the only workflow observations required before
# merge are CI, Decision Preflight, and the trusted-target State Gate
# (pull_request_target).  ``State Gate (push)`` is a post-merge mainline
# integration enforcement gate and must NOT be required as a pre-merge
# attestation prerequisite.
PRE_MERGE_WORKFLOW_KEYS: tuple[tuple[str, str], ...] = (
    ("CI", "pull_request"),
    ("Decision Preflight", "pull_request"),
    ("State Gate", "pull_request_target"),
)

# Historical canonical keys for archived intents that were created when the
# State Gate PR trigger was ``pull_request``.  Used only for validating
# immutable archive files.
HISTORICAL_WORKFLOW_KEYS_PULL_REQUEST: tuple[tuple[str, str], ...] = (
    ("CI", "pull_request"),
    ("Decision Preflight", "pull_request"),
    ("State Gate", "pull_request"),
    ("State Gate", "push"),
)

REQUIRED_ISSUE_LABELS = frozenset({"work-item", "r2", "owner-accepted"})


# ---------------------------------------------------------------------------
# Injectable provider protocols
# ---------------------------------------------------------------------------

class IssueProvider(Protocol):
    """Injectable GitHub Issue provider."""

    def fetch_issue(self, repository: str, issue_number: int) -> dict[str, Any]:
        """Return {'body': str, 'state': str, 'labels': list[str]}."""
        ...


class PRProvider(Protocol):
    """Injectable GitHub PR provider."""

    def fetch_pr(self, repository: str, pr_number: int) -> dict[str, Any]:
        """Return PR metadata dict."""
        ...


# ---------------------------------------------------------------------------
# Live providers using gh CLI
# ---------------------------------------------------------------------------

class LiveIssueProvider:
    """Production Issue provider using structured GraphQL via ``gh api graphql``.

    F1/v9: Replaces the unsupported ``gh issue view --json
    content_last_edited_at`` command with a structured GraphQL query that
    retrieves ``data.repository.issue.{body,state,labels}``.

    Fail-closed rules:
    - ``data.repository.issue`` envelope must be present;
    - labels pagination must be complete (``hasNextPage == false``) or
      the provider fails closed;
    - no fixture/default substitution for a failed live observation.
    """

    def fetch_issue(self, repository: str, issue_number: int) -> dict[str, Any]:
        parts = repository.split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise AuthorityBundleError("invalid_repository_format", repository)
        owner, name = parts[0], parts[1]
        # Single-line GraphQL query to avoid shell quoting issues.
        query = (
            "query{"
            f'repository(owner:"{owner}",name:"{name}"){{'
            f"issue(number:{int(issue_number)}){{"
            "body state"
            "labels(first:100){nodes{name}pageInfo{hasNextPage endCursor}}"
            "}}"
            "}}"
            "}"
        )
        result = subprocess.run(
            [
                "gh", "api", "graphql",
                "-f", f"query={query}",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise AuthorityBundleError(
                "gh_api_graphql_failed",
                f"exit={result.returncode}",
            )
        try:
            envelope = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise AuthorityBundleError("graphql_json_parse_failed", str(exc))

        data = envelope.get("data")
        if not isinstance(data, dict):
            raise AuthorityBundleError(
                "graphql_missing_data_envelope",
                str(envelope.get("errors", "")),
            )
        repo_data = data.get("repository")
        if not isinstance(repo_data, dict):
            raise AuthorityBundleError("graphql_repository_missing", "")
        issue = repo_data.get("issue")
        if not isinstance(issue, dict):
            raise AuthorityBundleError("graphql_issue_missing", "")

        # Complete labels pagination or fail closed.
        labels_data = issue.get("labels")
        if not isinstance(labels_data, dict):
            raise AuthorityBundleError("graphql_labels_missing", "")
        page_info = labels_data.get("pageInfo")
        if not isinstance(page_info, dict):
            raise AuthorityBundleError("graphql_labels_page_info_missing", "")
        if page_info.get("hasNextPage"):
            raise AuthorityBundleError(
                "graphql_labels_pagination_incomplete",
                str(page_info.get("endCursor", "")),
            )
        labels_nodes = labels_data.get("nodes")
        if not isinstance(labels_nodes, list):
            raise AuthorityBundleError("graphql_labels_nodes_missing", "")
        labels = [
            str(n.get("name", ""))
            for n in labels_nodes
            if isinstance(n, dict) and n.get("name")
        ]

        return {
            "body": str(issue.get("body", "")),
            "state": str(issue.get("state", "")),
            "labels": labels,
        }


class LivePRProvider:
    """Production PR provider using ``gh pr view``."""

    def fetch_pr(self, repository: str, pr_number: int) -> dict[str, Any]:
        result = subprocess.run(
            [
                "gh", "pr", "view", str(pr_number),
                "--repo", repository,
                "--json", "state,isDraft,baseRefName,baseRefOid,headRefName,headRefOid,autoMergeRequest",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise AuthorityBundleError(
                "gh_pr_view_failed",
                f"exit={result.returncode}",
            )
        try:
            raw = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise AuthorityBundleError("gh_pr_json_parse_failed", str(exc))
        return {
            "state": str(raw.get("state", "")),
            "isDraft": bool(raw.get("isDraft", False)),
            "baseRefName": str(raw.get("baseRefName", "")),
            "baseRefOid": str(raw.get("baseRefOid", "")),
            "headRefName": str(raw.get("headRefName", "")),
            "headRefOid": str(raw.get("headRefOid", "")),
            "autoMergeRequest": raw.get("autoMergeRequest"),
        }


# ---------------------------------------------------------------------------
# Authority Bundle
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuthorityBundle:
    """Immutable, cross-validated authority for live execution.

    Loaded internally from repository state and GitHub facts. Never accepts
    caller-supplied digests or Work Item payloads.
    """

    # Decision identity
    decision_id: str
    round_id: str
    decision_content_sha256: str

    # Command Plan
    command_plan_sha256: str
    allowed_command_ids: tuple[str, ...]
    allowed_commands: tuple[dict[str, Any], ...]

    # Issue
    issue_number: int
    issue_body_sha256: str
    issue_state: str
    issue_labels: tuple[str, ...]
    # Repository and PR
    repository: str
    pr_number: int
    branch: str
    base_sha: str
    risk_tier: str

    # Merge intent
    intent_id: str
    intent_decision_content_sha256: str
    intent_command_plan_sha256: str

    # Allowed paths
    allowed_paths: tuple[str, ...]

    # Required workflow/event keys
    required_workflow_keys: tuple[tuple[str, str], ...]

    # PR observations (filled by cross-validation)
    pr_state: str = ""
    pr_is_draft: bool = False
    pr_head_ref_name: str = ""
    pr_head_ref_oid: str = ""
    pr_base_ref_name: str = ""
    pr_base_ref_oid: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_AUTHORITY_PATHS = (
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/mainline_merge_intents/active.json",
)


def _hardened_git_env() -> dict[str, str]:
    blocked = {
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_REPLACE_REF_BASE", "GIT_COMMON_DIR",
        "GIT_CONFIG", "GIT_EXTERNAL_DIFF", "GIT_DIFF_OPTS",
    }
    env = {
        key: value for key, value in os.environ.items()
        if key not in blocked
        and not key.startswith("GIT_CONFIG_KEY_")
        and not key.startswith("GIT_CONFIG_VALUE_")
    }
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    return env


def _git_object_command(repo_root: Path, args: list[str]) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args], capture_output=True,
        timeout=30, env=_hardened_git_env(),
    )
    if result.returncode != 0:
        raise AuthorityBundleError(
            "authority_git_object_read_failed",
            f"command={args[0]}:exit={result.returncode}",
        )
    return result.stdout


def _require_commit(repo_root: Path, head_sha: str) -> None:
    _git_object_command(repo_root, ["cat-file", "-e", f"{head_sha}^{{commit}}"])


def _read_exact_authority_blob(repo_root: Path, head_sha: str, path: str) -> bytes:
    if path not in _AUTHORITY_PATHS:
        raise AuthorityBundleError("authority_path_not_allowed", path)
    raw = _git_object_command(repo_root, ["ls-tree", "-z", head_sha, "--", path])
    records = [record for record in raw.split(b"\0") if record]
    if len(records) != 1:
        raise AuthorityBundleError("authority_tree_entry_count_invalid", path)
    try:
        identity, observed_path = records[0].split(b"\t", 1)
        mode, object_type, _oid = identity.split(b" ", 2)
        decoded_path = observed_path.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise AuthorityBundleError("authority_tree_entry_malformed", path) from exc
    if decoded_path != path:
        raise AuthorityBundleError("authority_tree_path_mismatch", decoded_path)
    if mode not in (b"100644", b"100755") or object_type != b"blob":
        raise AuthorityBundleError(
            "authority_tree_entry_not_regular_blob",
            f"path={path}:mode={mode.decode(errors='replace')}:type={object_type.decode(errors='replace')}",
        )
    return _git_object_command(repo_root, ["cat-file", "blob", f"{head_sha}:{path}"])


def _validate_live_pr_shape(pr: dict[str, Any]) -> dict[str, Any]:
    state = str(pr.get("state", "")).upper()
    if state != "OPEN":
        raise AuthorityBundleError("pr_not_open", state)
    if not pr.get("isDraft", False):
        raise AuthorityBundleError("pr_not_draft", "")
    if pr.get("autoMergeRequest") is not None:
        raise AuthorityBundleError("pr_auto_merge_enabled", str(pr.get("autoMergeRequest")))
    if pr.get("baseRefName") != "main":
        raise AuthorityBundleError("pr_wrong_base_branch", str(pr.get("baseRefName")))
    for field in ("baseRefOid", "headRefOid"):
        value = str(pr.get(field, ""))
        if not _SHA1_HEX_RE.fullmatch(value):
            raise AuthorityBundleError("pr_oid_invalid", f"{field}={value}")
    if not str(pr.get("headRefName", "")):
        raise AuthorityBundleError("pr_head_branch_missing", "")
    return pr


def _parse_decision_packet(raw: bytes) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Parse decision_packet.md and return (meta, contract, content_sha256).

    The content SHA-256 is computed over the raw file bytes — not the parsed
    objects — so any material edit to the file changes the digest.
    """

    text = raw.decode("utf-8")
    meta_parsed = extract_markdown_json_block(text, "decision_meta")
    if not meta_parsed.get("found") or meta_parsed.get("parse_error"):
        raise AuthorityBundleError(
            "invalid_decision_meta",
            str(meta_parsed.get("parse_error")),
        )
    meta = {
        k: v for k, v in meta_parsed.items()
        if k not in {"found", "parse_error"}
    }

    contract_parsed = extract_markdown_json_block(text, "decision_contract")
    if not contract_parsed.get("found") or contract_parsed.get("parse_error"):
        raise AuthorityBundleError(
            "invalid_decision_contract",
            str(contract_parsed.get("parse_error")),
        )
    contract = {
        k: v for k, v in contract_parsed.items()
        if k not in {"found", "parse_error"}
    }

    content_sha256 = _sha256_bytes(raw)
    return meta, contract, content_sha256


def _parse_command_plan(raw: bytes) -> tuple[dict[str, Any], str]:
    """Parse command_plan.json and return (plan, sha256)."""

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AuthorityBundleError("invalid_command_plan_json", str(exc))
    if not isinstance(plan, dict):
        raise AuthorityBundleError("command_plan_not_object", "")
    return plan, _sha256_bytes(raw)


def _parse_merge_intent(raw: bytes) -> tuple[dict[str, Any], str]:
    """Parse active.json merge intent and return (intent, sha256)."""

    try:
        intent = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AuthorityBundleError("invalid_merge_intent_json", str(exc))
    if not isinstance(intent, dict):
        raise AuthorityBundleError("merge_intent_not_object", "")
    return intent, _sha256_bytes(raw)


# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------

def _validate_decision_meta(meta: dict[str, Any]) -> None:
    if meta.get("schema_version") != 1:
        raise AuthorityBundleError("invalid_decision_schema_version", str(meta.get("schema_version")))
    if meta.get("status") != "APPROVED":
        raise AuthorityBundleError("decision_not_approved", str(meta.get("status")))
    if meta.get("mainline") != "engineering_branch":
        raise AuthorityBundleError("invalid_mainline", str(meta.get("mainline")))
    decision_id = meta.get("decision_id", "")
    if not isinstance(decision_id, str) or not re.fullmatch(r"decision_[A-Za-z0-9][A-Za-z0-9_.-]{2,190}", decision_id):
        raise AuthorityBundleError("invalid_decision_id", str(decision_id))
    round_id = meta.get("round_id", "")
    if not isinstance(round_id, str) or not re.fullmatch(r"round_[A-Za-z0-9][A-Za-z0-9_.-]{2,191}", round_id):
        raise AuthorityBundleError("invalid_round_id", str(round_id))


def _validate_contract(
    contract: dict[str, Any],
    *,
    expected_issue: int,
    expected_pr: int,
    expected_branch: str,
    expected_base: str,
) -> None:
    if contract.get("source_issue") != expected_issue:
        raise AuthorityBundleError(
            "contract_issue_mismatch",
            f"contract={contract.get('source_issue')} expected={expected_issue}",
        )
    if contract.get("active_pr") != expected_pr:
        raise AuthorityBundleError(
            "contract_pr_mismatch",
            f"contract={contract.get('active_pr')} expected={expected_pr}",
        )
    if contract.get("required_branch") != expected_branch:
        raise AuthorityBundleError(
            "contract_branch_mismatch",
            f"contract={contract.get('required_branch')} expected={expected_branch}",
        )
    if contract.get("activation_base_sha") != expected_base:
        raise AuthorityBundleError(
            "contract_base_mismatch",
            f"contract={contract.get('activation_base_sha')} expected={expected_base}",
        )
    if contract.get("risk_tier") != "R2":
        raise AuthorityBundleError("invalid_risk_tier", str(contract.get("risk_tier")))
    # Forbidden operations must all be false
    for key in (
        "merge_allowed", "mark_ready_allowed", "auto_merge_allowed",
        "force_push_allowed", "rebase_allowed",
        "release_allowed", "deployment_allowed",
        "real_provider_credential_allowed",
        "live_work_item_publication_allowed",
        "trusted_host_live_probe_allowed",
        "audit_generation_allowed",
    ):
        if contract.get(key) is not False:
            raise AuthorityBundleError("forbidden_operation_not_false", key)


def _validate_command_plan(
    plan: dict[str, Any],
    *,
    expected_decision_id: str,
    expected_round_id: str,
) -> tuple[tuple[str, ...], tuple[dict[str, Any], ...]]:
    if plan.get("decision_id") != expected_decision_id:
        raise AuthorityBundleError(
            "plan_decision_id_mismatch",
            f"plan={plan.get('decision_id')} expected={expected_decision_id}",
        )
    if plan.get("round_id") != expected_round_id:
        raise AuthorityBundleError(
            "plan_round_id_mismatch",
            f"plan={plan.get('round_id')} expected={expected_round_id}",
        )
    commands = plan.get("commands", [])
    if not isinstance(commands, list):
        raise AuthorityBundleError("commands_not_list", "")
    command_ids: list[str] = []
    allowed_commands: list[dict[str, Any]] = []
    for cmd in commands:
        if not isinstance(cmd, dict):
            raise AuthorityBundleError("command_not_object", "")
        cid = str(cmd.get("command_id", ""))
        if not cid:
            raise AuthorityBundleError("missing_command_id", "")
        if cid in command_ids:
            raise AuthorityBundleError("duplicate_command_id", cid)
        command_ids.append(cid)
        allowed_commands.append(cmd)
    return tuple(command_ids), tuple(allowed_commands)


def _validate_merge_intent(
    intent: dict[str, Any],
    *,
    expected_decision_id: str,
    expected_decision_sha256: str,
    expected_command_plan_sha256: str,
    expected_pr: int,
    expected_base: str,
    expected_repository: str,
    validation_time: datetime | None = None,
) -> tuple[str, str, str]:
    # v9/F6: Enforce the exact active-Intent field set.  Any missing or
    # extra field blocks.  Historical archives are validated separately via
    # their historical policy snapshot, not through this function.
    expected_fields = {
        "schema_version",
        "intent_id",
        "repository",
        "source_pr",
        "locked_base_sha",
        "allowed_merge_method",
        "decision_identity",
        "command_plan_sha256",
        "merge_tree_policy",
        "required_workflows",
        "post_merge_integration_workflow",
        "expires_at",
    }
    observed_fields = set(intent.keys())
    if observed_fields != expected_fields:
        missing = sorted(expected_fields - observed_fields)
        extra = sorted(observed_fields - expected_fields)
        raise AuthorityBundleError(
            "intent_field_set_mismatch",
            f"missing={missing} extra={extra}",
        )
    if intent.get("schema_version") != 1:
        raise AuthorityBundleError(
            "invalid_intent_schema_version", str(intent.get("schema_version")),
        )
    intent_id = intent.get("intent_id")
    if not isinstance(intent_id, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", intent_id,
    ):
        raise AuthorityBundleError("invalid_intent_id", str(intent_id))
    decision_identity = intent.get("decision_identity", {})
    if not isinstance(decision_identity, dict):
        raise AuthorityBundleError("intent_decision_identity_not_object", "")
    expected_decision_identity_fields = {
        "decision_id", "decision_content_sha256",
    }
    if set(decision_identity) != expected_decision_identity_fields:
        raise AuthorityBundleError(
            "intent_decision_identity_field_set_mismatch",
            f"observed={sorted(decision_identity)} "
            f"expected={sorted(expected_decision_identity_fields)}",
        )
    if decision_identity.get("decision_id") != expected_decision_id:
        raise AuthorityBundleError(
            "intent_decision_id_mismatch",
            f"intent={decision_identity.get('decision_id')} expected={expected_decision_id}",
        )
    intent_decision_sha = str(decision_identity.get("decision_content_sha256", ""))
    if not _SHA256_HEX_RE.match(intent_decision_sha):
        raise AuthorityBundleError("invalid_intent_decision_sha256", intent_decision_sha)
    if intent_decision_sha != expected_decision_sha256:
        raise AuthorityBundleError(
            "intent_decision_sha_mismatch",
            f"intent={intent_decision_sha} expected={expected_decision_sha256}",
        )
    intent_plan_sha = str(intent.get("command_plan_sha256", ""))
    if not _SHA256_HEX_RE.match(intent_plan_sha):
        raise AuthorityBundleError("invalid_intent_plan_sha256", intent_plan_sha)
    if intent_plan_sha != expected_command_plan_sha256:
        raise AuthorityBundleError(
            "intent_plan_sha_mismatch",
            f"intent={intent_plan_sha} expected={expected_command_plan_sha256}",
        )
    if intent.get("source_pr") != expected_pr:
        raise AuthorityBundleError(
            "intent_pr_mismatch",
            f"intent={intent.get('source_pr')} expected={expected_pr}",
        )
    if intent.get("locked_base_sha") != expected_base:
        raise AuthorityBundleError(
            "intent_base_mismatch",
            f"intent={intent.get('locked_base_sha')} expected={expected_base}",
        )
    if intent.get("repository") != expected_repository:
        raise AuthorityBundleError(
            "intent_repository_mismatch",
            f"intent={intent.get('repository')} expected={expected_repository}",
        )
    if intent.get("allowed_merge_method") != "merge":
        raise AuthorityBundleError(
            "intent_merge_method_mismatch",
            f"intent={intent.get('allowed_merge_method')} expected=merge",
        )
    if intent.get("merge_tree_policy") != "equal_to_accepted_head_tree":
        raise AuthorityBundleError(
            "intent_merge_tree_policy_mismatch",
            f"intent={intent.get('merge_tree_policy')} "
            "expected=equal_to_accepted_head_tree",
        )
    expires_at = intent.get("expires_at")
    if not isinstance(expires_at, str) or not _parse_strict_iso_timestamp(expires_at):
        raise AuthorityBundleError("intent_expires_at_invalid", str(expires_at))
    expires_at_datetime = datetime.fromisoformat(
        expires_at.replace("Z", "+00:00"),
    ).astimezone(timezone.utc)
    observed_time = validation_time or datetime.now(timezone.utc)
    if observed_time.tzinfo is None:
        raise AuthorityBundleError("intent_validation_time_not_aware", "")
    if expires_at_datetime <= observed_time.astimezone(timezone.utc):
        raise AuthorityBundleError(
            "intent_expired",
            f"expires_at={expires_at} validation_time={observed_time.isoformat()}",
        )
    required_workflows = intent.get("required_workflows", [])
    # v9/F6: Active intents must use the exact three-workflow pre-merge
    # policy.  Composite names are compared so that pull_request_target
    # remains distinct from push/pull_request State Gate.
    expected_workflow_names = [
        composite_name(wf, ev) for wf, ev in PRE_MERGE_WORKFLOW_KEYS
    ]
    if required_workflows != expected_workflow_names:
        raise AuthorityBundleError(
            "intent_workflow_keys_mismatch",
            f"intent={required_workflows} expected={expected_workflow_names}",
        )
    # v9/F6: post_merge_integration_workflow must be exactly State Gate (push).
    if intent.get("post_merge_integration_workflow") != "State Gate (push)":
        raise AuthorityBundleError(
            "intent_post_merge_workflow_mismatch",
            f"intent={intent.get('post_merge_integration_workflow')} expected=State Gate (push)",
        )
    return (
        intent_id,
        intent_decision_sha,
        intent_plan_sha,
    )


def _validate_issue(
    issue: dict[str, Any],
    *,
    expected_issue: int,
    expected_repository: str,
) -> str:
    """Validate the live Issue observation and return its body SHA-256.

    Platform V1 deliberately does not treat ``lastEditedAt`` as an authority
    control because it has no approved revision or timestamp to compare it
    against.  Path-A's approval-revision verifier owns edit/revert protection.
    """

    state = str(issue.get("state", "")).upper()
    if state != "OPEN":
        raise AuthorityBundleError("issue_not_open", state)
    labels = issue.get("labels", [])
    label_set = set(labels)
    missing = REQUIRED_ISSUE_LABELS - label_set
    if missing:
        raise AuthorityBundleError("issue_missing_labels", ",".join(sorted(missing)))
    body = str(issue.get("body", ""))
    body_sha256 = _sha256_bytes(body.encode("utf-8"))
    return body_sha256


def _validate_pr(
    pr: dict[str, Any],
    *,
    expected_pr: int,
    expected_repository: str,
    expected_branch: str,
    expected_base: str,
) -> dict[str, Any]:
    state = str(pr.get("state", "")).upper()
    if state != "OPEN":
        raise AuthorityBundleError("pr_not_open", state)
    if not pr.get("isDraft", False):
        raise AuthorityBundleError("pr_not_draft", "")
    # v9/F5: autoMergeRequest must be null — a Draft PR with auto-merge
    # enabled must not enter the Authority Bundle.
    if pr.get("autoMergeRequest") is not None:
        raise AuthorityBundleError(
            "pr_auto_merge_enabled",
            str(pr.get("autoMergeRequest")),
        )
    if pr.get("baseRefName") != "main":
        raise AuthorityBundleError("pr_wrong_base_branch", str(pr.get("baseRefName")))
    if pr.get("baseRefOid") != expected_base:
        raise AuthorityBundleError(
            "pr_base_mismatch",
            f"pr={pr.get('baseRefOid')} expected={expected_base}",
        )
    if pr.get("headRefName") != expected_branch:
        raise AuthorityBundleError(
            "pr_head_branch_mismatch",
            f"pr={pr.get('headRefName')} expected={expected_branch}",
        )
    return pr


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_authority_bundle(
    *,
    repo_dir: str,
    repository: str,
    issue_number: int,
    pr_number: int,
    issue_provider: IssueProvider | None = None,
    pr_provider: PRProvider | None = None,
    validation_time: datetime | None = None,
) -> AuthorityBundle:
    """Load and cross-validate the Authority Bundle.

    F20/F26: This function reads authority from internal repository state
    and GitHub facts. It does NOT accept a Work Item, authority digest, or
    any caller-supplied authority payload.

    Parameters are target identifiers only:
    - ``repo_dir``: local repository path
    - ``repository``: GitHub repository (owner/name)
    - ``issue_number``: GitHub Issue number
    - ``pr_number``: GitHub PR number

    Raises ``AuthorityBundleError`` on any validation failure.
    """

    if issue_provider is None:
        issue_provider = LiveIssueProvider()
    if pr_provider is None:
        pr_provider = LivePRProvider()

    repo_root = Path(repo_dir).resolve(strict=True)

    # 1. Observe the live PR before parsing any candidate authority.
    pr_data = pr_provider.fetch_pr(repository, pr_number)
    pr_observed = _validate_live_pr_shape(pr_data)
    live_head = str(pr_observed["headRefOid"])
    _require_commit(repo_root, live_head)

    # 2. Load Decision from the exact live-head regular blob.
    decision_raw = _read_exact_authority_blob(
        repo_root, live_head, "project_state/decision_packet.md",
    )
    meta, contract, decision_sha256 = _parse_decision_packet(decision_raw)
    _validate_decision_meta(meta)

    decision_id = meta["decision_id"]
    round_id = meta["round_id"]

    # 3. Extract expected bindings from contract
    expected_issue = int(contract.get("source_issue", 0))
    expected_pr = int(contract.get("active_pr", 0))
    expected_branch = str(contract.get("required_branch", ""))
    expected_base = str(contract.get("activation_base_sha", ""))

    if expected_issue != issue_number:
        raise AuthorityBundleError(
            "issue_number_mismatch",
            f"contract={expected_issue} stdin={issue_number}",
        )
    if expected_pr != pr_number:
        raise AuthorityBundleError(
            "pr_number_mismatch",
            f"contract={expected_pr} stdin={pr_number}",
        )
    if not _SHA1_HEX_RE.match(expected_base):
        raise AuthorityBundleError("invalid_base_sha", expected_base)

    _validate_contract(
        contract,
        expected_issue=issue_number,
        expected_pr=pr_number,
        expected_branch=expected_branch,
        expected_base=expected_base,
    )

    # 4. Load Command Plan from the exact live-head regular blob.
    plan_raw = _read_exact_authority_blob(
        repo_root, live_head, "project_state/gates/command_plan.json",
    )
    plan, plan_sha256 = _parse_command_plan(plan_raw)
    command_ids, allowed_commands = _validate_command_plan(
        plan,
        expected_decision_id=decision_id,
        expected_round_id=round_id,
    )

    # 5. Load active Intent from the exact live-head regular blob.
    intent_raw = _read_exact_authority_blob(
        repo_root, live_head, "project_state/mainline_merge_intents/active.json",
    )
    intent, _intent_sha = _parse_merge_intent(intent_raw)
    intent_id, intent_decision_sha, intent_plan_sha = _validate_merge_intent(
        intent,
        expected_decision_id=decision_id,
        expected_decision_sha256=decision_sha256,
        expected_command_plan_sha256=plan_sha256,
        expected_pr=pr_number,
        expected_base=expected_base,
        expected_repository=repository,
        validation_time=validation_time,
    )

    # 6. Validate the already-observed PR against exact Decision bindings.
    pr_observed = _validate_pr(
        pr_observed,
        expected_pr=pr_number,
        expected_repository=repository,
        expected_branch=expected_branch,
        expected_base=expected_base,
    )

    # 7. Load GitHub Issue
    issue_data = issue_provider.fetch_issue(repository, issue_number)
    issue_body_sha256 = _validate_issue(
        issue_data,
        expected_issue=issue_number,
        expected_repository=repository,
    )

    # 8. Extract allowed paths from contract
    allowed_paths = tuple(str(p) for p in contract.get("allowed_mutated_paths", []))

    return AuthorityBundle(
        decision_id=decision_id,
        round_id=round_id,
        decision_content_sha256=decision_sha256,
        command_plan_sha256=plan_sha256,
        allowed_command_ids=command_ids,
        allowed_commands=allowed_commands,
        issue_number=issue_number,
        issue_body_sha256=issue_body_sha256,
        issue_state=str(issue_data.get("state", "")).upper(),
        issue_labels=tuple(str(l) for l in issue_data.get("labels", [])),
        repository=repository,
        pr_number=pr_number,
        branch=expected_branch,
        base_sha=expected_base,
        risk_tier=str(contract.get("risk_tier", "R2")),
        intent_id=intent_id,
        intent_decision_content_sha256=intent_decision_sha,
        intent_command_plan_sha256=intent_plan_sha,
        allowed_paths=allowed_paths,
        # v9/F2: Return exactly the validated three pre-merge workflow keys.
        # State Gate (push) is post-merge metadata, NOT a pre-merge prerequisite.
        required_workflow_keys=PRE_MERGE_WORKFLOW_KEYS,
        pr_state=str(pr_observed.get("state", "")).upper(),
        pr_is_draft=bool(pr_observed.get("isDraft", False)),
        pr_head_ref_name=str(pr_observed.get("headRefName", "")),
        pr_head_ref_oid=str(pr_observed.get("headRefOid", "")),
        pr_base_ref_name=str(pr_observed.get("baseRefName", "")),
        pr_base_ref_oid=str(pr_observed.get("baseRefOid", "")),
    )


def select_command(bundle: AuthorityBundle, command_id: str) -> dict[str, Any]:
    """Select a command from the Authority Bundle by exact command_id.

    F19: Commands are selected by ``command_id`` from the approved Command
    Plan, never from caller-supplied shell text.

    Raises ``AuthorityBundleError`` if the command_id is unknown.
    """

    for cmd in bundle.allowed_commands:
        if cmd.get("command_id") == command_id:
            return cmd
    raise AuthorityBundleError("unknown_command_id", command_id)
