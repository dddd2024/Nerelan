from __future__ import annotations

import pytest

from reverse_agent.architecture.contracts import ExecutionEnvelope
from reverse_agent.architecture.risk import RiskTier, WorkflowRoute
from reverse_agent.architecture.risk_classifier import classify_risk


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
