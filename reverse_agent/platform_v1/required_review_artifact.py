"""Opt-in host-enforced review artifact contract, independent of model exit code.

The report is a deliverable, not an independent PR verdict. A report with
WITHHELD/REJECT is evidence of a non-accepted review; no task success is claimed.
No model-authored text can modify this preapproved contract.
"""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any

from .run_store import TaskStoreError

CATEGORY = "RequiredReviewArtifactContract"
VERSION = 1
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REVIEW = re.compile(r"Nerelan-Review: (ACCEPT|REJECT|WITHHELD) ([0-9a-f]{40})")
_FENCE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})")
_REVIEW_OUTCOME = re.compile(
    r"^(?:Final[ -]?)?(?:Outcome|Decision|Verdict|Review[ -]?Status):\s*"
    r"(REJECT|WITHHELD|FAIL|FAILED)\b", re.IGNORECASE
)


class _HtmlBlockTracker(HTMLParser):
    """Persistent stdlib lexer for real <pre>/<code> nesting and comments.

    One tracker is fed every non-fenced line together with its original line
    terminator, so incomplete tags, quoted attribute values and comments keep
    their lexical state across line boundaries and a newline still separates
    ``<pre`` from its attributes. Every real tag and comment on a line is
    tokenized, including several sharing one line: a comment never hides an
    adjacent ``<pre>``, and a second unclosed ``<!--`` after a closed one stays
    pending. Attribute values and comment bodies are token text, never tags. A
    close tag only closes when it matches the innermost open block, so an
    out-of-order close is a mismatch. ``in_tag`` reports whether the lexer is
    holding an unfinished tag or comment (a dangling ``&`` charref is not one).
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.stack: list[str] = []
        self.mismatch = False
        self.stray_comment_close = False

    def handle_data(self, data: str) -> None:
        # A top-level "-->" with no opening comment is as invalid as an
        # unclosed one; inside an example block it is inert text.
        if not self.stack and "-->" in data:
            self.stray_comment_close = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in ("pre", "code"):
            self.stack.append(tag.lower())

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag not in ("pre", "code"):
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif self.stack:
            self.mismatch = True
        # A stray close outside any open context is ignored: it is not a
        # declaration and must not reject a genuine report.

    @property
    def in_tag(self) -> bool:
        """True while the lexer holds an unfinished tag/comment, not a charref."""
        return self.rawdata.startswith("<")

    @property
    def in_comment(self) -> bool:
        return self.rawdata.startswith("<!--")

    @property
    def active(self) -> bool:
        return bool(self.stack) or self.in_tag


def _parse_review_marker(content: str) -> tuple[tuple[str, str] | None, str]:
    """Only a genuine top-level verdict counts, not an example or quoted template.

    Markdown comments/fenced examples can legitimately repeat a marker; they
    are never declarations. Contexts are mutually exclusive by priority: a
    Markdown fence makes every HTML/comment literal inside it inert, while an
    active HTML pre/code block or a real HTML comment makes Markdown fences
    inert. The HTML lexer is persistent across lines and receives each line's
    real terminator, so incomplete tags, quoted attributes and comments keep
    their true lexical state and a marker line inside any of them is not a
    declaration. Unclosed fences/comments/blocks fail closed. The report
    remains model-authored and is NOT a substitute for external acceptance.
    """
    markers: list[tuple[str, str]] = []
    fence: str | None = None
    html = _HtmlBlockTracker()
    for raw in content.splitlines(keepends=True):
        line = (raw.splitlines() or [""])[0]
        # A Markdown fence makes every HTML/comment literal inside it inert, so
        # fence-active content never feeds the HTML lexer (a literal unclosed
        # <pre> in an example cannot open a real block) and a literal <!-- does
        # not open a real comment that could hide a later live verdict.
        if fence is not None:
            opened = _FENCE.match(line)
            if opened and opened.group(1)[0] == fence[0] and len(opened.group(1)) >= len(fence):
                if not line[opened.end():].strip():
                    fence = None
            continue
        # A Markdown fence only opens at a line boundary with no active real
        # pre/code block, unfinished tag or open comment; inside those it is
        # inert content.
        live = not html.active
        if live:
            opened = _FENCE.match(line)
            if opened:
                fence = opened.group(1)
                continue
        # Every real tag and comment on the line is tokenized, with the actual
        # line terminator, so lexical separation and unfinished state persist.
        try:
            html.feed(raw)
        except Exception:
            return None, "review_html_code_mismatched"
        if html.mismatch:
            return None, "review_html_code_mismatched"
        if html.stray_comment_close:
            return None, "review_comment_unclosed"
        if not live or html.active:
            continue
        # Do not count block quotes, code indentation, list items or templates.
        if line.startswith((" ", "\t", ">", "-", "*", "+")):
            continue
        stripped = re.sub(r"^#{1,6}[ ]+", "", line)
        if _REVIEW_OUTCOME.match(stripped):
            return None, "review_explicit_failure_outcome"
        # Match the raw original marker line; never strip, decode or unescape
        # HTML to synthesize a marker that was not literally present.
        match = _REVIEW.fullmatch(line.strip())
        if match:
            markers.append((match.group(1), match.group(2)))
    if fence is not None:
        return None, "review_fence_unclosed"
    if html.in_comment:
        return None, "review_comment_unclosed"
    if html.active:
        return None, "review_html_code_unclosed"
    if len(markers) != 1:
        return None, "review_verdict_missing_or_ambiguous"
    return markers[0], ""

_SAFE_PATH = re.compile(r"[A-Za-z0-9_.\-/]{1,180}\Z")


def normalize_required_artifacts(raw: Any) -> tuple[dict[str, str], ...]:
    if not isinstance(raw, (list, tuple)) or len(raw) > 2:
        raise TaskStoreError("required_artifact_contract_invalid")
    result = []
    paths = set()
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"path", "kind", "expected_sha"}:
            raise TaskStoreError("required_artifact_fields_invalid")
        path, kind, sha = item["path"], item["kind"], item["expected_sha"]
        if (not isinstance(path, str) or not _SAFE_PATH.fullmatch(path)
                or not path.startswith("review_evidence/")
                or any(part in ("", ".", "..") for part in path.split("/"))
                or not path.endswith(".md") or path in paths):
            raise TaskStoreError("required_artifact_path_invalid")
        if kind != "review_report" or not isinstance(sha, str) or not _SHA.fullmatch(sha):
            raise TaskStoreError("required_artifact_identity_invalid")
        paths.add(path)
        result.append({"path": path, "kind": kind, "expected_sha": sha})
    return tuple(result)


def _serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(obj: dict[str, Any]) -> str:
    return hashlib.sha256(_serialize(obj).encode("utf-8")).hexdigest()


def freeze_required_artifacts(store: Any, task: Any, *, goal: Any, plan_task: Any) -> None:
    files = normalize_required_artifacts(plan_task.required_artifacts)
    if not files:
        return
    contract = {"version": VERSION, "task_id": task.id, "goal_id": goal.id,
                "goal_revision": goal.revision, "files": list(files)}
    old = load_required_artifacts(store.get_task(task.id))
    if old is not None:
        if old != contract:
            raise TaskStoreError("required_artifact_contract_conflict")
        return
    token = _digest(contract)
    store.add_evidence(task.id, category=CATEGORY, label="planned_review_deliverables",
                       value=token, status="APPROVED",
                       detail=_serialize(contract), raw_json_digest=token)


def load_required_artifacts(task: Any) -> dict[str, Any] | None:
    refs = [r for r in task.evidence_refs if r.get("category") == CATEGORY]
    if not refs:
        return None
    if len(refs) != 1:
        raise TaskStoreError("required_artifact_contract_ambiguous")
    row = refs[0]
    try:
        contract = json.loads(row["detail"])
        valid = (
            isinstance(contract, dict)
            and set(contract) == {"version", "task_id", "goal_id", "goal_revision", "files"}
            and contract["version"] == VERSION
            and contract["task_id"] == task.id
            and isinstance(contract["goal_id"], str) and bool(contract["goal_id"])
            and type(contract["goal_revision"]) is int and contract["goal_revision"] > 0
            and isinstance(contract["files"], list) and bool(contract["files"])
            and list(normalize_required_artifacts(contract["files"])) == contract["files"]
            and row["value"] == row["raw_json_digest"] == _digest(contract)
            and row["status"] == "APPROVED"
        )
    except (ValueError, KeyError, TypeError, TaskStoreError):
        valid = False
    if not valid:
        raise TaskStoreError("required_artifact_contract_tampered")
    return contract


def validate_required_artifacts(task: Any, worktree: str | Path) -> tuple[bool, str]:
    """Check actual bounded worktree bytes; does not trust agent narrative."""
    contract = load_required_artifacts(task)
    if contract is None:
        return True, "not_required"
    try:
        root = Path(worktree).resolve(strict=True)
        if not root.is_dir():
            return False, "artifact_worktree_missing"
        for spec in contract["files"]:
            candidate = root.joinpath(*spec["path"].split("/"))
            if any(part.is_symlink() for part in (candidate, *candidate.parents) if part != root):
                return False, "artifact_symlink_rejected"
            candidate = candidate.resolve(strict=True)
            if not candidate.is_relative_to(root) or not candidate.is_file():
                return False, "artifact_outside_worktree"
            size = candidate.stat().st_size
            if not 40 <= size <= 128 * 1024:
                return False, "artifact_empty_or_oversized"
            content = candidate.read_text(encoding="utf-8", errors="strict")
            marker, error = _parse_review_marker(content)
            if marker is None:
                return False, error
            verdict, sha = marker
            if sha != spec["expected_sha"]:
                return False, "review_exact_sha_mismatch"
            if verdict != "ACCEPT":
                return False, f"review_verdict_{verdict.lower()}"
    except (OSError, UnicodeError, ValueError, RuntimeError):
        return False, "required_artifact_missing_or_invalid"
    return True, "required_review_artifact_present"
