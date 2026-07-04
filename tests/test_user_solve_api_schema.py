from reverse_agent.user_solve_api_schema import schema_snapshot


def test_schema_snapshot_covers_frontend_contract_surfaces() -> None:
    snapshot = schema_snapshot()

    assert snapshot["fixture_only"] is True
    assert snapshot["request"]["real_uploads"] is False
    assert snapshot["response"]["default_user_output_hides_internal_refs"] is True
    assert {"fixture_not_found", "route_not_found"} <= set(snapshot["error_payload"]["codes"])
    assert set(snapshot["ui_state"]["display_states"]) >= {
        "candidate_pending_validation",
        "needs_more_evidence",
        "verified",
        "blocked",
        "failed",
    }
    assert {item["path"] for item in snapshot["routes"]} >= {
        "/api/fixtures",
        "/api/fixtures/{fixture_name}",
        "/api/solve",
    }
    assert "fixtures/catalog.json" in snapshot["frontend_demo"]["required_files"]
