from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Optional

import pytest

from reverse_agent.architecture.contracts import ExecutionEnvelope
from reverse_agent.architecture.risk import RiskTier, WorkflowRoute
from reverse_agent.architecture.risk_classifier import classify_risk


@dataclass(frozen=True)
class _StubPathRiskFloor:
    """Minimal duck-typed PathRiskFloor for testing the architecture layer.

    The architecture layer must not import from ``control_plane``; it accepts
    any object exposing ``risk_for_path(path) -> str | None``.
    """

    entries: tuple[tuple[str, str], ...]

    def risk_for_path(self, path: str) -> Optional[str]:
        normalized = path.replace("\\", "/").lstrip("./")
        for pattern, risk in self.entries:
            candidate = pattern.replace("\\", "/").lstrip("./")
            if self._matches(candidate, normalized):
                return risk
        return None

    @staticmethod
    def _matches(candidate: str, normalized: str) -> bool:
        # Strip leading "**/" - matches anything before the rest.
        leading_any = candidate.startswith("**/")
        if leading_any:
            candidate = candidate[3:]
        # Strip trailing "/**" - matches anything after the rest.
        trailing_any = candidate.endswith("/**")
        if trailing_any:
            candidate = candidate[:-3]
        candidate = candidate.strip("/")

        if leading_any and trailing_any:
            # **/foo/** -> path contains /foo/
            if not candidate:
                return True
            return (
                normalized == candidate
                or normalized.startswith(f"{candidate}/")
                or normalized.endswith(f"/{candidate}")
                or f"/{candidate}/" in f"/{normalized}/"
            )
        if leading_any:
            # **/foo     -> any path named foo at any depth
            # **/*.exe   -> any path ending with .ext
            if "*" in candidate or "?" in candidate:
                return fnmatch(normalized, candidate) or fnmatch(normalized, f"*/{candidate}")
            return normalized == candidate or normalized.endswith(f"/{candidate}")
        if trailing_any:
            # foo/**     -> prefix match
            return normalized == candidate or normalized.startswith(f"{candidate}/")
        return normalized == candidate or fnmatch(normalized, candidate)


@pytest.mark.parametrize(
    ("operations", "tier", "route"),
    [
        (("review",), RiskTier.R0, WorkflowRoute.STANDARD_PATH),
        (("source_edit", "unit_test"), RiskTier.R1, WorkflowRoute.STANDARD_PATH),
        (("workflow_change",), RiskTier.R2, WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED),
        (("unknown_binary_execution",), RiskTier.R3, WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED),
    ],
)
def test_representative_risk_classification(operations, tier, route) -> None:
    result = classify_risk(ExecutionEnvelope(operations, ("path",)))
    assert result.risk_tier is tier
    assert result.route is route


def test_conflicting_known_features_choose_highest_risk() -> None:
    result = classify_risk(ExecutionEnvelope(("review", "dependency_change", "debugger"), ("path",)))
    assert result.risk_tier is RiskTier.R3


@pytest.mark.parametrize("operations", [(), ("invented_operation",), ("review", "invented_operation")])
def test_missing_or_unknown_operations_block(operations) -> None:
    result = classify_risk(ExecutionEnvelope(operations, ("path",)))
    assert result.risk_tier is None
    assert result.route is WorkflowRoute.BLOCKED


# --- Phase D: path-aware risk floor ----------------------------------------


def test_path_risk_floor_promotes_workflow_path_to_r2() -> None:
    """A ``source_edit`` (R1) on a workflow file must reach R2.

    The caller cannot lower workflow, dependency, Decision, gate, secret,
    binary or destructive work by labeling it as a generic source edit.
    """

    floor = _StubPathRiskFloor(((".github/workflows/**", "R2"),))
    envelope = ExecutionEnvelope(("source_edit",), (".github/workflows/ci.yml",))
    result = classify_risk(envelope, path_risk_floor=floor)
    assert result.risk_tier is RiskTier.R2
    assert result.route is WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED


def test_path_risk_floor_promotes_secrets_path_to_r3() -> None:
    """A ``source_edit`` (R1) on a secrets path must reach R3."""

    floor = _StubPathRiskFloor((("**/secrets/**", "R3"),))
    envelope = ExecutionEnvelope(("source_edit",), ("config/secrets/api.key",))
    result = classify_risk(envelope, path_risk_floor=floor)
    assert result.risk_tier is RiskTier.R3


def test_path_risk_floor_promotes_binary_path_to_r3() -> None:
    floor = _StubPathRiskFloor((("**/*.exe", "R3"),))
    envelope = ExecutionEnvelope(("source_edit",), ("tools/patcher.exe",))
    result = classify_risk(envelope, path_risk_floor=floor)
    assert result.risk_tier is RiskTier.R3


def test_operation_under_reporting_cannot_reduce_risk() -> None:
    """If the path requires R2 but operations are missing, classification must block.

    Operation under-reporting cannot lower the risk floor; unknown operations
    must block regardless of what the path floor says.
    """

    floor = _StubPathRiskFloor(((".github/workflows/**", "R2"),))
    envelope = ExecutionEnvelope(("invented_operation",), (".github/workflows/ci.yml",))
    result = classify_risk(envelope, path_risk_floor=floor)
    assert result.risk_tier is None
    assert result.route is WorkflowRoute.BLOCKED


def test_unknown_sensitive_path_blocks_when_floor_present() -> None:
    """An unknown path combined with a path floor must still use operation risk.

    If neither the operations nor the path floor promote the risk, the
    classification falls back to the operation-based tier. An unknown path
    alone must not block; an unknown operation still blocks.
    """

    floor = _StubPathRiskFloor(((".github/workflows/**", "R2"),))
    envelope = ExecutionEnvelope(("source_edit",), ("docs/unknown.md",))
    result = classify_risk(envelope, path_risk_floor=floor)
    assert result.risk_tier is RiskTier.R1
    assert result.route is WorkflowRoute.STANDARD_PATH


def test_capability_flag_risk_promotes_to_r3() -> None:
    """A denied capability flag contributes R3 risk via max()."""

    envelope = ExecutionEnvelope(("source_edit",), ("reverse_agent/example.py",))
    result = classify_risk(envelope, capability_flag_risk=RiskTier.R3)
    assert result.risk_tier is RiskTier.R3
    assert result.route is WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED


def test_max_of_operation_path_and_capability_risk() -> None:
    """All three inputs combine via max(): R1 op + R2 path + R3 flag = R3."""

    floor = _StubPathRiskFloor(((".github/workflows/**", "R2"),))
    envelope = ExecutionEnvelope(("source_edit",), (".github/workflows/ci.yml",))
    result = classify_risk(
        envelope,
        path_risk_floor=floor,
        capability_flag_risk=RiskTier.R3,
    )
    assert result.risk_tier is RiskTier.R3


def test_floor_does_not_lower_existing_risk() -> None:
    """When operation risk already exceeds floor risk, operation risk wins."""

    floor = _StubPathRiskFloor((("docs/**", "R1"),))
    envelope = ExecutionEnvelope(("workflow_change",), ("docs/readme.md",))
    result = classify_risk(envelope, path_risk_floor=floor)
    assert result.risk_tier is RiskTier.R2
