const bundle = {
  panels: ["Dashboard", "Decision", "Command-plan", "Jobs", "Tasks", "Handoff", "Import", "Gate", "Audit", "Settings"],
  fixtures: {
    dashboard: { decision_id: "decision_20260704_manual_mode_web_orchestrator_mvp_big_step_v1", round_id: "round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1", mode: "manual", command_count: 23, dispatch_enabled: false, production_service: false },
    decision: { status: "APPROVED", authority: "project_state/decision_packet.md", task_packet_role: "background_only" },
    commandPlan: { plan_status: "PASSED", command_count: 23, command_plan_is_authority: true },
    jobs: [{ job_id: "job_demo_20260704_manual_mode_web_orchestrator_mvp_big_step_v1", status: "READY", dispatch_enabled: false }],
    tasks: [{ task_id: "demo_manual_mode_task", status: "READY", real_sample: false }],
    handoff: { handoff_id: "handoff_job_demo_20260704_manual_mode_web_orchestrator_mvp_big_step_v1", runner_dispatch_enabled: false, external_tool_invocation: false },
    importPreview: { preview_status: "PASSED", verified_evidence: false, manual_claim_only: true },
    gate: { result: "manual_mode_orchestrator_result.json", snapshot: "manual_mode_orchestrator_snapshot.json" },
    audit: { model_api_invocation: false, full_solve_reports_read: false },
    settings: { fixture_only: true, network_calls: false, build_step_required: false }
  }
};

const tabs = document.querySelector("#tabs");
const panel = document.querySelector("#panel");

function keyFor(name) {
  return name.toLowerCase().replace("-", "").replace("commandplan", "commandPlan").replace("import", "importPreview");
}

function render(name) {
  [...tabs.querySelectorAll("button")].forEach((button) => {
    button.dataset.active = button.textContent === name ? "true" : "false";
  });
  const key = keyFor(name);
  const data = bundle.fixtures[key] ?? bundle.fixtures.dashboard;
  panel.innerHTML = `
    <div class="panel-head">
      <h2>${name}</h2>
      <span>${data.dispatch_enabled === false || data.runner_dispatch_enabled === false || data.network_calls === false ? "Manual review only" : "Preview"}</span>
    </div>
    <pre>${JSON.stringify(data, null, 2)}</pre>
  `;
}

bundle.panels.forEach((name) => {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = name;
  button.addEventListener("click", () => render(name));
  tabs.appendChild(button);
});

render("Dashboard");
