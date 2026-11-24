import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { GoalProgress } from "@/components/goal-progress";
import type { PlatformGoal } from "@/lib/platform-client";
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


describe("task-first active Goal workspace", () => {
  // Activity-stream cases moved to goal-timeline.test.tsx with the unified goal timeline.
  it("keeps progress compact without a visible module heading or repeated Goal title", () => {
    renderWithProviders(<GoalProgress goal={GOAL} />);

    expect(screen.getByText("执行进度")).toHaveClass("sr-only");
    expect(screen.queryByText("Task-first workspace")).not.toBeInTheDocument();
    expect(screen.getByText("Converge active workspace")).toBeInTheDocument();
    expect(screen.getByText("Agent 正在执行")).toBeInTheDocument();
    expect(screen.getByTestId("goal-progress-summary")).toHaveTextContent("0/1");
  });

  it("makes the selected Goal the primary Home heading and keeps healthy coordinator state quiet", () => {
    const source = readFileSync("src/routes/home.tsx", "utf8");

    expect(source).toContain('data-testid="active-goal-header"');
    // The Goal title is still the primary heading; it is now derived through
    // `goalTitle` (drops #N and [Tag] prefixes) so machine-written titles do not become a text wall.
    expect(source).toContain("goalTitle(detailGoal");
    expect(source).toContain('data-testid="active-goal-stream"');
    expect(source).toContain("platform.coordinator.enabled");
    expect(source).toContain('? "sr-only"');
  });
});
