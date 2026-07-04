import pytest

from reverse_agent.tool_profiles import ToolProfile, default_tool_profiles, load_tool_profiles, tool_profile_snapshot


def test_default_tool_profiles_are_deterministic_and_safe() -> None:
    first = tool_profile_snapshot()
    second = tool_profile_snapshot()

    assert first == second
    assert first["executes_tools"] is False
    assert [item.tool_id for item in default_tool_profiles()] == [
        "fast_strings",
        "ida_summary",
        "runtime_validation",
    ]


def test_tool_profile_rejects_machine_specific_path_source() -> None:
    with pytest.raises(ValueError):
        ToolProfile(
            tool_id="bad",
            label="Bad",
            category="static",
            path_source="C:\\Tools\\ida.exe",
            availability="available",
        )


def test_load_tool_profiles_applies_override_by_tool_id() -> None:
    profiles = load_tool_profiles(
        [
            {
                "tool_id": "ida_summary",
                "label": "IDA summary metadata",
                "category": "static",
                "path_source": "USER_CONFIGURED_IDA_PATH",
                "availability": "disabled",
                "capability_flags": ["ida_summary"],
                "disabled_reason": "not allowed in this fixture preview",
            }
        ]
    )

    ida = {item.tool_id: item for item in profiles}["ida_summary"]
    assert ida.availability.value == "disabled"
    assert ida.disabled_reason
