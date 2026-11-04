"""Who owns account-level routing: Magpie or Nerelan (Owner decision 2026-11-04).

The audit found that Magpie already switches between subscription accounts
(``accounts switch <agent> next``), routes by use/pace/speed/price
(``group … routing=…``) and can block until allowance returns
(``quota wait``). Nerelan's own account selection, cooldowns and idle waiting
therefore duplicate an upstream capability whenever Magpie is managing accounts.

This module only *decides who decides*. It is a pure function over configuration
and two environment acknowledgements — it performs no I/O, so it can never
change behaviour because a health probe timed out.

Resolution rules:

===================  =========================================================
``account_routing``  owner
===================  =========================================================
``local``            Nerelan selects accounts (today's behaviour, the default)
``magpie``           Magpie selects accounts; Nerelan stops applying account
                     health/cooldown/idle-wait constraints
``auto``             ``magpie`` only when **both** Magpie integration is enabled
                     (``REVERSE_AGENT_MAGPIE=1``) and the Owner has acknowledged
                     that switching behaviour was verified
                     (``REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING=1``);
                     otherwise ``local``
===================  =========================================================

The second flag exists on purpose: the audit verified that the *capability*
exists, not that it behaves correctly on this machine (M2/M3 are marked
"capability confirmed, behaviour untested"). Flipping the owner silently on a
reachable port would be exactly the kind of unverified behaviour change
`AGENTS.md` asks us to avoid.
"""
from __future__ import annotations

import os
from typing import Mapping, Optional

ROUTING_OWNERS = ("local", "magpie", "auto")
MAGPIE_ENABLED_ENV = "REVERSE_AGENT_MAGPIE"
SWITCHING_ACK_ENV = "REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING"


def normalise(value: object) -> str:
    text = str(value or "").strip().lower()
    return text if text in ROUTING_OWNERS else "local"


def resolve_account_routing(value: object, *,
                            env: Optional[Mapping[str, str]] = None) -> str:
    """Return the effective owner: ``"local"`` or ``"magpie"`` (never ``"auto"``)."""
    requested = normalise(value)
    if requested != "auto":
        return requested
    environment = env if env is not None else os.environ
    enabled = environment.get(MAGPIE_ENABLED_ENV) == "1"
    acknowledged = environment.get(SWITCHING_ACK_ENV) == "1"
    return "magpie" if enabled and acknowledged else "local"


def routing_view(value: object, *, env: Optional[Mapping[str, str]] = None) -> dict[str, object]:
    """Operator-facing explanation of the decision (why it resolved this way)."""
    requested = normalise(value)
    environment = env if env is not None else os.environ
    owner = resolve_account_routing(requested, env=environment)
    reason = ("explicit" if requested != "auto"
              else "auto_magpie_verified" if owner == "magpie"
              else "auto_requires_verified_switching")
    return {
        "requested": requested,
        "owner": owner,
        "reason": reason,
        "magpie_enabled": environment.get(MAGPIE_ENABLED_ENV) == "1",
        "switching_acknowledged": environment.get(SWITCHING_ACK_ENV) == "1",
    }
