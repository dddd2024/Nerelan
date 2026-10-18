import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { RunsPage } from "@/routes/runs";

describe("source-backed Goal to Task to Run navigation", () => {
  it("links a run to its exact Goal and Task without mutating history", async () => {
    renderWithProviders(<RunsPage />, { initialEntries: ["/runs"] });
    const goalLink = await screen.findByTestId("run-goal-detail-link-task-demo-1");
    expect(goalLink).toHaveAttribute("href", "/approvals?goal=goal-demo-platform");
    expect(screen.getByTestId("run-goal-history-link-task-demo-1"))
      .toHaveAttribute("href", "/runs?goal=goal-demo-platform");
    expect(screen.getByTestId("run-task-detail-link-task-demo-1"))
      .toHaveAttribute("href", "/tasks/task-demo-1");
  });

  it("lists distinct task runs when a direct Goal ID matches on this page", async () => {
    renderWithProviders(<RunsPage />, { initialEntries: ["/runs?goal=goal-demo-platform"] });
    expect(await screen.findByTestId("run-task-demo-1")).toBeInTheDocument();
    expect(screen.getByTestId("run-task-demo-2")).toBeInTheDocument();
    expect(screen.getByTestId("runs-goal-filter")).toHaveTextContent("当前页 3 条关联运行");
    expect(screen.getByTestId("runs-goal-filter")).toHaveTextContent("未跨页汇总");
    expect(screen.getByRole("link", { name: "查看全部运行" })).toHaveAttribute("href", "/runs");
  });

  it("does not claim nonexistent global history from an empty current page", async () => {
    renderWithProviders(<RunsPage />, { initialEntries: ["/runs?goal=not-loaded-goal"] });
    expect(await screen.findByTestId("runs-goal-page-empty")).toHaveTextContent(
      "不能据此判定历史记录不存在",
    );
    expect(screen.queryByTestId("run-task-demo-1")).not.toBeInTheDocument();
  });
});
