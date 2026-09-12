import { afterEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { RoadmapPage } from "@/routes/roadmap";
import * as platformClient from "@/lib/platform-client";

afterEach(() => vi.restoreAllMocks());

describe("Roadmap page", () => {
  it("keeps completed phase and member execution separate from verification and delivery", async () => {
    vi.spyOn(platformClient, "fetchRoadmap").mockResolvedValue([{
      id: "phase-ended", title: "Execution ended", position: 0, description: "", derived_status: "COMPLETED",
      goals: [{ id: "goal-ended", title: "Ready for review", status: "COMPLETED", repository: "owner/repo", updated_at: "2026-09-12T00:00:00Z" }],
      created_at: "2026-09-12T00:00:00Z", updated_at: "2026-09-12T00:00:00Z",
    }]);
    renderWithProviders(<RoadmapPage />);
    expect(await screen.findByTestId("roadmap-phase-status-phase-ended")).toHaveTextContent("执行完成，待审查");
    expect(screen.getByTestId("roadmap-goal-goal-ended")).toHaveTextContent("执行完成，待审查");
    expect(screen.getByText(/功能验证、审查与交付仍需分别确认/)).toBeVisible();
    expect(screen.queryByText("已完成")).not.toBeInTheDocument();
    expect(screen.queryByText("功能已验证")).not.toBeInTheDocument();
  });
  it("renders phases with derived status and member goals", async () => {
    renderWithProviders(<RoadmapPage />);
    expect(screen.getByRole("heading", { name: /路线图/ })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("P0 读模型")).toBeInTheDocument());

    expect(screen.getByTestId("roadmap-phase-status-phase-demo-1").textContent).toBe(
      "进行中",
    );
    expect(screen.getByText("完善无人值守多 Agent 平台")).toBeInTheDocument();
    expect(screen.getByText("预算与成本硬上限")).toBeInTheDocument();
    expect(screen.getAllByText("P1 无人值守").length).toBeGreaterThan(0);
  });

  it("marks empty phases as planned with an empty-goal hint", async () => {
    renderWithProviders(<RoadmapPage />);
    await waitFor(() => expect(screen.getByText("P1 无人值守")).toBeInTheDocument());
    expect(screen.getByTestId("roadmap-phase-status-phase-demo-2").textContent).toBe(
      "规划中",
    );
    expect(screen.getByText("该阶段还没有挂载目标。")).toBeInTheDocument();
  });

  it("documents that phase status is derived, not independently maintained", async () => {
    renderWithProviders(<RoadmapPage />);
    expect(
      await screen.findByText(/阶段状态始终由成员目标的状态推导/),
    ).toBeInTheDocument();
  });
});
