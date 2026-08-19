import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { HomePage } from "@/routes/home";


describe("Platform V2 goal workspace", () => {
  it("shows platform status, goal composer, recent goals and agent progress", async () => {
    renderWithProviders(<HomePage />);
    expect(screen.getByRole("heading", { name: "今天想完成什么？" })).toBeInTheDocument();
    expect(screen.getByLabelText("描述最终目标")).toBeInTheDocument();
    expect(screen.getByText("策略在服务端执行；浏览器不持有 shell、文件系统或模型凭据。")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("协调器在线")).toBeInTheDocument());
    expect(screen.getByText("Agent progress")).toBeInTheDocument();
    expect(screen.getByText("实现协调与恢复链路")).toBeInTheDocument();
  });

  it("requires explicit autonomous-window confirmation before starting", async () => {
    const user = userEvent.setup();
    renderWithProviders(<HomePage />);
    const submit = screen.getByLabelText("规划并运行");
    await user.type(screen.getByLabelText("描述最终目标"), "完成一个可以恢复的多 Agent 任务");
    expect(submit).toBeDisabled();
    await user.click(screen.getByText("启用 2 小时自治窗口"));
    expect(submit).toBeEnabled();
    await user.click(submit);
    await waitFor(() => expect(screen.getAllByText("完成一个可以恢复的多 Agent 任务").length).toBeGreaterThan(0));
  });
});
