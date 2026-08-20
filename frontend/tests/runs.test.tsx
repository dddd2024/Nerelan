import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { RunsPage } from "@/routes/runs";


describe("Agent Runs page", () => {
  it("renders the derived run timeline with state badges", async () => {
    renderWithProviders(<RunsPage />);
    expect(screen.getByRole("heading", { name: /Agent 运行/ })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByTestId("run-task-demo-1")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("run-state-task-demo-1").textContent).toBe(
      "等待人工审查",
    );
    expect(screen.getByTestId("run-state-task-demo-2").textContent).toBe("运行中");
  });

  it("shows the goal link and publication PR link per run", async () => {
    renderWithProviders(<RunsPage />);
    await waitFor(() =>
      expect(screen.getByTestId("run-goal-task-demo-1")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("run-goal-task-demo-1").textContent).toContain(
      "完善无人值守多 Agent 平台",
    );

    const pr = screen.getByTestId("run-pr-task-demo-1");
    expect(pr).toHaveAttribute(
      "href",
      "https://github.com/dddd2024/reverse-agent/pull/97",
    );
    expect(pr.textContent).toContain("#97");

    expect(screen.queryByTestId("run-pr-task-demo-2")).not.toBeInTheDocument();
  });

  it("states the read-model contract in the page copy", () => {
    renderWithProviders(<RunsPage />);
    expect(
      screen.getByText(/由任务库、目标链接与发布记录派生的只读时间线/),
    ).toBeInTheDocument();
  });
});
