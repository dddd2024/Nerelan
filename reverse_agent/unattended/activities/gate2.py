"""The minimal synthetic Activity used by the compatibility probe."""

from __future__ import annotations

from temporalio import activity


@activity.defn
async def run_synthetic_activity(value: str) -> str:
    """Return a deterministic marker from outside Workflow code."""

    if not value or len(value) > 256:
        raise ValueError("synthetic_activity_input_out_of_bounds")
    return f"activity:{value}"
