from __future__ import annotations

from typing import Any, Mapping


def build_manual_execution_handoff(
    *,
    decision: Mapping[str, Any],
    command_plan: Mapping[str, Any],
    task_id: str,
    job_id: str,
) -> dict[str, Any]:
    commands = [
        {
            "index": command.get("index"),
            "kind": str(command.get("kind") or ""),
            "command": str(command.get("command") or ""),
            "expected_exit_codes": list(command.get("expected_exit_codes") or []),
        }
        for command in command_plan.get("commands", [])
        if isinstance(command, Mapping)
    ]
    omitted = [
        {
            "kind": str(command.get("kind") or ""),
            "command": str(command.get("command") or ""),
            "reason": str(command.get("reason") or command.get("notes") or ""),
        }
        for command in command_plan.get("omitted_commands", [])
        if isinstance(command, Mapping)
    ]
    return {
        "schema_version": 1,
        "handoff_id": f"handoff_{job_id}",
        "decision_id": str(decision.get("decision_id") or ""),
        "round_id": str(decision.get("round_id") or ""),
        "mainline": str(decision.get("mainline") or ""),
        "task_id": task_id,
        "job_id": job_id,
        "decision_authority": "project_state/decision_packet.md",
        "command_plan_authority": "project_state/gates/command_plan.json",
        "allowed_commands": commands,
        "omitted_commands": omitted,
        "stop_conditions": [
            "Do not run omitted commands.",
            "Do not dispatch runners or remote agents.",
            "Do not process real samples or uploads.",
            "Stop if final-check or command-plan authority fails.",
        ],
        "remote_mutation_allowed": False,
        "runner_dispatch_enabled": False,
        "external_tool_invocation": False,
        "model_api_invocation": False,
        "prompt_packet": (
            "Manual-mode handoff preview. Review command-plan authority, execute only allowed "
            "local commands if separately authorized by a future decision, and import structured "
            "results without claiming real sample verification."
        ),
    }
