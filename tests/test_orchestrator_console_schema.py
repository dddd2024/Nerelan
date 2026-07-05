from reverse_agent.orchestrator_console_schema import CONSOLE_PANELS, build_console_fixture_bundle


def test_console_fixture_bundle_covers_static_panels() -> None:
    bundle = build_console_fixture_bundle()

    assert "Dashboard" in CONSOLE_PANELS
    assert "Handoff" in bundle["panels"]
    assert bundle["static_only"] is True
    assert bundle["network_calls"] is False
    assert bundle["build_step_required"] is False
