"""Provider-free contracts for compact, progressively disclosed agent instructions."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = {
    "AGENTS.md": 12_000,
    ".codex-skills/reverse-agent-iteration/SKILL.md": 2_000,
    ".codex-skills/samplereverse-frontier/SKILL.md": 1_300,
    "docs/prompts/codex_execution_prompt.md": 1_800,
    "docs/prompts/project_workspace_prompt.md": 1_800,
    "docs/prompts/README.md": 2_200,
}
REFERENCES = (
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/references/project-state-round.md",
    ".codex-skills/samplereverse-frontier/references/sample-guardrails.md",
    "docs/prompts/legacy-project-state-reference.md",
)
LINK_RE = re.compile(r"\[[^\]\n]+\]\(([^)\s]+)\)")
DRIVE_RE = re.compile(r"\b[A-Za-z]:[\\/]")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


@pytest.mark.parametrize("relative,budget", ENTRIES.items())
def test_entry_footprint_is_bounded(relative: str, budget: int) -> None:
    assert 0 < len((ROOT / relative).read_bytes()) <= budget


@pytest.mark.parametrize("relative", (*ENTRIES, *REFERENCES))
def test_local_conditional_links_resolve(relative: str) -> None:
    source = ROOT / relative
    for target in LINK_RE.findall(source.read_text(encoding="utf-8")):
        if target.startswith(("https://", "http://")):
            continue
        file_part, _, anchor = target.partition("#")
        resolved = (source.parent / file_part).resolve() if file_part else source.resolve()
        assert resolved.is_relative_to(ROOT.resolve()) and resolved.is_file(), target
        if anchor:
            headings = re.findall(r"^#+\s+(.+)$", resolved.read_text(encoding="utf-8"), re.M)
            slugs = {re.sub(r"[^\w\s-]", "", h.lower()).replace(" ", "-") for h in headings}
            assert anchor in slugs, target


def test_skill_entries_are_precise_and_registry_compatible() -> None:
    registry = json.loads(read(".codex-skills/registry.json"))["skills"]
    expected = {
        "reverse-agent-iteration": "generic_workflow",
        "samplereverse-frontier": "sample_profile",
    }
    for name, scope in expected.items():
        text = read(f".codex-skills/{name}/SKILL.md")
        front = text.split("---", 2)[1]
        values = {}
        for line in front.splitlines():
            if line.strip():
                key, _, value = line.partition(":")
                values[key.strip()] = value.strip().strip('"')
        assert values["name"] == name
        assert values["description"] and len(values["description"]) <= 180
        assert "explicitly scoped" in values["description"].lower()
        assert "not for" in values["description"].lower()
        assert values["scope"] == registry[name]["scope"] == scope
        assert int(values["version"]) == registry[name]["version"] == 2


def test_authority_paths_are_distinct_and_current() -> None:
    text = read("AGENTS.md")
    path_a = text.split("### Path A", 1)[1].split("### Path B", 1)[0]
    path_b = text.split("### Path B", 1)[1].split("## Risk tiers", 1)[0]
    assert "CANDIDATE, not execution authority" in path_a
    assert "r1-approved" in path_a and "body_digest_sha256" in path_a
    assert "material" in path_a and "reapproval" in path_a
    assert "Ordinary R0/R1 work does not use" in path_a
    assert "APPROVED" in path_b and "PRE_EXECUTION_AUTHORIZED" in path_b
    assert "immutable" in path_b and "cannot authorize R2/R3" in path_b
    assert "comments are never authority" in text


@pytest.mark.parametrize("relative", ("docs/prompts/codex_execution_prompt.md", "docs/prompts/project_workspace_prompt.md"))
def test_prompts_are_locators_not_fixed_local_recipes(relative: str) -> None:
    text = read(relative)
    assert "dddd2024/Nerelan" in text and "Fresh-read" in text
    assert "locator" in text and "Path A" in text and "Path B" in text
    assert "Execution surface:" in text and "Outcome:" in text
    assert not DRIVE_RE.search(text)
    assert "sole execution authority" not in text and "Set-Location" not in text


def test_legacy_and_sample_details_are_opt_in() -> None:
    generic = read(".codex-skills/reverse-agent-iteration/SKILL.md")
    sample = read(".codex-skills/samplereverse-frontier/SKILL.md")
    project_ref = read(REFERENCES[1])
    sample_ref = read(REFERENCES[2])
    assert "Only when the active task explicitly uses" in generic
    assert "no mandatory seven-file replay" in project_ref
    assert "Do not scan full `solve_reports/`" in project_ref
    assert "Ordinary Nerelan engineering must not activate sample solving" in sample
    assert "does not authorize binary execution" in sample
    assert "CompareAwareSearchStrategy" not in sample and "CompareAwareSearchStrategy" in sample_ref
    assert "Do not run the Base64/RC4 breakpoint probe by default" in sample_ref


def test_completion_and_landing_boundaries_remain_fail_closed() -> None:
    text = read("AGENTS.md")
    for token in (
        "retry budget",
        "failed mandatory focused tests",
        "independent exact-head",
        "PUBLICATION_READY",
        "agent-initiated",
        "automation-initiated",
        "R1 final-acceptance carve-out",
        "A published Draft is not a mainline landing",
    ):
        assert token in text
    assert "Missing independent exact-head acceptance blocks landing, not already-authorized implementation" in text
    assert "Do not reset, clean, stash, restore, delete or bulk-stage" in text
    assert "do not label unverified work complete" in text
