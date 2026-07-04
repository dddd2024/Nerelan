import json
from pathlib import Path

from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_fixtures import FIXTURE_NAMES, fixture_catalog, fixture_payload, fixture_request


def test_fixture_catalog_covers_frontend_states() -> None:
    catalog = fixture_catalog()

    assert catalog["fixture_only"] is True
    assert set(catalog["names"]) == {"candidate", "missing-evidence", "blocked", "failed", "verified"}
    assert not contains_internal_reference(catalog)


def test_fixture_payloads_are_deterministic_copies() -> None:
    first = fixture_payload("candidate")
    second = fixture_payload("candidate")
    first["selected_candidate"] = "changed"

    assert second["selected_candidate"] == "flag{demo_candidate}"


def test_fixture_request_builds_safe_requests_for_all_fixtures() -> None:
    for name in FIXTURE_NAMES:
        request = fixture_request(name)
        assert request.fixture_name == name
        assert request.input_kind == "fixture"
        assert not contains_internal_reference(request.to_user_dict())


def test_static_demo_fixture_catalog_matches_python_catalog() -> None:
    path = Path("frontend/user_solve_demo/fixtures/catalog.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    names = {item["fixture_name"] for item in payload["fixtures"]}

    assert names == set(FIXTURE_NAMES)
    assert not contains_internal_reference(payload)
