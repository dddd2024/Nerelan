# Actual Windows native-client acceptance for118/384

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261007_issue118_client_page_close_r3_v1",
  "round_id": "round_20261007_issue118_client_page_close_r3_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "ISSUE118_ACTUAL_WINDOWS_PRIVATE_CLIENT_ACCEPTANCE",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / explicit current Owner full architecture delegation",
  "approval_basis": "Owner explicitly approved v3 scope, activation-bound 90-minute window, then exact updated signed Edge fingerprint on 2026-10-07; all failure/spending history preserved.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-native-browser-acceptance-r3-v3-20261004",
  "base_sha": "af707142ce037e7392111db442419bf2ac7c7b06",
  "activation_base_sha": "af707142ce037e7392111db442419bf2ac7c7b06",
  "starting_head": "af707142ce037e7392111db442419bf2ac7c7b06",
  "required_branch": "codex/issue118-client-page-close-r3-v1-20261007",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "local_browser_execution_allowed": true,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": true,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "# Bounded page-close source repair + one real acceptance \u2014 pending Owner approval\n\nActual v3 evidence: source86caba starts at configured frontend18879 with ready private broker. After identity-bound native WindowPattern.Close, browser root has no main window but still exists; original broker remains after25seconds and host readiness staystrue. Canonical owned cleanup succeeded with both Windows Jobs empty. Observation1's PowerShell HOME error and unavailable minimized-window pixels remain recorded, not waived or represented as product acceptance. No positive/negative HTTP status or settings-navigation result is claimed. Draft1086 is terminal/unaccepted/unmerged.\n\n## Exact prospective source scope\n\nOnly these three product paths may change:\n\n- frontend/trusted-client.mjs: register the supported main frontend page's close event before navigation; treat that page close as a terminal client-session condition alongside private-input end and browser disconnected. Reuse Playwright's event interface. Always finish browser/context cleanup and destroy private stdin; do not require browser disconnected to notice a closed main page. Preserve current native HTTP confinement/auth/bootstrap behavior and fixed diagnostics.\n- frontend/trusted-client.node-test.mjs: add a provider-free actual Node child regression with synthetic private bootstrap held open and an ephemeral SDK test seam that emits main-page close without browser disconnected. Require bounded child exit and cleanup; preserve all original tests/assertions. The SDK seam is a fixture, not real browser evidence. Do not install or copy a runtime.\n- docs/local-client-session.md: document the supported main-page terminal condition and accurately distinguish fixture/native-source verification from later real browser acceptance.\n\nNo host, launcher, workflow, dependency, frontend application, governance instruction or credential source change. No check weakening. Source identity remains separate from Owner policy confirmation and privileged adapters; this does not complete #118/#384.\n\n## New exact authority and publication\n\nReuse controller F:/Nerelan-issue1027-frontend-audit; preserve its five generated gates. New branch codex/issue118-client-page-close-r3-v1-20261007 from explicit integration codex/issue118-native-browser-acceptance-r3-v3-20261004@af707142ce037e7392111db442419bf2ac7c7b06. One new immutable Decision-only activation, existing canonical gates/preflight/readiness, first exact Draft before source edits, one product commit, two pushes, one Draft, up to two description updates. No staging of runtime/helpers/evidence/generated gates. No ready/merge/main/history rewrite/tag/release/deploy.\n\nAllow up to two source corrections and two provider-free development invocations, then three required checks: full tests/platform_v1 with only original installed-OpenCode opt-in exclusions, actual tests/test_path_a_gate.py, and committed exact-head focused launcher/trusted-client/bootstrap/session tests including native Node. git diff --check and existing publication-readiness required. Observe original natural exact-head CI logs/JUnit; no dispatch or rerun. Any failed mandatory check blocks product publication; no automatic successor/reset.\n\nExact check commands use known C:/Program Files/Python313/python.exe -B -X utf8 -m pytest -q. Focused development/exact-head paths are tests/platform_v1/test_dev_up_contract.py, test_trusted_client_bootstrap.py, test_task_client_auth.py, test_trusted_host.py, test_trusted_host_lifecycle.py and test_local_client_session.py (all six beneath tests/platform_v1); the existing bootstrap test invokes the native Node suite. Each focused invocation<=900s, full Platform<=2400s, Path A<=120s. Use a fresh basetemp child under F:/nrl-pageclose118-v1, creating its empty parent before the first invocation. Full Platform excludes exactly the original four opt-ins: test_task3c_v6_production_relay.py::TestCombinedTrustedHostInstalledOpenCodeE2E::test_real_task_api_opencode_relay_fake_provider_end_to_end; test_task3c_v4_repairs.py::TestInstalledOpenCodeFakeProviderSmoke::test_installed_opencode_fake_provider_end_to_end; test_task3c_v5_opencode_probe.py::TestDirectFakeProviderControl::test_opencode_direct_fake_provider; test_task3c_v5_opencode_probe.py::TestRelayFakeProviderRun::test_opencode_relay_fake_provider (each beneath tests/platform_v1). No other deselection/skip or baseline change.\n\n## Included real acceptance after source and native CI pass\n\nExactly one new owned clone F:/nrl-auth118-native4 on the verified product commit, isolated cacheDir, existing dependencies without install/shared-cache modification, one stack start<=180s, one browser start, two observation invocations<=180s each, one identity-bound cleanup<=120s. Ports18877/18878/18879 must be free; healthy existing runtimes and previous owned clones remain untouched. Existing approved known Node and Microsoft-signed Edge154.0.4258.62 fingerprints must match immediately before launch. No models/provider/auth probes, credentials, tasks/window activation or privileged side effects.\n\nExternal observer changes are included: replace reserved HOME with a task-specific variable; add a static reserved-variable check before runtime; restore only the identity-bound owned native window to Normal via WindowPattern before PrintWindow capture, without relying on foreground or capturing another window. Verify actual home/tasks/settings pixels, explicit frontend-frame Task API200, unrelated missing-capability/no-Origin401 and health readiness-only; close the supported main page/window via native UI and require original broker exit/readiness false before canonical cleanup. Missing/blank pixels or unexecuted HTTP evidence are unverified, never acceptance. Preserve failures and perform no second runtime start.\n\nFreeze a new 90-minute absolute cutoff at first activation under this new approval; do not renew after activation. This new scope does not alter any previous cutoff or immutable Decision. Source totals begin with dev6/corrections7 spent; up to two additional allowed, not resets. Prior runtime startups3, browser launches2, observations4 remain. If this phase starts its runtime, aggregates become startups4/browser3/observations<=6. Actual source spending is charged as incurred.\n\nThis combined new grant includes all named source repair, checks, exact Draft publication and one later real acceptance so covered steps do not need repeated approval. It does not grant independent acceptance/landing or other #118 phases. Current v3 source correction budget is zero and runtime startup budget exhausted, so none of these new operations is authorized until explicit Owner approval is recorded and a fresh immutable Decision is activated.\n\nOWNER EXPLICITLY APPROVED this exact three-file repair/check/CI/one-real-acceptance proposal in the chat on2026-10-07, and delegated routine covered corrections/checks/acceptance without repeated confirmation. This is recorded Owner approval, not Agent self-issued authority. All prior failures/spending remain. No further runtime startup or scope/budget/expiry widening is implied.\n\nFROZEN_START=2026-10-07T08:32:39.178206+00:00; EXPIRES_AT=2026-10-07T10:02:39.178206+00:00",
    "completion_boundary": "Three-file source repair, local/native-CI evidence and one real acceptance; no independent acceptance/full architecture/landing claim."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "frontend/trusted-client.mjs",
    "frontend/trusted-client.node-test.mjs",
    "docs/local-client-session.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "frontend/trusted-client.mjs",
    "frontend/trusted-client.node-test.mjs",
    "docs/local-client-session.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "reverse_agent/platform_v1/local_client_session.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/model_access/service.py",
    ".github/workflows/ci.yml",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/repository-client.ts",
    "frontend/src/lib/goal-start-operation.ts",
    "frontend/src/lib/goal-continuation-operation.ts"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "pyproject.toml",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "**/secrets/**",
    "**/.env",
    "**/auth.json"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "mark_ready",
    "merge",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "raw_secret_read_or_export",
    "model_provider_config_mutation",
    "payment",
    "process_stop_without_identity",
    "issue_comment",
    "pull_request_comment",
    "raw_credential_read_copy_or_print",
    "independent_acceptance_by_self_or_same_underlying_model",
    "automatic_GPT_fallback_or_retries",
    "shared_dependency_mutation",
    "existing_model_configuration_mutation",
    "unknown_process_stop",
    "ignore_rules_or_sandbox_bypass",
    "existing_runtime_or_configuration_mutation",
    "application_model_retry",
    "model_fallback",
    "raw_managed_session_access",
    "existing_task_or_runtime_mutation",
    "destructive_outside_new_owned_disposable_fixture_process_groups_or_scratch"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": true,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Owned real frontend18879/Task18877/Model18878/ephemeral relay only; no models/provider/auth probes/other listeners."
    ],
    "github_control_plane_network_exceptions": [
      "Two exact pushes exactcodex/issue118-client-page-close-r3-v1-20261007, one Draft againstcodex/issue118-native-browser-acceptance-r3-v3-20261004@af707142ce037e7392111db442419bf2ac7c7b06,2 descriptions, bounded read-only natural CI and authority; no other writes."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/platform_v1/functional_validation.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "native.bootstrap",
      "command": "Fresh exact-base branch, immutable Decision-only activation and canonical gates; Draft before any actual runtime.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "local_static_check",
        "command_plan_generation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "native.implementation",
      "command": "# Bounded page-close source repair + one real acceptance \u2014 pending Owner approval\n\nActual v3 evidence: source86caba starts at configured frontend18879 with ready private broker. After identity-bound native WindowPattern.Close, browser root has no main window but still exists; original broker remains after25seconds and host readiness staystrue. Canonical owned cleanup succeeded with both Windows Jobs empty. Observation1's PowerShell HOME error and unavailable minimized-window pixels remain recorded, not waived or represented as product acceptance. No positive/negative HTTP status or settings-navigation result is claimed. Draft1086 is terminal/unaccepted/unmerged.\n\n## Exact prospective source scope\n\nOnly these three product paths may change:\n\n- frontend/trusted-client.mjs: register the supported main frontend page's close event before navigation; treat that page close as a terminal client-session condition alongside private-input end and browser disconnected. Reuse Playwright's event interface. Always finish browser/context cleanup and destroy private stdin; do not require browser disconnected to notice a closed main page. Preserve current native HTTP confinement/auth/bootstrap behavior and fixed diagnostics.\n- frontend/trusted-client.node-test.mjs: add a provider-free actual Node child regression with synthetic private bootstrap held open and an ephemeral SDK test seam that emits main-page close without browser disconnected. Require bounded child exit and cleanup; preserve all original tests/assertions. The SDK seam is a fixture, not real browser evidence. Do not install or copy a runtime.\n- docs/local-client-session.md: document the supported main-page terminal condition and accurately distinguish fixture/native-source verification from later real browser acceptance.\n\nNo host, launcher, workflow, dependency, frontend application, governance instruction or credential source change. No check weakening. Source identity remains separate from Owner policy confirmation and privileged adapters; this does not complete #118/#384.\n\n## New exact authority and publication\n\nReuse controller F:/Nerelan-issue1027-frontend-audit; preserve its five generated gates. New branch codex/issue118-client-page-close-r3-v1-20261007 from explicit integration codex/issue118-native-browser-acceptance-r3-v3-20261004@af707142ce037e7392111db442419bf2ac7c7b06. One new immutable Decision-only activation, existing canonical gates/preflight/readiness, first exact Draft before source edits, one product commit, two pushes, one Draft, up to two description updates. No staging of runtime/helpers/evidence/generated gates. No ready/merge/main/history rewrite/tag/release/deploy.\n\nAllow up to two source corrections and two provider-free development invocations, then three required checks: full tests/platform_v1 with only original installed-OpenCode opt-in exclusions, actual tests/test_path_a_gate.py, and committed exact-head focused launcher/trusted-client/bootstrap/session tests including native Node. git diff --check and existing publication-readiness required. Observe original natural exact-head CI logs/JUnit; no dispatch or rerun. Any failed mandatory check blocks product publication; no automatic successor/reset.\n\nExact check commands use known C:/Program Files/Python313/python.exe -B -X utf8 -m pytest -q. Focused development/exact-head paths are tests/platform_v1/test_dev_up_contract.py, test_trusted_client_bootstrap.py, test_task_client_auth.py, test_trusted_host.py, test_trusted_host_lifecycle.py and test_local_client_session.py (all six beneath tests/platform_v1); the existing bootstrap test invokes the native Node suite. Each focused invocation<=900s, full Platform<=2400s, Path A<=120s. Use a fresh basetemp child under F:/nrl-pageclose118-v1, creating its empty parent before the first invocation. Full Platform excludes exactly the original four opt-ins: test_task3c_v6_production_relay.py::TestCombinedTrustedHostInstalledOpenCodeE2E::test_real_task_api_opencode_relay_fake_provider_end_to_end; test_task3c_v4_repairs.py::TestInstalledOpenCodeFakeProviderSmoke::test_installed_opencode_fake_provider_end_to_end; test_task3c_v5_opencode_probe.py::TestDirectFakeProviderControl::test_opencode_direct_fake_provider; test_task3c_v5_opencode_probe.py::TestRelayFakeProviderRun::test_opencode_relay_fake_provider (each beneath tests/platform_v1). No other deselection/skip or baseline change.\n\n## Included real acceptance after source and native CI pass\n\nExactly one new owned clone F:/nrl-auth118-native4 on the verified product commit, isolated cacheDir, existing dependencies without install/shared-cache modification, one stack start<=180s, one browser start, two observation invocations<=180s each, one identity-bound cleanup<=120s. Ports18877/18878/18879 must be free; healthy existing runtimes and previous owned clones remain untouched. Existing approved known Node and Microsoft-signed Edge154.0.4258.62 fingerprints must match immediately before launch. No models/provider/auth probes, credentials, tasks/window activation or privileged side effects.\n\nExternal observer changes are included: replace reserved HOME with a task-specific variable; add a static reserved-variable check before runtime; restore only the identity-bound owned native window to Normal via WindowPattern before PrintWindow capture, without relying on foreground or capturing another window. Verify actual home/tasks/settings pixels, explicit frontend-frame Task API200, unrelated missing-capability/no-Origin401 and health readiness-only; close the supported main page/window via native UI and require original broker exit/readiness false before canonical cleanup. Missing/blank pixels or unexecuted HTTP evidence are unverified, never acceptance. Preserve failures and perform no second runtime start.\n\nFreeze a new 90-minute absolute cutoff at first activation under this new approval; do not renew after activation. This new scope does not alter any previous cutoff or immutable Decision. Source totals begin with dev6/corrections7 spent; up to two additional allowed, not resets. Prior runtime startups3, browser launches2, observations4 remain. If this phase starts its runtime, aggregates become startups4/browser3/observations<=6. Actual source spending is charged as incurred.\n\nThis combined new grant includes all named source repair, checks, exact Draft publication and one later real acceptance so covered steps do not need repeated approval. It does not grant independent acceptance/landing or other #118 phases. Current v3 source correction budget is zero and runtime startup budget exhausted, so none of these new operations is authorized until explicit Owner approval is recorded and a fresh immutable Decision is activated.\n\nOWNER EXPLICITLY APPROVED this exact three-file repair/check/CI/one-real-acceptance proposal in the chat on2026-10-07, and delegated routine covered corrections/checks/acceptance without repeated confirmation. This is recorded Owner approval, not Agent self-issued authority. All prior failures/spending remain. No further runtime startup or scope/budget/expiry widening is implied.\n\nFROZEN_START=2026-10-07T08:32:39.178206+00:00; EXPIRES_AT=2026-10-07T10:02:39.178206+00:00",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "frontend/trusted-client.mjs",
        "frontend/trusted-client.node-test.mjs",
        "docs/local-client-session.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "native.validation",
      "command": "# Bounded page-close source repair + one real acceptance \u2014 pending Owner approval\n\nActual v3 evidence: source86caba starts at configured frontend18879 with ready private broker. After identity-bound native WindowPattern.Close, browser root has no main window but still exists; original broker remains after25seconds and host readiness staystrue. Canonical owned cleanup succeeded with both Windows Jobs empty. Observation1's PowerShell HOME error and unavailable minimized-window pixels remain recorded, not waived or represented as product acceptance. No positive/negative HTTP status or settings-navigation result is claimed. Draft1086 is terminal/unaccepted/unmerged.\n\n## Exact prospective source scope\n\nOnly these three product paths may change:\n\n- frontend/trusted-client.mjs: register the supported main frontend page's close event before navigation; treat that page close as a terminal client-session condition alongside private-input end and browser disconnected. Reuse Playwright's event interface. Always finish browser/context cleanup and destroy private stdin; do not require browser disconnected to notice a closed main page. Preserve current native HTTP confinement/auth/bootstrap behavior and fixed diagnostics.\n- frontend/trusted-client.node-test.mjs: add a provider-free actual Node child regression with synthetic private bootstrap held open and an ephemeral SDK test seam that emits main-page close without browser disconnected. Require bounded child exit and cleanup; preserve all original tests/assertions. The SDK seam is a fixture, not real browser evidence. Do not install or copy a runtime.\n- docs/local-client-session.md: document the supported main-page terminal condition and accurately distinguish fixture/native-source verification from later real browser acceptance.\n\nNo host, launcher, workflow, dependency, frontend application, governance instruction or credential source change. No check weakening. Source identity remains separate from Owner policy confirmation and privileged adapters; this does not complete #118/#384.\n\n## New exact authority and publication\n\nReuse controller F:/Nerelan-issue1027-frontend-audit; preserve its five generated gates. New branch codex/issue118-client-page-close-r3-v1-20261007 from explicit integration codex/issue118-native-browser-acceptance-r3-v3-20261004@af707142ce037e7392111db442419bf2ac7c7b06. One new immutable Decision-only activation, existing canonical gates/preflight/readiness, first exact Draft before source edits, one product commit, two pushes, one Draft, up to two description updates. No staging of runtime/helpers/evidence/generated gates. No ready/merge/main/history rewrite/tag/release/deploy.\n\nAllow up to two source corrections and two provider-free development invocations, then three required checks: full tests/platform_v1 with only original installed-OpenCode opt-in exclusions, actual tests/test_path_a_gate.py, and committed exact-head focused launcher/trusted-client/bootstrap/session tests including native Node. git diff --check and existing publication-readiness required. Observe original natural exact-head CI logs/JUnit; no dispatch or rerun. Any failed mandatory check blocks product publication; no automatic successor/reset.\n\nExact check commands use known C:/Program Files/Python313/python.exe -B -X utf8 -m pytest -q. Focused development/exact-head paths are tests/platform_v1/test_dev_up_contract.py, test_trusted_client_bootstrap.py, test_task_client_auth.py, test_trusted_host.py, test_trusted_host_lifecycle.py and test_local_client_session.py (all six beneath tests/platform_v1); the existing bootstrap test invokes the native Node suite. Each focused invocation<=900s, full Platform<=2400s, Path A<=120s. Use a fresh basetemp child under F:/nrl-pageclose118-v1, creating its empty parent before the first invocation. Full Platform excludes exactly the original four opt-ins: test_task3c_v6_production_relay.py::TestCombinedTrustedHostInstalledOpenCodeE2E::test_real_task_api_opencode_relay_fake_provider_end_to_end; test_task3c_v4_repairs.py::TestInstalledOpenCodeFakeProviderSmoke::test_installed_opencode_fake_provider_end_to_end; test_task3c_v5_opencode_probe.py::TestDirectFakeProviderControl::test_opencode_direct_fake_provider; test_task3c_v5_opencode_probe.py::TestRelayFakeProviderRun::test_opencode_relay_fake_provider (each beneath tests/platform_v1). No other deselection/skip or baseline change.\n\n## Included real acceptance after source and native CI pass\n\nExactly one new owned clone F:/nrl-auth118-native4 on the verified product commit, isolated cacheDir, existing dependencies without install/shared-cache modification, one stack start<=180s, one browser start, two observation invocations<=180s each, one identity-bound cleanup<=120s. Ports18877/18878/18879 must be free; healthy existing runtimes and previous owned clones remain untouched. Existing approved known Node and Microsoft-signed Edge154.0.4258.62 fingerprints must match immediately before launch. No models/provider/auth probes, credentials, tasks/window activation or privileged side effects.\n\nExternal observer changes are included: replace reserved HOME with a task-specific variable; add a static reserved-variable check before runtime; restore only the identity-bound owned native window to Normal via WindowPattern before PrintWindow capture, without relying on foreground or capturing another window. Verify actual home/tasks/settings pixels, explicit frontend-frame Task API200, unrelated missing-capability/no-Origin401 and health readiness-only; close the supported main page/window via native UI and require original broker exit/readiness false before canonical cleanup. Missing/blank pixels or unexecuted HTTP evidence are unverified, never acceptance. Preserve failures and perform no second runtime start.\n\nFreeze a new 90-minute absolute cutoff at first activation under this new approval; do not renew after activation. This new scope does not alter any previous cutoff or immutable Decision. Source totals begin with dev6/corrections7 spent; up to two additional allowed, not resets. Prior runtime startups3, browser launches2, observations4 remain. If this phase starts its runtime, aggregates become startups4/browser3/observations<=6. Actual source spending is charged as incurred.\n\nThis combined new grant includes all named source repair, checks, exact Draft publication and one later real acceptance so covered steps do not need repeated approval. It does not grant independent acceptance/landing or other #118 phases. Current v3 source correction budget is zero and runtime startup budget exhausted, so none of these new operations is authorized until explicit Owner approval is recorded and a fresh immutable Decision is activated.\n\nOWNER EXPLICITLY APPROVED this exact three-file repair/check/CI/one-real-acceptance proposal in the chat on2026-10-07, and delegated routine covered corrections/checks/acceptance without repeated confirmation. This is recorded Owner approval, not Agent self-issued authority. All prior failures/spending remain. No further runtime startup or scope/budget/expiry widening is implied.\n\nFROZEN_START=2026-10-07T08:32:39.178206+00:00; EXPIRES_AT=2026-10-07T10:02:39.178206+00:00",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution",
        "commit",
        "source_edit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "native.publication",
      "command": "Two exact pushes and one Draft, two descriptions; no landing. codex/issue118-client-page-close-r3-v1-20261007",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "runtime_scratch_policy": {
    "paths": [],
    "stage_allowed": false,
    "note": "Exactly new owned external runtimeF:\\nrl-auth118-native4; one clone/stack/browser, readonly shared deps, cacheDir safety config only. Never stage runtime/evidence. Existing runtimes preserved."
  },
  "workstream_id": "issue118-client-page-close-r3-v1",
  "source_issues": [
    118,
    384
  ],
  "local_browser_launch_limit": 1,
  "execution_window_hours": 1.5,
  "integration_observation_surface": "user_local_exact_planning_base_fresh_branch",
  "runtime_host_launch_limit": 1,
  "frontend_launch_limit": 1,
  "approval_event_or_time": "2026-10-07T08:32:39.178206+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 2,
  "runtime_acceptance_limits": {
    "clone": 1,
    "stack_start": 1,
    "browser_start": 1,
    "observations": 2,
    "normal_cleanup": 1,
    "source_corrections": 2,
    "source_checks_replay": 3,
    "prior_source_dev_spent": 6,
    "prior_source_corrections_spent": 7,
    "prior_runtime_failed_startups": 1,
    "cumulative_runtime_startup_limit": 4,
    "prior_runtime_startups": 3,
    "prior_browser_startups": 2,
    "prior_observations_spent": 4,
    "prior_source_original_deadline": "2026-10-07T09:49:02.635253+00:00",
    "owned_runtime_root": "F:\\nrl-auth118-native4",
    "expires_at": "2026-10-07T10:02:39.178206+00:00"
  },
  "development_check_run_limit": 2,
  "development_correction_round_limit": 2,
  "mandatory_pytest_process_limit": 3,
  "owned_test_scratch_root": "F:\\nrl-pageclose118-v1",
  "cumulative_prior_development_checks": 6,
  "cumulative_prior_correction_rounds": 7,
  "cumulative_development_check_limit": 8,
  "cumulative_correction_round_limit": 9
}
```
