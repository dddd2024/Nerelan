import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { GoalProgress } from "@/components/goal-progress";
import type { PlatformGoal } from "@/lib/platform-client";
import { renderWithProviders } from "./test-utils";

function goalWithStatus(status: string): PlatformGoal {
  return {
    id: "goal-a", title: "Goal", objective: "Work", repository: "owner/repo", status: "RUNNING", revision: 1,
    spec_markdown: "", plan_markdown: "", tasks: [], acceptance_criteria: [], artifact_digest: "",
    executor_kind: "deterministic_fixture", orchestration_mode: "single", binding_ref: "", window_id: "",
    created_at: "", updated_at: "",
    task_links: [{ task_id: "task/a ?&", plan_task_id: "T001", title: "Implement result", status }],
  };
}

describe("Goal progress status truth", () => {
  it("shows interruption visibly and links the exact task without offering unconditional resume", () => {
    renderWithProviders(<GoalProgress goal={goalWithStatus("INTERRUPTED")} />);
    expect(screen.getByText("执行已中断")).toBeVisible();
    expect(screen.queryByText("等待依赖完成")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "查看 Implement result 的中断运行" })).toHaveAttribute("href", "/runs?task=task%2Fa%20%3F%26");
    expect(screen.queryByRole("button", { name: /恢复/ })).not.toBeInTheDocument();
    expect(screen.getByTestId("goal-progress-summary")).toHaveTextContent("0/1");
  });

  it.each([
    ["QUEUED", "等待依赖完成"],
    ["RUNNING", "Agent 正在执行"],
    ["READY_FOR_REVIEW", "执行完成，待审查"],
    ["FAILED", "需要处理阻塞"],
  ])("keeps %s status semantics and links the exact materialized task", (status, label) => {
    renderWithProviders(<GoalProgress goal={goalWithStatus(status)} />);
    expect(screen.queryByText("执行已中断")).not.toBeInTheDocument();
    expect(screen.getByText(label)).toBeVisible();
    expect(screen.getByRole("link", { name: "查看 Implement result 的运行" })).toHaveAttribute("href", "/runs?task=task%2Fa%20%3F%26");
    expect(screen.queryByRole("button", { name: /恢复/ })).not.toBeInTheDocument();
    expect(screen.getByTestId("goal-progress-summary")).toHaveTextContent(status === "READY_FOR_REVIEW" ? "1/1" : "0/1");
  });
});
