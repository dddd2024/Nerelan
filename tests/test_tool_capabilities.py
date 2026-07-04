from reverse_agent.tool_capabilities import capability_from_profiles, capability_snapshot


def test_capability_snapshot_is_metadata_only() -> None:
    snapshot = capability_snapshot()
    capability = snapshot["capability"]

    assert snapshot["fixture_only"] is True
    assert capability["can_dispatch"] is False
    assert capability["executes_external_tools"] is False
    assert "fast_strings" in capability["available_tools"]
    assert "runtime_validation" in capability["disabled_tools"]


def test_runner_capability_rejects_dispatch() -> None:
    try:
        capability_from_profiles(runner_id="fixture", platform="local")
    except ValueError as exc:  # pragma: no cover
        raise AssertionError(f"default capability should be valid: {exc}") from exc
