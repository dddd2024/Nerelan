# User Solve Workbench Foundation

The User Solve Workbench is a local, fixture-only preview layer over the accepted user-solve contracts. It composes the controller, fixtures, UI state mapping, capability metadata, route plans, and synthetic task traces without dispatching real work.

## Boundary

- No real sample analysis.
- No external analysis tool invocation.
- No production HTTP service.
- No database, queue, scheduler, or remote runner dispatch.
- No persistent task or session files.

The workbench API is route-shaped but in-process: callers pass `method`, `path`, and an optional body into pure functions.

## Surfaces

- `reverse_agent/tool_profiles.py` defines deterministic tool metadata.
- `reverse_agent/tool_capabilities.py` summarizes runner capabilities from profiles.
- `reverse_agent/user_solve_route_plan.py` describes planned next actions without executing them.
- `reverse_agent/user_solve_task_trace.py` serializes synthetic fixture task traces.
- `reverse_agent/user_solve_workbench.py` composes fixture responses, UI state, route plans, capabilities, and traces.
- `reverse_agent/user_solve_workbench_api.py` exposes local route-shaped preview functions.

Gate artifacts are written under `project_state/gates/` as current-round evidence only.
