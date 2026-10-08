"""Bounded, read-only diagnostics BEFORE requesting ordinary-R1 approval.

APPROVAL_READY is structural readiness, never approval, execution authority or
product acceptance. Live GitHub approval, ownership and exact-head checks remain
mandatory. This module reuses Path A; it does not replace that authority path.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Sequence

from . import path_a

MAX_INPUT_BYTES = 256 * 1024
MAX_PATHS = 128
MAX_OCCUPIED_PATHS = 256
MAX_DIAGNOSTICS = 64
MAX_PATH_LENGTH = 512

# These are existing Issue headings, not a new authority schema. Aliases in one
# group are mutually exclusive: never silently select the first of two scopes.
_SECTION_ALIASES = {
    "specification": ("Approved specification", "Approved specification candidate"),
    "allowed_paths": ("Allowed paths",),
    "forbidden_operations": ("Forbidden operations",),
    "acceptance": ("Acceptance criteria",),
    "checks": ("Required checks", "Required deterministic checks"),
    "target_branch": ("Target branch",),
    "integration_base_ref": ("Integration base ref",),
    "base_sha": ("Base SHA",),
    "allowed_operations": ("Allowed operations",),
}
_OPTIONAL_SECTIONS = {"allowed_operations"}
_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
_FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")
_REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,99}/[A-Za-z0-9_.-]{1,100}")


class _Diagnostics:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []
        self.truncated = False

    def add(self, code: str, section: str = "", *, index: int | None = None) -> None:
        # Never echo user prose, command text, tokens or filesystem error text.
        item: dict[str, Any] = {"code": code, "section": section}
        if index is not None:
            item["index"] = index
        if item in self.items:
            return
        if len(self.items) < MAX_DIAGNOSTICS:
            self.items.append(item)
        else:
            self.truncated = True


def _bounded_text(value: Any, diagnostics: _Diagnostics, section: str) -> str | None:
    if not isinstance(value, str):
        diagnostics.add("input_not_text", section)
        return None
    if len(value) > MAX_INPUT_BYTES:
        diagnostics.add("input_too_large", section)
        return None
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError:
        diagnostics.add("input_not_utf8", section)
        return None
    if size > MAX_INPUT_BYTES:
        diagnostics.add("input_too_large", section)
        return None
    if "\x00" in value or any(ord(c) < 32 and c not in "\n\r\t" for c in value):
        diagnostics.add("input_control_character", section)
        return None
    return path_a.normalize_issue_body(value)


def _sections(body: str, diagnostics: _Diagnostics) -> dict[str, tuple[str, str]]:
    """Bound each section before calling the existing fence-based parsers."""
    aliases = {name.casefold(): key for key, names in _SECTION_ALIASES.items() for name in names}
    lines = body.splitlines(keepends=True)
    headings: list[tuple[int, int, str]] = []
    fence: str | None = None
    for index, line in enumerate(lines):
        stripped = line.rstrip("\r\n")
        marker = _FENCE.match(stripped)
        if marker:
            run, suffix = marker.groups()
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not suffix.strip():
                fence = None
            continue
        match = _HEADING.match(stripped)
        if not match:
            continue
        level, title = len(match[1]), match[2]
        key = aliases.get(title.casefold())
        if fence is not None:
            # Path A's historical regex can see headings inside fences. Do not
            # call a body ready when it has two competing interpretations.
            if key:
                diagnostics.add("section_heading_inside_fence", key)
            continue
        headings.append((index, level, title))
    if fence is not None:
        diagnostics.add("unclosed_fence", "issue_body")

    found: dict[str, list[tuple[str, str]]] = {}
    for pos, (start, level, title) in enumerate(headings):
        key = aliases.get(title.casefold())
        if key is None:
            continue
        if level < 2:
            diagnostics.add("section_heading_level_invalid", key)
        stop = len(lines)
        for next_start, next_level, next_title in headings[pos + 1:]:
            if next_level <= level or next_title.casefold() in aliases:
                stop = next_start
                break
        found.setdefault(key, []).append((title, "".join(lines[start:stop])))
    result = {}
    for key in _SECTION_ALIASES:
        occurrences = found.get(key, [])
        if not occurrences:
            if key not in _OPTIONAL_SECTIONS:
                diagnostics.add("issue_missing_section", key)
        elif len(occurrences) != 1:
            diagnostics.add("issue_duplicate_section", key)
        else:
            result[key] = occurrences[0]
    return result


def _block(section: tuple[str, str], diagnostics: _Diagnostics, key: str) -> str | None:
    title, text = section
    blocks = path_a._text_blocks(text)
    markers = [line for line in text.splitlines() if _FENCE.match(line)]
    canonical = (
        len(markers) == 2
        and re.fullmatch(r"```(?:text)?[ \t]*", markers[0], re.IGNORECASE)
        and markers[1] == "```"
    )
    if len(blocks) != 1 or not canonical:
        diagnostics.add("section_requires_one_text_block", key)
        return None
    try:
        value = path_a._section_fenced_block(text, title)
    except path_a.PathAGateError as exc:
        diagnostics.add(exc.code, key)
        return None
    if not value.strip():
        diagnostics.add("issue_empty_section", key)
        return None
    return value


def _safe_ref(value: str) -> bool:
    if not value or len(value) > 200 or value in {"@", "HEAD"}:
        return False
    if value.startswith(("-", "/", "refs/")) or value.endswith(("/", ".")):
        return False
    if ".." in value or "@{" in value or re.search(r"[\x00-\x20\x7f~^:?*\[\\]", value):
        return False
    return all(part and not part.startswith(".") and not part.endswith(".lock") for part in value.split("/"))


def _literal_path(value: str) -> bool:
    return bool(
        value and len(value) <= MAX_PATH_LENGTH
        and not value.startswith(("/", "-"))
        and not re.match(r"^[A-Za-z]:", value)
        and not any(c in value for c in "\\:*?[]\x00")
        and not any(ord(c) < 32 or ord(c) == 127 for c in value)
        and all(
            part not in {"", ".", ".."}
            and part.casefold() != ".git"
            and not part.endswith((" ", "."))
            for part in value.split("/")
        )
    )


def preflight_work_item(
    issue_body: str, *, repository: str, observed_base_sha: str | None = None,
    occupied_paths: Sequence[str] = (), pr_body: str | None = None,
    issue_number: int | None = None, observed_head_sha: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Aggregate static R1 candidate errors without executing or authorizing.

    Caller-supplied base/head/occupied paths are observations, NOT live verified
    facts. Literal paths are required for a ready result; glob scopes must be
    expanded and reviewed because this offline check cannot prove their future
    R1 risk coverage. Omitting repo_root does not claim test targets exist.
    """
    diagnostics = _Diagnostics()
    body = _bounded_text(issue_body, diagnostics, "issue_body")
    repository_valid = isinstance(repository, str) and bool(_REPOSITORY.fullmatch(repository))
    if repository_valid:
        repository_valid = repository.split("/")[1] not in {".", ".."}
    if not repository_valid:
        diagnostics.add("repository_invalid", "repository")
    if issue_number is not None and (type(issue_number) is not int or issue_number <= 0):
        diagnostics.add("issue_number_invalid", "issue_number")
    for key, value in (("observed_base_sha", observed_base_sha), ("observed_head_sha", observed_head_sha)):
        if value is not None and (not isinstance(value, str) or not path_a.SHA_RE.fullmatch(value)):
            diagnostics.add("observed_sha_invalid", key)

    root_valid = repo_root is None or isinstance(repo_root, Path)
    if not root_valid:
        diagnostics.add("repo_root_invalid", "repo_root")
    test_targets_present = False
    fields: dict[str, str] = {}
    paths: tuple[str, ...] = ()
    selected_checks: list[str] = []
    if body is not None:
        sections = _sections(body, diagnostics)
        for key in ("specification", "acceptance"):
            if key in sections:
                prose = sections[key][1].split("\n", 1)[-1].strip()
                if not prose or prose.casefold() in {"_no response_", "n/a", "none", "tbd"}:
                    diagnostics.add("issue_empty_section", key)
        for key in ("forbidden_operations", "checks", "target_branch", "integration_base_ref", "base_sha"):
            if key not in sections:
                continue
            value = _block(sections[key], diagnostics, key)
            if value is None:
                continue
            if key in {"target_branch", "integration_base_ref", "base_sha"}:
                if len(value.strip().splitlines()) != 1:
                    diagnostics.add("section_requires_scalar", key)
                else:
                    fields[key] = value.strip()
        if "checks" in sections:
            try:
                # Isolated sections prevent a missing fence from consuming the
                # next section. The existing forbidden-token policy is reused.
                path_a._validate_issue_commands(sections["checks"][1])
            except path_a.PathAGateError as exc:
                diagnostics.add(exc.code, "checks")
        if "allowed_operations" in sections:
            _block(sections["allowed_operations"], diagnostics, "allowed_operations")
        try:
            path_a._validate_issue_commands(body)
        except path_a.PathAGateError as exc:
            diagnostics.add(exc.code, "checks")
        try:
            path_a.parse_snapshot(body)
        except path_a.PathAGateError as exc:
            if exc.code != "snapshot_missing":
                diagnostics.add("candidate_contains_snapshot", "issue_body")
        else:
            diagnostics.add("candidate_contains_snapshot", "issue_body")

        if "allowed_paths" in sections and _block(sections["allowed_paths"], diagnostics, "allowed_paths") is not None:
            try:
                paths = path_a.parse_allowed_paths(sections["allowed_paths"][1])
            except path_a.PathAGateError as exc:
                diagnostics.add(exc.code, "allowed_paths")
            if len(paths) > MAX_PATHS:
                diagnostics.add("too_many_allowed_paths", "allowed_paths")
                paths = ()
            seen: set[str] = set()
            for index, path in enumerate(paths):
                if any(c in path for c in "*?[]"):
                    diagnostics.add("path_scope_requires_expansion", "allowed_paths", index=index)
                elif not _literal_path(path):
                    diagnostics.add("path_not_portable_literal", "allowed_paths", index=index)
                if path.casefold() in seen:
                    diagnostics.add("duplicate_allowed_path", "allowed_paths", index=index)
                seen.add(path.casefold())
                risk = path_a._minimum_path_risk(path)
                if risk is not None:
                    diagnostics.add("path_risk_exceeds_r1", "allowed_paths", index=index)
            if paths and all(_literal_path(path) for path in paths):
                try:
                    selection = path_a.select_task_checks(
                        paths, repo_root=repo_root if root_valid else None,
                    )
                    selected_checks = list(selection["commands"])
                    test_targets_present = bool(repo_root is not None and root_valid and selected_checks)
                except path_a.PathAGateError as exc:
                    diagnostics.add(exc.code, "selected_checks")

    for key in ("target_branch", "integration_base_ref"):
        if key in fields and not _safe_ref(fields[key]):
            diagnostics.add("branch_ref_invalid", key)
    if fields.get("target_branch") == "main" or (
        fields.get("target_branch") and fields.get("target_branch") == fields.get("integration_base_ref")
    ):
        diagnostics.add("work_branch_is_integration_branch", "target_branch")
    if "base_sha" in fields and not path_a.SHA_RE.fullmatch(fields["base_sha"]):
        diagnostics.add("base_sha_invalid", "base_sha")
    if observed_base_sha is not None and fields.get("base_sha") != observed_base_sha:
        diagnostics.add("observed_base_mismatch", "base_sha")

    if not isinstance(occupied_paths, (list, tuple)) or len(occupied_paths) > MAX_OCCUPIED_PATHS:
        diagnostics.add("occupied_paths_invalid", "occupied_paths")
    else:
        for index, occupied in enumerate(occupied_paths):
            if not isinstance(occupied, str) or not _literal_path(occupied):
                diagnostics.add("occupied_path_invalid", "occupied_paths", index=index)
            elif any(path_a._path_matches(occupied.casefold(), p.casefold()) for p in paths):
                diagnostics.add("occupied_path_overlap", "occupied_paths", index=index)

    snapshot_checked = False
    if pr_body is not None:
        draft = _bounded_text(pr_body, diagnostics, "pr_body")
        if draft is not None:
            try:
                snapshot = path_a.parse_snapshot(draft)
            except path_a.PathAGateError as exc:
                diagnostics.add(exc.code, "pr_body")
            else:
                expected = {
                    "repository": repository,
                    "body_digest_sha256": path_a.issue_body_digest(body) if body is not None else None,
                    "target_branch": fields.get("target_branch"),
                    "integration_base_ref": fields.get("integration_base_ref"),
                    "base_sha": fields.get("base_sha"),
                }
                if issue_number is not None:
                    expected["issue_number"] = issue_number
                if observed_head_sha is not None:
                    expected["exact_head_sha"] = observed_head_sha
                for key, value in expected.items():
                    if getattr(snapshot, key) != value:
                        diagnostics.add("snapshot_binding_mismatch", key)
                snapshot_checked = True

    return {
        "schema_version": 1,
        "kind": "work_item_preflight",
        "readiness": "NEEDS_REVISION" if diagnostics.items else "APPROVAL_READY",
        "body_digest_sha256": path_a.issue_body_digest(body) if body is not None else None,
        "diagnostics": diagnostics.items,
        "diagnostics_truncated": diagnostics.truncated,
        "allowed_path_count": len(paths),
        "selected_checks": selected_checks,
        "snapshot_parsed": snapshot_checked,
        "test_targets_present": test_targets_present,
        "live_state_verified": False,
        "commands_executed": False,
        "approval_granted": False,
        "implementation_authority": False,
        "ready_authority": False,
        "merge_authority": False,
        "product_accepted": False,
        "implementation_complete": False,
        "requires_owner_review": True,
        "limitations": [
            "Static R1 candidate diagnostics only; semantic sufficiency is not established.",
            "Live approval provenance, revision, ownership and exact Git identity still require verification.",
            "Declared checks are not executed; functional acceptance and delivery are not observed.",
        ],
    }


