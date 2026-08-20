import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { RoadmapPage } from "@/routes/roadmap";


describe("Roadmap page", () => {
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
