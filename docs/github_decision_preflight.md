# GitHub Decision Preflight

`.github/workflows/decision-preflight.yml` is a read-only workflow surface for local/static decision validation.

The workflow installs the package, runs the project gate preflight and command plan, materializes post-final sync and job lifecycle evidence, checks CI workflow readiness, runs `decision-preflight`, and executes focused tests for the affected governance modules.

The workflow has `contents: read` permissions and does not include repository mutation commands, pull request mutation commands, runner dispatch, external model calls, reverse sample execution, cleanup apply, archive apply, or closeout execution. Its uploaded artifact scope is limited to generated gate JSON and `project_state/pytest_result.txt` evidence.
