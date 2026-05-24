from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "version",
    "status",
    "scope",
    "owner",
    "last_reviewed",
}
ALLOWED_STATUS = {"active", "deprecated", "archived"}
ALLOWED_SCOPE = {
    "generic_workflow",
    "engineering_branch",
    "reverse_solving",
    "sample_profile",
    "tool_usage",
}
NEGATION_MARKERS = (
    "do not",
    "don't",
    "must not",
    "should not",
    "not ",
    "only when",
    "unless",
    "no default",
    "not by default",
)
LONG_HEX_RE = re.compile(r"\b[0-9a-fA-F]{16,}\b")
RUN_NAME_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_-]*_20\d{6,}\b")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _json_error(message: str) -> dict[str, Any]:
    return {"status": "failed", "skills_checked": 0, "errors": [message], "warnings": []}


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_scalar(value: str) -> Any:
    value = _strip_quotes(value)
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if re.fullmatch(r"\d+", value):
        return int(value)
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return None, text

    raw = lines[1:end_index]
    body = "\n".join(lines[end_index + 1 :])
    parsed: dict[str, Any] = {}
    current_key: str | None = None
    current_child: str | None = None

    for line in raw:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            current_child = None
            parsed[key] = {} if value == "" else _parse_scalar(value)
            continue
        if current_key is None:
            continue
        if line.startswith("  ") and not line.startswith("    ") and ":" in line:
            if not isinstance(parsed.get(current_key), dict):
                parsed[current_key] = {}
            key, value = line.strip().split(":", 1)
            key = key.strip()
            value = value.strip()
            current_child = key
            parsed[current_key][key] = [] if value == "" else _parse_scalar(value)
            continue
        if line.startswith("    - ") and current_child and isinstance(parsed.get(current_key), dict):
            values = parsed[current_key].setdefault(current_child, [])
            if isinstance(values, list):
                values.append(_parse_scalar(line.strip()[2:].strip()))
            continue
        if line.startswith("  - "):
            values = parsed.setdefault(current_key, [])
            if isinstance(values, list):
                values.append(_parse_scalar(line.strip()[2:].strip()))

    return parsed, body


def _is_negated(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in NEGATION_MARKERS)


def _content_lines(body: str) -> list[tuple[int, str]]:
    return [(index, line.strip()) for index, line in enumerate(body.splitlines(), start=1) if line.strip()]


def _check_forbidden_defaults(skill_name: str, body: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for line_no, line in _content_lines(body):
        lowered = line.lower()
        negated = _is_negated(line)
        location = f"{skill_name}:body:{line_no}"

        if "project_progress_log" in lowered:
            if not negated and any(word in lowered for word in ("read", "tail", "default", "start")):
                errors.append(f"{location}: active skill defaults to PROJECT_PROGRESS_LOG.txt")
            elif not negated and "project_progress_log.txt" in lowered:
                warnings.append(f"{location}: ambiguous PROJECT_PROGRESS_LOG.txt reference")

        if "solve_reports" in lowered:
            full_scan = any(phrase in lowered for phrase in ("scan full", "full solve_reports", "entire solve_reports"))
            newest_harness = "newest" in lowered and "harness_runs" in lowered
            direct_default = "inspect" in lowered and "harness_runs" in lowered and "default" in lowered
            if not negated and (full_scan or newest_harness or direct_default):
                errors.append(f"{location}: active skill defaults to broad solve_reports read")

        probe_default = any(
            pattern in lowered
            for pattern in (
                "run runtime probe",
                "run runtime probes",
                "run the runtime probe",
                "run the runtime probes",
                "run breakpoint probe",
                "run breakpoint probes",
                "run the breakpoint probe",
                "run the breakpoint probes",
                "runtime probe by default",
                "runtime probes by default",
                "breakpoint probe by default",
                "breakpoint probes by default",
            )
        )
        if probe_default and not negated:
            errors.append(f"{location}: active skill defaults to runtime probe")

    return errors, warnings


def _check_sample_dynamic_facts(skill_name: str, body: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for line_no, line in _content_lines(body):
        lowered = line.lower()
        if _is_negated(line):
            continue
        location = f"{skill_name}:body:{line_no}"
        if LONG_HEX_RE.search(line):
            errors.append(f"{location}: sample profile contains long hex dynamic fact")
        if RUN_NAME_RE.search(line):
            errors.append(f"{location}: sample profile contains dated run name")
        if "solve_reports" in lowered and ("\\" in line or "/" in line) and any(suffix in lowered for suffix in (".json", ".log", ".txt")):
            errors.append(f"{location}: sample profile contains direct solve_reports artifact path")
        elif "solve_reports" in lowered and not _is_negated(line):
            warnings.append(f"{location}: sample profile references solve_reports; verify it is a guardrail")
    return errors, warnings


def audit_skills(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    registry_path = root / ".codex-skills" / "registry.json"
    errors: list[str] = []
    warnings: list[str] = []
    skills_checked = 0

    if not registry_path.exists():
        return _json_error(f"registry not found: {registry_path}")

    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _json_error(f"registry is invalid JSON: {exc}")

    if "schema_version" not in registry:
        errors.append("registry missing schema_version")
    skills = registry.get("skills")
    if not isinstance(skills, dict):
        errors.append("registry skills must be an object")
        skills = {}

    for skill_name, entry in sorted(skills.items()):
        if not isinstance(entry, dict):
            errors.append(f"{skill_name}: registry entry must be an object")
            continue
        rel_path = entry.get("path")
        if not isinstance(rel_path, str) or not rel_path:
            errors.append(f"{skill_name}: registry entry missing path")
            continue
        skill_path = root / rel_path
        if not skill_path.exists():
            errors.append(f"{skill_name}: registered path does not exist: {rel_path}")
            continue

        text = skill_path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)
        if frontmatter is None:
            errors.append(f"{skill_name}: SKILL.md missing frontmatter")
            continue
        skills_checked += 1

        missing = sorted(REQUIRED_FRONTMATTER_FIELDS - set(frontmatter))
        if missing:
            errors.append(f"{skill_name}: frontmatter missing required fields: {', '.join(missing)}")

        if frontmatter.get("name") != skill_name:
            errors.append(f"{skill_name}: frontmatter name does not match registry key")
        if frontmatter.get("status") not in ALLOWED_STATUS:
            errors.append(f"{skill_name}: invalid status {frontmatter.get('status')!r}")
        if frontmatter.get("scope") not in ALLOWED_SCOPE:
            errors.append(f"{skill_name}: invalid scope {frontmatter.get('scope')!r}")

        for field in ("version", "status", "scope"):
            if field in entry and frontmatter.get(field) != entry.get(field):
                errors.append(
                    f"{skill_name}: frontmatter {field}={frontmatter.get(field)!r} "
                    f"does not match registry {entry.get(field)!r}"
                )

        if entry.get("status") == "active":
            default_errors, default_warnings = _check_forbidden_defaults(skill_name, body)
            errors.extend(default_errors)
            warnings.extend(default_warnings)
            if entry.get("scope") == "sample_profile":
                dynamic_errors, dynamic_warnings = _check_sample_dynamic_facts(skill_name, body)
                errors.extend(dynamic_errors)
                warnings.extend(dynamic_warnings)

    return {
        "status": "failed" if errors else "passed",
        "skills_checked": skills_checked,
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit repo-tracked Codex skills.")
    parser.add_argument("--repo-root", default="", help="Repository root. Defaults to this script's repo.")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else None
    result = audit_skills(repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
