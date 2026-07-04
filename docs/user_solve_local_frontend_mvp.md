# User Solve Local Frontend MVP

The local frontend MVP is a fixture-only preview over the accepted offline User
Solve control plane.

## Surfaces

- `reverse_agent/user_solve_fixtures.py` defines the deterministic fixture
  catalog.
- `reverse_agent/user_solve_frontend_bridge.py` renders controller envelopes for
  frontend consumption.
- `reverse_agent/user_solve_local_api.py` provides route-shaped in-process
  functions for local previews.
- `reverse_agent/user_solve_api_schema.py` emits the schema/demo snapshot.
- `reverse_agent/user_solve_ui_state.py` maps internal statuses to stable UI
  states.
- `reverse_agent/user_solve_errors.py` defines public-safe error payloads.
- `frontend/user_solve_demo/` is the static demo.

## Demo States

The demo covers `candidate`, `missing-evidence`, `blocked`, `failed`, and
`verified`. `candidate` remains pending validation. `verified` exists only as a
supplied fixture with passed validation evidence. `missing-evidence` maps to
non-executing fallback guidance.

## Inspecting Locally

Open `frontend/user_solve_demo/index.html` directly. The page reads
`fixtures/catalog.json` when a static server is available and uses embedded
fixtures as a fallback when opened from disk.

The workbench foundation reuses this static demo as its visual surface and adds
route-plan, capability, and task-trace metadata through the local workbench
facade and gate snapshots.

The project gate for this slice is:

```powershell
python -m reverse_agent.project_gate user-solve-local-frontend-mvp --state-dir project_state
```

It writes:

- `project_state/gates/user_solve_local_frontend_mvp_result.json`
- `project_state/gates/user_solve_frontend_mvp_snapshot.json`

## Boundaries

This MVP does not process real uploads or binaries, persist user sessions,
dispatch runners, call network APIs, create a server, use a database or queue,
or claim any concrete sample is solved, statically verified, runtime validated,
or audit verified.
