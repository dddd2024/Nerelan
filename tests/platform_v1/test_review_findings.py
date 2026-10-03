"""Seeded, provider-free review-contract evidence, not live review evaluations."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import json
import os
import subprocess

import pytest

from reverse_agent.platform_v1.review_findings import (
    FindingGroup, ReviewContractError, ReviewFeedback, ReviewFinding, ReviewTarget,
    deduplicate_review_findings, feedback_for_current_target, normalize_review_finding,
    normalize_review_target, reconcile_review_findings, record_review_feedback,
)


FLAGS = ("evidence_verified", "independent_acceptance", "execution_authorized",
         "repair_authorized", "landing_authorized")


def target_data(**changes):
    data = {"forge": "github", "repository": "fixture/review", "change_request": "PR:12",
            "base_ref": "main", "base_sha": "a" * 40, "base_tree_sha": "b" * 40,
            "head_ref": "review-candidate", "head_sha": "c" * 40, "head_tree_sha": "d" * 40,
            "patch_sha256": "e" * 64, "paths": ["src/one.py", "src/two.py"],
            "excluded_paths": ["src/two.py"], "profile": "correctness",
            "observations_sha256": "f" * 64}
    data.update(changes)
    return data


def finding_data(**changes):
    data = {"rule_id": "fixture.return-type", "category": "correctness", "severity": "high",
            "confidence": "high", "path": "src/one.py", "start_line": 3, "end_line": 4,
            "symbol": "calculate", "summary": "Seeded return type differs from its caller contract.",
            "source": "deterministic", "evidence_refs": ["1" * 64]}
    data.update(changes)
    return data


def feedback(finding, target, **changes):
    data = {"status": "NOT_REPRODUCIBLE", "reason": "Seeded library evidence contradicts the inference.",
            "evidence_refs": ["2" * 64], "adjudicator_ref": "fixture:reviewer",
            "observed_at": "2026-10-03T16:00:00+08:00"}
    data.update(changes)
    return record_review_feedback(finding, target, **data)


def test_target_is_canonical_immutable_and_does_not_mutate_input():
    raw = target_data()
    before = deepcopy(raw)
    target = normalize_review_target(raw)
    permuted = deepcopy(raw)
    permuted["paths"].reverse()
    assert normalize_review_target(permuted) == target
    assert normalize_review_target(target.document) == target
    assert raw == before
    raw["paths"].clear()
    doc = target.document
    doc["paths"].clear()
    assert target.reviewed_paths == frozenset({"src/one.py"})
    with pytest.raises(FrozenInstanceError):
        target._json = "{}"


@pytest.mark.parametrize("field", ["repository", "forge", "change_request", "base_ref", "base_sha",
    "base_tree_sha", "head_ref", "head_sha", "head_tree_sha", "patch_sha256", "paths",
    "excluded_paths", "profile", "observations_sha256"])
def test_each_target_identity_field_changes_generation(field):
    original = normalize_review_target(target_data())
    raw = target_data()
    if field == "paths":
        raw[field].append("src/three.py")
    elif field == "excluded_paths":
        raw[field] = []
    elif field.endswith("sha256"):
        raw[field] = "3" * 64
    elif field.endswith("sha"):
        raw[field] = "3" * 40
    else:
        raw[field] = "different"
    assert normalize_review_target(raw).digest != original.digest


@pytest.mark.parametrize("changes", [
    {"base_sha": "A" * 40}, {"head_sha": "not-an-oid"}, {"head_tree_sha": "a" * 64},
    {"patch_sha256": "a" * 40}, {"paths": []}, {"excluded_paths": ["other.py"]},
    {"excluded_paths": ["src/one.py", "src/two.py"]},
    {"paths": ["src/one.py", "src/one.py"]}, {"paths": ["src/**"]},
    {"paths": ["../src/one.py"]}, {"paths": ["/src/one.py"]},
    {"paths": ["C:/src/one.py"]}, {"paths": ["src\\one.py"]},
    {"paths": ["src//one.py"]}, {"profile": chr(0xd800)}, {"profile": "x\nline"},
    {"observations_sha256": None}, {"execution_authorized": True},
    {"private_chain_of_thought": "untrusted extra field"},
])
def test_invalid_target_claims_fail_without_echoing_payload(changes):
    with pytest.raises(ReviewContractError) as error:
        normalize_review_target(target_data(**changes))
    assert str(error.value).startswith("review_")
    assert "untrusted extra" not in str(error.value)


@pytest.mark.parametrize("field", FLAGS)
def test_input_cannot_inject_authority_and_output_flags_cannot_be_changed(field):
    raw = target_data(**{field: True})
    with pytest.raises(ReviewContractError):
        normalize_review_target(raw)
    target = normalize_review_target(target_data())
    finding = normalize_review_finding(target, finding_data())
    disposition = feedback(finding, target)
    states = reconcile_review_findings([finding], target)
    group = deduplicate_review_findings([finding])[0]
    for value in (target, finding, disposition, states[0], group):
        assert getattr(value, field) is False
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, True)
    for value in (target, finding, disposition):
        assert value.to_record()[field] is False
    with pytest.raises(ReviewContractError):
        normalize_review_finding(target, finding_data(**{field: True}))


@pytest.mark.parametrize("changes", [
    {"path": "src/two.py"}, {"path": "src/one.py/child"}, {"path": "src/one?.py"},
    {"start_line": True}, {"start_line": 0}, {"end_line": 2}, {"end_line": 10_000_001},
    {"severity": "proven"}, {"confidence": "confirmed"}, {"source": "trusted-because-model-said-so"},
    {"summary": "x" * 2001}, {"evidence_refs": []}, {"evidence_refs": ["raw-output"]},
    {"finding_id": "1" * 64}, {"summary": chr(0xd800)}, {"rule_id": "unsafe rule"},
])
def test_finding_scope_identity_and_data_are_bounded(changes):
    target = normalize_review_target(target_data())
    with pytest.raises(ReviewContractError):
        normalize_review_finding(target, finding_data(**changes))


@pytest.mark.parametrize("summary,credential", [
    ("api_key=fixture-secret-value", "fixture-secret-value"),
    ("Authorization: Bearer fixture-sensitive-value", "fixture-sensitive-value"),
    ("bearer abcdefghijklmnopqrstuvwxyz", "abcdefghijklmnopqrstuvwxyz"),
])
def test_shared_secret_detector_discards_whole_matching_summary_and_feedback(summary, credential):
    target = normalize_review_target(target_data())
    finding = normalize_review_finding(target, finding_data(summary=summary))
    disposition = feedback(finding, target, reason=summary)
    assert finding.document["summary"] == disposition.document["reason"] == "[REDACTED]"
    assert credential not in json.dumps([finding.to_record(), disposition.to_record()])


def test_explicit_duplicate_identity_prefers_analyzer_preserves_contributors_and_is_order_stable():
    target = normalize_review_target(target_data())
    analyzer = normalize_review_finding(target, finding_data())
    model = normalize_review_finding(target, finding_data(source="model", summary="Different prose, same explicit rule.",
                                                          evidence_refs=["2" * 64]))
    before = deepcopy(model.document)
    assert analyzer.finding_id == model.finding_id
    first = deduplicate_review_findings([model, analyzer, model])
    second = deduplicate_review_findings([analyzer, model])
    assert first == second and len(first) == 1
    assert first[0].representative == analyzer
    assert len(first[0].contributions) == 2
    assert first[0].document["sources"] == ["deterministic", "model"]
    assert first[0].document["evidence_refs"] == ["1" * 64, "2" * 64]
    assert model.document == before


def test_similar_prose_is_not_semantically_deduped_or_promoted_to_verified():
    target = normalize_review_target(target_data())
    one = normalize_review_finding(target, finding_data(source="model"))
    two = normalize_review_finding(target, finding_data(source="model", rule_id="fixture.different-rule"))
    assert len(deduplicate_review_findings([one, two])) == 2
    assert not one.evidence_verified
    assert deduplicate_review_findings([]) == ()


def test_duplicate_matching_requires_same_exact_target_and_constructor_ids_cannot_be_forged():
    target = normalize_review_target(target_data())
    new_target = normalize_review_target(target_data(head_sha="9" * 40))
    one = normalize_review_finding(target, finding_data())
    two = normalize_review_finding(new_target, finding_data())
    with pytest.raises(ReviewContractError, match="generation_mismatch"):
        deduplicate_review_findings([one, two])
    forged = one.document
    forged["target_digest"] = new_target.digest
    with pytest.raises(ReviewContractError, match="identity_mismatch"):
        ReviewFinding(target, json.dumps(forged, sort_keys=True, separators=(",", ":")))
    with pytest.raises(ReviewContractError, match="group_identity"):
        FindingGroup(one, (two,))


def test_new_head_makes_findings_and_feedback_stale_without_automatically_marking_fixed():
    target = normalize_review_target(target_data())
    finding = normalize_review_finding(target, finding_data(source="model"))
    before = deepcopy(finding.document)
    disposition = feedback(finding, target)
    assert disposition.document["observed_at"] == "2026-10-03T08:00:00.000000Z"
    assert disposition.document["status"] == "NOT_REPRODUCIBLE"
    assert feedback_for_current_target(disposition, target) == disposition
    assert reconcile_review_findings([finding], target)[0].status == "OPEN"
    new_target = normalize_review_target(target_data(head_sha="9" * 40))
    states = reconcile_review_findings([finding], new_target)
    assert states[0].finding == finding
    assert states[0].status == "STALE_AFTER_TARGET_CHANGE"
    assert feedback_for_current_target(disposition, new_target) is None
    with pytest.raises(ReviewContractError, match="stale_target"):
        feedback(finding, new_target)
    assert finding.document == before
    assert reconcile_review_findings([], new_target) == ()


@pytest.mark.parametrize("changes", [
    {"status": "FIXED_IN_HEAD:unverified"}, {"status": "ACCEPTED"},
    {"status": "EXECUTION_AUTHORIZED"}, {"reason": ""}, {"evidence_refs": []},
    {"observed_at": "2026-10-03T08:00:00"}, {"observed_at": "bad-time"},
    {"adjudicator_ref": ""},
])
def test_feedback_cannot_forge_fix_acceptance_authority_or_omit_evidence(changes):
    target = normalize_review_target(target_data())
    finding = normalize_review_finding(target, finding_data())
    with pytest.raises(ReviewContractError):
        feedback(finding, target, **changes)


def test_feedback_constructor_rejects_mismatched_target_or_hidden_authority_field():
    target = normalize_review_target(target_data())
    finding = normalize_review_finding(target, finding_data())
    disposition = feedback(finding, target)
    for changes in ({"target_digest": "9" * 64}, {"execution_authorized": True}):
        forged = disposition.document
        forged.update(changes)
        with pytest.raises(ReviewContractError):
            ReviewFeedback(finding, json.dumps(forged, sort_keys=True, separators=(",", ":")))


@pytest.mark.parametrize("algorithm", ["sha1", "sha256"])
def test_real_fixture_git_identity_and_patch_are_bound_but_not_claimed_verified(tmp_path, algorithm):
    hooks = tmp_path / "empty-hooks"
    hooks.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    # These commands operate only on this disposable fixture; no network/hooks.
    def git(*args):
        result = subprocess.run(["git", "-c", f"core.hooksPath={hooks}", "-c", "core.autocrlf=false",
            "-c", "user.name=Review Fixture", "-c", "user.email=fixture@localhost", *args],
            cwd=tmp_path, env=env, capture_output=True, check=True, timeout=20)
        return result.stdout
    git("init", f"--object-format={algorithm}", "--initial-branch=main")
    source = tmp_path / "src"
    source.mkdir()
    (source / "one.py").write_bytes(b"def calculate():\n    return 1\n")
    git("add", "--", "src/one.py")
    git("commit", "-m", "fixture base")
    base = git("rev-parse", "HEAD").decode().strip()
    base_tree = git("rev-parse", "HEAD^{tree}").decode().strip()
    (source / "one.py").write_bytes(b"def calculate():\n    return 'wrong type'\n")
    git("add", "--", "src/one.py")
    git("commit", "-m", "fixture seeded defect")
    head = git("rev-parse", "HEAD").decode().strip()
    tree = git("rev-parse", "HEAD^{tree}").decode().strip()
    patch = git("diff", "--no-ext-diff", "--no-textconv", base, head, "--", "src/one.py")
    target = normalize_review_target(target_data(base_sha=base, base_tree_sha=base_tree,
        head_sha=head, head_tree_sha=tree, patch_sha256=hashlib.sha256(patch).hexdigest(),
        paths=["src/one.py"], excluded_paths=[]))
    assert len(target.document["head_sha"]) == (40 if algorithm == "sha1" else 64)
    assert not target.evidence_verified
    finding = normalize_review_finding(target, finding_data(start_line=2, end_line=2))
    assert finding.document["target_digest"] == target.digest
    assert finding.finding_id != normalize_review_finding(
        normalize_review_target(target_data()), finding_data(start_line=2, end_line=2)).finding_id
