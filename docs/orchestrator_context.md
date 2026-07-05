# Orchestrator Context

Planner and auditor context snapshots are bounded to current project-state decision, command-plan, gate, report, and pytest artifacts.

They do not read full `solve_reports/`, call model APIs, process uploads, or expand reverse-solving scope.
