"""Check subscription quota before dispatch, not after a run fails (P0-3).

For a binding on a subscription account (Codex / Claude Code login), the host compares
what the account's windows have left with what this binding's tasks typically use:

* ``switch`` - the limit is reached, or even the optimistic estimate cannot fit the next
  task: an agent-team role moves to an alternative binding on another account, when one
  exists; otherwise the run goes ahead with a recorded warning.
* ``warn`` - the pessimistic estimate does not fit, or the account is near its limit:
  the run goes ahead and the warning is recorded.
* ``ok`` - nothing indicates a shortfall.

API-key bindings have no subscription window and are never checked here.
"""

from __future__ import annotations

import re
from statistics import median
from typing import Any, Iterable, Mapping, Sequence

from ..model_access.contracts import NATIVE_CLI_PROVIDERS
from ..model_access.pricing import equivalent_cost
from ..model_access.quota_forecast import guard, parse_time, worst


def typical_task_units(records: Iterable[Mapping[str, Any]], binding_id: str, model_id: str) -> float | None:
    """Median list-price units of this binding's successful tasks that reported tokens."""
    values = []
    for record in records:
        if record.get("binding_ref") != binding_id or not record.get("ok") or not record.get("tokens"):
            continue
        model = record["models"][0] if len(record.get("models") or ()) == 1 else model_id
        usd = equivalent_cost(model, record["tokens"]).get("usd")
        if usd:
            values.append(usd)
    return round(median(values), 4) if values else None


def typical_need(records: Sequence[Mapping[str, Any]], binding: Mapping[str, Any],
                 bindings: Sequence[Mapping[str, Any]]) -> tuple[float | None, str]:
    """The binding's own typical task, else its connection's, else any task's, with the source."""
    own = typical_task_units(records, binding["binding_id"], binding["model_id"])
    if own is not None:
        return own, "binding"
    for scope, members in (("connection", [b for b in bindings if b["connection_id"] == binding["connection_id"]]),
                           ("all_tasks", list(bindings))):
        values = [value for member in members
                  if (value := typical_task_units(records, member["binding_id"], member["model_id"])) is not None]
        if values:
            return round(median(values), 4), scope
    return None, "none"


def check(connection: Mapping[str, Any], quotas: Mapping[str, Any], need_units: float | None) -> dict[str, Any] | None:
    """Worst decision over the account's windows, or None for a binding without one."""
    provider = connection.get("executor_provider_id")
    if provider not in NATIVE_CLI_PROVIDERS or connection.get("auth_method") == "api_key":
        return None
    quota = quotas.get(provider)
    windows = quota.get("windows") if isinstance(quota, Mapping) else None
    if not windows:
        return {"decision": "ok", "reason": "quota_unknown", "provider": provider}
    decision = worst(guard(window, need_units) | {"window": window.get("window")} for window in windows)
    return decision | {"provider": provider, "need_units": need_units}


# Coding roles from weakest to strongest; a stand-in may only be as strong or stronger.
CODING_LADDER = ("simple", "coder", "complex")


def alternatives(role: str, current: Mapping[str, Any], *, bindings: Sequence[Mapping[str, Any]],
                 roster: Mapping[str, Mapping[str, Any]], usable_executors: set[str],
                 standins: Sequence[str] = ()) -> list[Mapping[str, Any]]:
    """Candidate bindings on other connections: the same model first, then stronger coding roles,
    then the stand-ins the Owner declared for this coding role.

    Quality must not drop to save quota, so a weaker role's agent is never a stand-in unless the
    Owner named it, and the planner and reviewer are only replaced by the same model on another account.
    """
    def eligible(binding: Mapping[str, Any] | None) -> bool:
        return bool(binding and binding.get("enabled") and binding["connection_id"] != current["connection_id"]
                    and binding["executor_id"] in usable_executors)

    by_id = {binding["binding_id"]: binding for binding in bindings}
    ordered = [b for b in bindings if eligible(b) and b["model_id"] == current["model_id"]]
    if role in CODING_LADDER:
        for stronger in CODING_LADDER[CODING_LADDER.index(role) + 1:]:
            binding = by_id.get((roster.get(stronger) or {}).get("binding_id", ""))
            if eligible(binding) and binding not in ordered:
                ordered.append(binding)
        for binding_id in standins:
            binding = by_id.get(binding_id)
            if eligible(binding) and binding not in ordered:
                ordered.append(binding)
    return ordered


# Answers in which the account itself said it is out of quota; only these start or extend a hold.
ACCOUNT_LIMIT = re.compile(r"api_error_429|rate_limit|usage_limit")
# Failures that mean quota, not agent skill: the account's answer, or the host refusing dispatch for it.
LIMIT_HIT = re.compile(ACCOUNT_LIMIT.pattern + r"|quota_exhausted")
LIMIT_HIT_HOLD_SECONDS = 3600  # when the account's own reset time is unknown


def limit_hit_until(hit_at: float, quota: Mapping[str, Any] | None) -> float:
    """Until when an account that just refused a run counts as exhausted.

    The earliest known window reset after the hit; otherwise a fixed hold. An estimate that
    the window has room again never overrides what the account actually answered.
    """
    resets = []
    for window in (quota or {}).get("windows", ()) if isinstance(quota, Mapping) else ():
        value = window.get("resets_at") if isinstance(window, Mapping) else None
        reset = float(value) if type(value) in (int, float) else parse_time(value)
        if reset is not None and reset > hit_at:
            resets.append(reset)
    return min(resets) if resets else hit_at + LIMIT_HIT_HOLD_SECONDS
