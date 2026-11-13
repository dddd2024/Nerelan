import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import type { PlatformGoal, PlatformGoalTaskLink } from "@/lib/platform-client";
import { goalProgressLine } from "@/lib/goal-progress-line";

const link = (over: Partial<PlatformGoalTaskLink>): PlatformGoalTaskLink => ({
  task_id: "t1", plan_task_id: "T001", title: "改 README", status: "QUEUED", ...over,
});

describe("goalProgressLine", () => {
  it("says what the agent is doing while a task runs", () => {
    const line = goalProgressLine({ status: "RUNNING", task_links: [link({
      status: "RUNNING", activity: { type: "EXECUTOR_PROGRESS", title: "Read", description: "读取 README.md", timestamp: "" },
    })] });
    expect(line).toEqual({ tone: "live", text: "正在做：读取 README.md" });
    expect(goalProgressLine({ status: "RUNNING", task_links: [link({ status: "RUNNING" })] }).text)
      .toBe("正在做：Agent 已启动，等待第一条动作");
  });

  it("says why it stopped and how many tries it took", () => {
    const line = goalProgressLine({ status: "BLOCKED", task_links: [link({
      status: "FAILED",
      failure: { classification: "executor_stalled", detail: "opencode_stalled:900", message: "" },
      attempts: [{ task_id: "t0", status: "FAILED" } as never],
    })] });
    expect(line.tone).toBe("stopped");
    expect(line.text).toMatch(/^已停下：.+（已试 2 次）$/);
  });

  it("treats a cancelled step as stopped, not queued", () => {
    expect(goalProgressLine({ status: "BLOCKED", task_links: [link({ status: "READY_FOR_REVIEW" }), link({ task_id: "t2", status: "CANCELLED" })] }))
      .toEqual({ tone: "stopped", text: "已停下：有一步被取消" });
  });

  it("names what waits on the Owner before any task exists", () => {
    expect(goalProgressLine({ status: "DRAFT", task_links: [] }).text).toBe("草稿：等你生成计划");
    expect(goalProgressLine({ status: "PLANNED" }).text).toBe("计划已生成：等你审阅");
  });

  it("counts finished steps and says when all are ready for review", () => {
    expect(goalProgressLine({ status: "RUNNING", task_links: [link({ status: "READY_FOR_REVIEW" }), link({ task_id: "t2" })] }).text)
      .toBe("排队中：已完成 1/2 步");
    expect(goalProgressLine({ status: "COMPLETED", task_links: [link({ status: "READY_FOR_REVIEW" })] }))
      .toEqual({ tone: "done", text: "执行完成，等你审查" });
  });
});

const GOALS = [
  { id: "g-old", title: "#7 修登录", objective: "旧的尝试", repository: "o/r", status: "BLOCKED", updated_at: "2026-11-10T00:00:00Z", task_links: [] },
  { id: "g-new", title: "#7 修登录", objective: "新的尝试", repository: "o/r", status: "RUNNING", updated_at: "2026-11-12T00:00:00Z", task_links: [] },
  { id: "g-other", title: "整理文档", objective: "docs", repository: "o/r", status: "DRAFT", updated_at: "2026-11-11T00:00:00Z", task_links: [] },
] as unknown as PlatformGoal[];

const navigate = vi.fn();
vi.mock("react-router", async (actual) => ({ ...(await actual<typeof import("react-router")>()), useNavigate: () => navigate }));
vi.mock("@/hooks/use-platform", () => ({ useGoals: () => ({ data: GOALS }) }));
vi.mock("@/hooks/use-tasks", () => ({ useTasks: () => ({ data: [], isLoading: false, isError: false }) }));

describe("search finds goals", () => {
  it("lists one entry per issue and opens the goal", async () => {
    const { ConversationPanel } = await import("@/components/conversation-panel");
    const onClose = vi.fn();
    render(<MemoryRouter><ConversationPanel open onClose={onClose} /></MemoryRouter>);
    expect(screen.getByTestId("conversation-goal-g-new")).toBeInTheDocument();
    expect(screen.queryByTestId("conversation-goal-g-old")).not.toBeInTheDocument();

    await userEvent.type(screen.getByTestId("task-search-input"), "文档");
    expect(screen.getByTestId("conversation-goal-g-other")).toHaveTextContent("草稿：等你生成计划");
    expect(screen.queryByTestId("conversation-goal-g-new")).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId("conversation-goal-g-other"));
    expect(navigate).toHaveBeenCalledWith("/?goal=g-other");
    expect(onClose).toHaveBeenCalled();

    await userEvent.clear(screen.getByTestId("task-search-input"));
    await userEvent.type(screen.getByTestId("task-search-input"), "不存在的词");
    expect(screen.getByTestId("conversation-panel-empty")).toHaveTextContent("没有匹配的目标或任务。");
  });
});
