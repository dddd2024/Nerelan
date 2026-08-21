import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { HomePage } from "@/routes/home";


describe("Platform V2 Home Workspace V2", () => {
  async function homeReady() {
    renderWithProviders(<HomePage />);
    await waitFor(() => expect(screen.getByText("协调器在线")).toBeInTheDocument(), { timeout: 4000 });
  }

  it("renders the centered single-column layout: composer, current execution, recent goals", async () => {
    await homeReady();
    expect(screen.getByRole("heading", { name: "今天想完成什么？" })).toBeInTheDocument();
    expect(screen.getByLabelText("描述最终目标")).toBeInTheDocument();
    expect(screen.getByText("Agent progress")).toBeInTheDocument();
    expect(screen.getByText("实现协调与恢复链路")).toBeInTheDocument();
    const current = screen.getByTestId("current-execution-section");
    const recent = screen.getByTestId("recent-goals-section");
    expect(current).toBeInTheDocument();
    expect(recent).toBeInTheDocument();
    expect(current.compareDocumentPosition(recent) & Node.DOCUMENT_POSITION_FOLLOWING).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
  });

  it("removes the permanent right rail and keeps recent goals capped at 3", async () => {
    await homeReady();
    const main = screen.getByTestId("platform-home");
    expect(main.querySelector("[class*='grid-cols']")).toBeNull();
    expect(main.querySelector("aside")).toBeNull();
    expect(screen.queryByText("Multi-agent workspace")).not.toBeInTheDocument();
    const recentSection = screen.getByTestId("recent-goals-section");
    const recentButtons = recentSection.querySelectorAll("button[type='button']");
    expect(recentButtons.length).toBeLessThanOrEqual(3);
  });

  it("shows authoritative current-execution state from the selected goal", async () => {
    await homeReady();
    const goalTitle = screen.getByRole("heading", { name: "完善无人值守多 Agent 平台" });
    expect(goalTitle).toBeInTheDocument();
    const currentSection = screen.getByTestId("current-execution-section");
    expect(currentSection).toContainElement(screen.getByText("Agent progress"));
    expect(currentSection).toContainElement(screen.getByText("分析目标与代码库"));
    expect(currentSection).toContainElement(screen.getByText("验证并准备证据"));
  });

  it("requires explicit autonomous-window confirmation before starting", async () => {
    await homeReady();
    const user = userEvent.setup();
    const submit = screen.getByLabelText("规划并运行");
    await user.type(screen.getByLabelText("描述最终目标"), "完成一个可以恢复的多 Agent 任务");
    expect(submit).toBeDisabled();
    await user.click(screen.getByText("启用 2 小时自治窗口"));
    expect(submit).toBeEnabled();
    await user.click(submit);
    await waitFor(() => expect(screen.getAllByText("完成一个可以恢复的多 Agent 任务").length).toBeGreaterThan(0));
  });
});
