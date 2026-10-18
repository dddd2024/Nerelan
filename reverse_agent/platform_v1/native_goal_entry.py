"""Explicit native startup command using the official CombinedTrustedHost lifecycle.

python -m reverse_agent.platform_v1.native_goal_entry --native-admit-goal GOAL_ID

Optional --native-isolate-unknown-sha256 SHA256 selects the complete bounded
historical UNKNOWN snapshot for display and atomic revalidation. The digest
grants no authority; genuine native Owner consent is still required.

This starts a host, never attaches to an existing host. Existing port ownership
errors apply. Without the option it performs normal host startup. Consent uses
the host's Windows identity and genuine native dialog; no auto-confirm option.
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence
import re


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--native-admit-goal", action="append", metavar="GOAL_ID")
    parser.add_argument("--native-isolate-unknown-sha256", action="append", metavar="SHA256")
    args = parser.parse_args(argv)
    goals = args.native_admit_goal
    if goals is not None and (
        len(goals) != 1 or re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,255}", goals[0]) is None
    ):
        parser.error("--native-admit-goal requires exactly one unambiguous Goal ID")

    isolation = args.native_isolate_unknown_sha256
    if isolation is not None and (
        goals is None or len(isolation) != 1
        or re.fullmatch(r"[0-9a-f]{64}", isolation[0]) is None
    ):
        parser.error("isolation requires one snapshot SHA-256 and one native Goal")
    # Parse before importing/constructing the host or running readiness probes.
    from .trusted_host import run_combined_trusted_host
    if goals is None:
        run_combined_trusted_host()
    else:
        run_combined_trusted_host(native_goal_id=goals[0], **(
            {"unknown_claims_sha256": isolation[0]} if isolation else {}))


if __name__ == "__main__":
    main()
