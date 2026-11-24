"""Declared Magpie group members: pacing and availability (Owner decision 2026-11-17, groups first)."""
from reverse_agent.platform_v1.routing_inputs import (group_members, inherit_group_availability,
                                                      paced_group_provider, parse_groups)

GROUPS = {
    "group/nerelan-kimi-k3": {"identity": "kimi-k3",
                              "members": ["workbuddy/kimi-k3-1", "raccoon/sn-kimi-k3", "token-sensenova/kimi-k3"]},
    "group/nerelan-gpt-6-sol": {"identity": "gpt-6-sol", "members": ["codex/gpt-6-sol", "workbuddy-ai/gpt-6-sol"]},
    "group/nerelan-glm-5-3": {"identity": "glm-5.3"},
}


def candidate(binding_id, model_id, state="UNKNOWN", connection="magpie"):
    return {"binding_id": binding_id, "model_id": model_id, "connection_id": connection,
            "availability": {"state": state}}


def test_parse_groups_keeps_valid_members_and_reports_invalid_ones():
    groups, errors = parse_groups({
        "group/a": {"identity": "kimi-k3", "members": [" workbuddy/kimi-k3-1 ", "raccoon/sn-kimi-k3"]},
        "group/b": {"identity": "glm-5.3", "members": "workbuddy/glm-5.3"},
        "group/c": {"identity": "glm-5.3", "members": ["glm-5.3"]},
        "group/d": {"identity": "glm-5.3", "members": ["group/nested"]},
        "group/e": {"identity": "glm-5.3"},
    })
    assert groups["group/a"] == {"identity": "kimi-k3", "members": ["workbuddy/kimi-k3-1", "raccoon/sn-kimi-k3"]}
    # Bad members are dropped, but the group stays declared with its identity.
    assert all(groups[name] == {"identity": "glm-5.3"} for name in ("group/b", "group/c", "group/d", "group/e"))
    assert errors == [f"invalid_model_routing_group_members:group/{name}" for name in "bcd"]


def test_group_members_resolves_declared_groups_only():
    assert group_members("group/nerelan-kimi-k3", GROUPS)[0] == "workbuddy/kimi-k3-1"
    assert group_members("magpie/group/nerelan-kimi-k3", GROUPS)  # provider-prefixed resolved id
    assert group_members("group/nerelan-glm-5-3", GROUPS) == ()  # declared without members
    assert group_members("group/undeclared", GROUPS) == ()
    assert group_members("token-sensenova/kimi-k3", GROUPS) == ()


def test_a_group_failing_over_onto_a_paced_account_is_paced():
    assert paced_group_provider("group/nerelan-gpt-6-sol", GROUPS, {"codex", "claude"}) == "codex"
    assert paced_group_provider("group/nerelan-kimi-k3", GROUPS, {"codex", "claude"}) == ""
    assert paced_group_provider("codex/gpt-6-sol", GROUPS, {"codex"}) == ""  # direct models keep their own rule


def test_an_unknown_group_takes_an_available_members_availability():
    rows = [candidate("magpie-group-nerelan-kimi-k3", "group/nerelan-kimi-k3"),
            candidate("magpie-workbuddy-kimi-k3-1", "workbuddy/kimi-k3-1", "UNKNOWN"),
            candidate("magpie-token-sensenova-kimi-k3", "token-sensenova/kimi-k3", "AVAILABLE")]
    inherit_group_availability(rows, GROUPS, {"codex"})
    assert rows[0]["availability"] == {"state": "AVAILABLE", "reason": "group_member_available",
                                       "member_binding": "magpie-token-sensenova-kimi-k3"}


def test_group_availability_is_never_borrowed_from_paced_other_connection_or_over_own_evidence():
    rows = [candidate("magpie-group-nerelan-gpt-6-sol", "group/nerelan-gpt-6-sol"),
            candidate("magpie-codex-gpt-6-sol", "codex/gpt-6-sol", "AVAILABLE"),
            candidate("magpie-group-nerelan-kimi-k3", "group/nerelan-kimi-k3", "UNAVAILABLE"),
            candidate("magpie-workbuddy-kimi-k3-1", "workbuddy/kimi-k3-1", "AVAILABLE"),
            candidate("other-group", "group/nerelan-kimi-k3", connection="other"),
            candidate("magpie-group-nerelan-glm-5-3", "group/nerelan-glm-5-3"),
            candidate("magpie-workbuddy-glm-5.3", "workbuddy/glm-5.3", "AVAILABLE")]
    inherit_group_availability(rows, GROUPS, {"codex"})
    # A paced member lends nothing; pacing the group decides it.
    assert rows[0]["availability"] == {"state": "UNKNOWN"}
    # The group's own evidence (here UNAVAILABLE) always wins.
    assert rows[2]["availability"] == {"state": "UNAVAILABLE"}
    # A member on another connection is a different account path.
    assert rows[4]["availability"] == {"state": "UNKNOWN"}
    # No declared members: nothing to inherit from.
    assert rows[5]["availability"] == {"state": "UNKNOWN"}
