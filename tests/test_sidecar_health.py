from __future__ import annotations

from reverse_agent.sidecar_health import (
    merge_candidate_sidecar_health,
    normalize_sidecar_health,
    summarize_sidecar_health,
)


def test_normalize_sidecar_health_maps_fields_and_extra() -> None:
    raw = {
        "script_load_status": "loaded",
        "hook_install_status": "installed",
        "hook_count": 3,
        "python_message_count_total": 12,
        "subprocess_returncode": 124,
        "unknown_field": "keep_me",
    }

    health = normalize_sidecar_health(raw)

    assert health["schema_version"] == 1
    assert health["lifecycle"]["script_load_status"] == "loaded"
    assert health["hook_install"]["hook_install_status"] == "installed"
    assert health["hook_install"]["hook_count"] == 3
    assert health["message_bridge"]["python_message_count_total"] == 12
    assert health["subprocess"]["subprocess_returncode"] == 124
    assert health["extra"]["unknown_field"] == "keep_me"


def test_summarize_sidecar_health_flattens_categories() -> None:
    health = {
        "schema_version": 1,
        "lifecycle": {"script_load_status": "loaded"},
        "hook_install": {"hook_count": 3},
        "message_bridge": {"python_message_count_total": 5},
    }

    summary = summarize_sidecar_health(health)

    assert summary["script_load_status"] == "loaded"
    assert summary["hook_count"] == 3
    assert summary["python_message_count_total"] == 5


def test_merge_candidate_sidecar_health_attaches_normalized_view() -> None:
    merged = merge_candidate_sidecar_health({"candidate_hex": "aa"}, {"hook_install_status": "installed"})

    assert merged["candidate_hex"] == "aa"
    assert merged["sidecar_health"]["hook_install"]["hook_install_status"] == "installed"
