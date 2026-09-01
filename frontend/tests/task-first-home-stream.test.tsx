import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { GoalCurrentActivity } from "@/components/goal-current-activity";
import { GoalProgress } from "@/components/goal-progress";
import type { PlatformAgentRun, PlatformGoal } from "@/lib/platform-client";
import { renderWithProviders } from "./test-utils";

const GOAL: PlatformGoal = {
  id: "goal-v8",
  title: "Task-first workspace",
  objective: "Keep execution truth continuous and semantic.",
  repository: "dddd2024/reverse-agent",
  status: "RUNNING",
  revision: 1,
  spec_markdown: "",
  plan_markdown: "",
  tasks: [],
  acceptance_criteria: [],
  artifact_digest: "",
  executor_kind: "opencode",
  orchestration_mode: "sequential_team",
  binding_ref: "",
  window_id: "window-v8",
  created_at: "2026-09-01T09:30:00Z",
  updated_at: "2026-09-01T09:45:00Z",
  task_links: [
    {
      task_id: "task-v8",
      plan_task_id: "T001",
      status: "RUNNING",
      title: "Converge active workspace",
    },
  ],
};

const RUN = {
  task_id: "task-v8",
  title: "[Task-first workspace] T001 Converge active workspace",
  repository: "dddd2024/reverse-agent",
  status: "RUNNING",
  state: "RUNNING",
  executor_kind: "opencode",
  orchestration_mode: "sequential_team",
  created_at: "2026-09-01T09:30:00Z",
  updated_at: "2026-09-01T09:45:00Z",
  failure_classification: "",
  goal_id: "goal-v8",
  goal_title: "Task-first workspace",
  window_id: "window-v8",
  liveness: "ACTIVE",
  last_activity_at: new Date().toISOString(),
  current_agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
  current_activity: {
    category: "EDIT",
    title: "Updated semantic stream",
    description: "Reduced default telemetry.",
    agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
    timestamp: "2026-09-01T09:42:00Z",
  },
  activity: [
    {
      id: "event-v8",
      task_id: "task-v8",
      timestamp: "2026-09-01T09:41:00Z",
      category: "EDIT",
      title: "Updated active workspace",
      description: "",
      agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
      stage: "EXECUTE",
      path: "frontend/src/routes/home.tsx",
    },
  ],
  change_summary: { file_count: 3, additions: 42, deletions: 11 },
  events: [],
  changed_files: [],
  usage: {
    status: "USAGE_UNKNOWN",
    input_units: 0,
    output_units: 0,
    reasoning_units: 0,
    cache_read_units: 0,
    cache_write_units: 0,
    cost_micro_units: 0,
    total_token_units: 0,
    observation_count: 0,
    unknown_observation_count: 0,
    provenance_ids: [],
    per_role: [],
  },
  budget: null,
  publication: null,
} as PlatformAgentRun;

describe("task-first active Goal workspace", () => {
  it("keeps progress compact without a visible module heading or repeated Goal title", () => {
    renderWithProviders(<GoalProgress goal={GOAL} />);

    expect(screen.getByText("Agent progress")).toHaveClass("sr-only");
    expect(screen.queryByText("Task-first workspace")).not.toBeInTheDocument();
    expect(screen.getByText("Converge active workspace")).toBeInTheDocument();
    expect(screen.getByText("Agent 正在执行")).toBeInTheDocument();
    expect(screen.getByTestId("goal-progress-summary")).toHaveTextContent("0/1");
  });

  it("renders semantic activity without default exact clock timestamps", () => {
    renderWithProviders(<GoalCurrentActivity goal={GOAL} runs={[RUN]} />);

    expect(screen.getByText("Agent 活动")).toHaveClass("sr-only");
    expect(screen.getByTestId("goal-activity-liveness")).toHaveClass("sr-only");

    const row = screen.getByTestId("goal-activity-event-event-v8");
    expect(row).toHaveTextContent("Updated active workspace");
    expect(row).toHaveTextContent("Coder");
    expect(row).toHaveTextContent("编辑");
    expect(row).toHaveTextContent("frontend/src/routes/home.tsx");
    expect(row.textContent).not.toContain("09:41");
    expect(row.textContent).not.toContain("09-01");
  });

  it("makes the selected Goal the primary Home heading and keeps healthy coordinator state quiet", () => {
    const source = readFileSync("src/routes/home.tsx", "utf8");

    expect(source).toContain('data-testid="active-goal-header"');
    expect(source).toContain("{detailGoal.title}");
    expect(source).toContain('data-testid="active-goal-stream"');
    expect(source).toContain("platform.coordinator.enabled");
    expect(source).toContain('? "sr-only"');
  });
});