def _read_input(path: Path) -> str:
    """Read bounded UTF-8 from a stable regular-file handle, not a FIFO/device."""
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_INPUT_BYTES:
        raise ValueError("input_file_not_bounded_regular")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        current = os.fstat(descriptor)
        if not stat.S_ISREG(current.st_mode) or (before.st_dev, before.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("input_file_changed")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        after = os.fstat(descriptor)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("input_too_large")
        if (current.st_size, current.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("input_file_changed")
        return raw.decode("utf-8", errors="strict")
    finally:
        os.close(descriptor)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue-body-file", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-body-file", type=Path)
    parser.add_argument("--issue-number", type=int)
    parser.add_argument("--observed-base-sha")
    parser.add_argument("--observed-head-sha")
    parser.add_argument("--occupied-path", action="append", default=[])
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args(argv)
    try:
        body = _read_input(args.issue_body_file)
        draft = _read_input(args.pr_body_file) if args.pr_body_file is not None else None
    except (OSError, UnicodeError, ValueError):
        result = preflight_work_item("", repository=args.repository)
        result["diagnostics"] = [{"code": "input_file_unreadable_or_invalid", "section": "input_file"}]
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 2
    result = preflight_work_item(
        body, repository=args.repository, observed_base_sha=args.observed_base_sha,
        occupied_paths=args.occupied_path, pr_body=draft, issue_number=args.issue_number,
        observed_head_sha=args.observed_head_sha, repo_root=args.repo_root,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["readiness"] == "APPROVAL_READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
