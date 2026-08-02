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
import re
import subprocess
from dataclasses import dataclass
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

# Canonical required (workflowName, event) keys for PR #97.
CANONICAL_WORKFLOW_KEYS: tuple[tuple[str, str], ...] = (
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
    """Production Issue provider using ``gh issue view``."""

    def fetch_issue(self, repository: str, issue_number: int) -> dict[str, Any]:
        result = subprocess.run(
            [
                "gh", "issue", "view", str(issue_number),
                "--repo", repository,
                "--json", "body,state,labels",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise AuthorityBundleError(
                "gh_issue_view_failed",
                f"exit={result.returncode}",
            )
        try:
            raw = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise AuthorityBundleError("gh_issue_json_parse_failed", str(exc))
        labels = []
        for label in raw.get("labels", []):
            if isinstance(label, dict):
                labels.append(str(label.get("name", "")))
            elif isinstance(label, str):
                labels.append(label)
        return {
            "body": str(raw.get("body", "")),
            "state": str(raw.get("state", "")),
            "labels": labels,
        }


class LivePRProvider:
    """Production PR provider using ``gh pr view``."""

    def fetch_pr(self, repository: str, pr_number: int) -> dict[str, Any]:
        result = subprocess.run(
            [
                "gh", "pr", "view", str(pr_number),
                "--repo", repository,
                "--json", "state,isDraft,baseRefName,baseRefOid,headRefName,headRefOid",
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


def _read_blob(repo_root: Path, path: str) -> bytes:
    """Read a file from the working tree (not git objects)."""

    full = repo_root / path
    if not full.is_file():
        raise AuthorityBundleError("missing_authority_file", path)
    return full.read_bytes()


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
) -> tuple[str, str, str]:
    decision_identity = intent.get("decision_identity", {})
    if not isinstance(decision_identity, dict):
        raise AuthorityBundleError("intent_decision_identity_not_object", "")
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
    required_workflows = intent.get("required_workflows", [])
    # F22/F23: Merge intent stores composite names (e.g. "State Gate (push)"),
    # not bare workflow names. Compare against the composite-name form so
    # push/pull_request State Gate remain distinct.
    expected_workflow_names = [
        composite_name(wf, ev) for wf, ev in CANONICAL_WORKFLOW_KEYS
    ]
    if required_workflows != expected_workflow_names:
        raise AuthorityBundleError(
            "intent_workflow_keys_mismatch",
            f"intent={required_workflows} expected={expected_workflow_names}",
        )
    return (
        str(intent.get("intent_id", "")),
        intent_decision_sha,
        intent_plan_sha,
    )


def _validate_issue(
    issue: dict[str, Any],
    *,
    expected_issue: int,
    expected_repository: str,
) -> str:
    state = str(issue.get("state", "")).upper()
    if state != "OPEN":
        raise AuthorityBundleError("issue_not_open", state)
    labels = issue.get("labels", [])
    label_set = set(labels)
    missing = REQUIRED_ISSUE_LABELS - label_set
    if missing:
        raise AuthorityBundleError("issue_missing_labels", ",".join(sorted(missing)))
    body = str(issue.get("body", ""))
    return _sha256_bytes(body.encode("utf-8"))


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

    repo_root = Path(repo_dir)

    # 1. Load decision_packet.md
    decision_raw = _read_blob(repo_root, "project_state/decision_packet.md")
    meta, contract, decision_sha256 = _parse_decision_packet(decision_raw)
    _validate_decision_meta(meta)

    decision_id = meta["decision_id"]
    round_id = meta["round_id"]

    # 2. Extract expected bindings from contract
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

    # 3. Load command_plan.json
    plan_raw = _read_blob(repo_root, "project_state/gates/command_plan.json")
    plan, plan_sha256 = _parse_command_plan(plan_raw)
    command_ids, allowed_commands = _validate_command_plan(
        plan,
        expected_decision_id=decision_id,
        expected_round_id=round_id,
    )

    # 4. Load active merge intent
    intent_raw = _read_blob(repo_root, "project_state/mainline_merge_intents/active.json")
    intent, _intent_sha = _parse_merge_intent(intent_raw)
    intent_id, intent_decision_sha, intent_plan_sha = _validate_merge_intent(
        intent,
        expected_decision_id=decision_id,
        expected_decision_sha256=decision_sha256,
        expected_command_plan_sha256=plan_sha256,
        expected_pr=pr_number,
        expected_base=expected_base,
        expected_repository=repository,
    )

    # 5. Load GitHub Issue
    issue_data = issue_provider.fetch_issue(repository, issue_number)
    issue_body_sha256 = _validate_issue(
        issue_data,
        expected_issue=issue_number,
        expected_repository=repository,
    )

    # 6. Load GitHub PR
    pr_data = pr_provider.fetch_pr(repository, pr_number)
    pr_observed = _validate_pr(
        pr_data,
        expected_pr=pr_number,
        expected_repository=repository,
        expected_branch=expected_branch,
        expected_base=expected_base,
    )

    # 7. Extract allowed paths from contract
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
        required_workflow_keys=CANONICAL_WORKFLOW_KEYS,
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
