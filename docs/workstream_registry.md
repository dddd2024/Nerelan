# Workstream Registry

`project_state/roadmap/workstreams.json` is a lightweight roadmap index. It prevents new ideas from becoming execution authority by accident.

Allowed lifecycle states are:

`IDEA`, `CANDIDATE`, `ROADMAP_ACCEPTED`, `READY_FOR_DECISION`, `ACTIVE_ROUND`, `ACCEPTED`, `DEFERRED`, `REJECTED`.

Only the workstream selected by `project_state/decision_packet.md` may be marked `ACTIVE_ROUND`. All other roadmap entries remain planning context until a future decision promotes them.

The registry keeps major directions separate: project governance, state hygiene, manual Web orchestration, User Solve Layer, AgentRunner dispatch, GitHub CI/state gate work, reverse-solving capability, external tool integration, and database/indexing ideas.
