import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { act, type ReactNode, useState } from "react";
import { render as rtlRender, type RenderOptions } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HomePage } from "@/routes/home";
import * as platformClient from "@/lib/platform-client";
import type { PlatformGoal } from "@/lib/platform-client";

const DEMO_ID = "goal-demo-platform";

const COMPLETED_LINKS = [
  { task_id: "t1", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "分析目标与代码库" },
  { task_id: "t2", plan_task_id: "T002", status: "READY_FOR_REVIEW", title: "实现协调与恢复链路" },
  { task_id: "t3", plan_task_id: "T003", status: "READY_FOR_REVIEW", title: "验证并准备证据" },
] as const;

const BLOCKED_LINKS = [
  { task_id: "t1", plan_task_id: "T001", status: "FAILED", title: "分析目标与代码库" },
  { task_id: "t2", plan_task_id: "T002", status: "RUNNING", title: "实现协调与恢复链路" },
  { task_id: "t3", plan_task_id: "T003", status: "QUEUED", title: "验证并准备证据" },
] as const;

const CANCELLED_LINKS = [
  { task_id: "t1", plan_task_id: "T001", status: "CANCELLED", title: "分析目标与代码库" },
  { task_id: "t2", plan_task_id: "T002", status: "RUNNING", title: "实现协调与恢复链路" },
  { task_id: "t3", plan_task_id: "T003", status: "QUEUED", title: "验证并准备证据" },
] as const;

const DEFAULT_LINKS = [
  { task_id: "t1", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "分析目标与代码库" },
  { task_id: "t2", plan_task_id: "T002", status: "RUNNING", title: "实现协调与恢复链路" },
  { task_id: "t3", plan_task_id: "T003", status: "QUEUED", title: "验证并准备证据" },
] as const;

const ts = "2026-01-01T00:00:00Z";

function makeClient(staleTime = 0) {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime } },
  });
}

function Wrapper({ children, initialEntries, factory }: { children: ReactNode; initialEntries?: string[]; factory?: () => QueryClient }) {
  const client = useState(() => (factory ?? makeClient)())[0];
  const initial: { initialEntries?: string[] } = { initialEntries: initialEntries ?? ["/"] };
  return <QueryClientProvider client={client}><MemoryRouter {...initial}>{children}</MemoryRouter></QueryClientProvider>;
}

function render(ui: ReactNode, opts?: RenderOptions & { factory?: () => QueryClient; initialEntries?: string[] }) {
  return rtlRender(ui as Parameters<typeof rtlRender>[0], { wrapper: (props: { children: ReactNode }) => Wrapper(props as unknown as { children: ReactNode; factory?: () => QueryClient }), ...opts });
}

function seededClient(status: PlatformGoal["status"] = "RUNNING", links: readonly { task_id: string; plan_task_id: string; status: string; title: string }[] = DEFAULT_LINKS) {
  const goalData = makeGoalData(status, links);
  vi.mocked(platformClient.fetchGoal).mockResolvedValue(goalData);
  vi.mocked(platformClient.fetchGoals).mockResolvedValue([
    goalData,
    makeGoalData("COMPLETED", []),
    makeGoalData("APPROVED", []),
    makeGoalData("DRAFT", []),
  ] as PlatformGoal[]);
  const c = makeClient(5_000);
  c.setQueryData(["goals"], [
    goalData,
    makeGoalData("COMPLETED", []),
    makeGoalData("APPROVED", []),
    makeGoalData("DRAFT", []),
  ] as PlatformGoal[]);
  c.setQueryData(["goals", DEMO_ID], goalData);
  return c;
}

function makeGoalData(status: PlatformGoal["status"], links: readonly { task_id: string; plan_task_id: string; status: string; title: string }[]): PlatformGoal {
  return {
    id: DEMO_ID, title: "完善无人值守多 Agent 平台", objective: "目标 A", status,
    repository: "dddd2024/reverse-agent", revision: 2,
    spec_markdown: "# Spec", plan_markdown: "# Plan",
    tasks: [{ id: "T001", title: "分析目标与代码库", dependencies: [] }, { id: "T002", title: "实现协调与恢复链路", dependencies: ["T001"] }, { id: "T003", title: "验证并准备证据", dependencies: ["T002"] }],
    acceptance_criteria: ["任务可恢复"], artifact_digest: "b4a91c0e",
    executor_kind: "opencode", orchestration_mode: "sequential_team",
    binding_ref: "coding-default", window_id: "window-demo",
    created_at: ts, updated_at: ts, task_links: [...links],
  };
}

async function homeReady(seed = true) {
  render(<HomePage />, { factory: seed ? seededClient : makeClient });
  await waitFor(() => expect(screen.getByText("Agent progress")).toBeInTheDocument(), { timeout: 4000 });
}

beforeEach(() => {
  vi.spyOn(platformClient, "fetchGoal").mockResolvedValue(makeGoalData("RUNNING", DEFAULT_LINKS));
  vi.spyOn(platformClient, "fetchGoals").mockResolvedValue([
    makeGoalData("RUNNING", DEFAULT_LINKS),
    makeGoalData("COMPLETED", []),
  ] as PlatformGoal[]);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Platform V2 Home Workspace V2", () => {
  it("renders the centered single-column layout: composer, current execution, recent goals", async () => {
    await homeReady();
    expect(screen.getByRole("heading", { name: "今天想完成什么？" })).toBeInTheDocument();
    expect(screen.getByLabelText("描述最终目标")).toBeInTheDocument();
    expect(screen.getByText("Agent progress")).toBeInTheDocument();
    expect(screen.getByText("实现协调与恢复链路")).toBeInTheDocument();
    const main = screen.getByTestId("platform-home");
    const sections = Array.from(main.querySelectorAll("section[data-testid]")) as HTMLElement[];
    expect(sections[0]?.dataset?.testid).toBe("goal-composer-section");
    expect(sections[1]?.dataset?.testid).toBe("current-execution-section");
    expect(sections[2]?.dataset?.testid).toBe("recent-goals-section");
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

  it("shows authoritative current-execution state from the selected goal detail", async () => {
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
    const newGoal = makeGoalData("RUNNING", DEFAULT_LINKS);
    newGoal.id = "goal-new";
    newGoal.title = "完成一个可以恢复的多 Agent 任务";
    newGoal.objective = "完成一个可以恢复的多 Agent 任务";
    vi.spyOn(platformClient, "startGoal").mockResolvedValue(newGoal);
    vi.spyOn(platformClient, "fetchGoal").mockImplementation((goalId) =>
      Promise.resolve(goalId === "goal-new" ? newGoal : makeGoalData("RUNNING", DEFAULT_LINKS))
    );
    vi.spyOn(platformClient, "fetchGoals").mockResolvedValue([newGoal, makeGoalData("RUNNING", DEFAULT_LINKS)] as PlatformGoal[]);
    const submit = screen.getByLabelText("规划并运行");
    await user.type(screen.getByLabelText("描述最终目标"), "完成一个可以恢复的多 Agent 任务");
    expect(submit).toBeDisabled();
    await user.click(screen.getByText("启用 2 小时自治窗口"));
    expect(submit).toBeEnabled();
    await user.click(submit);
    await waitFor(() => expect(screen.getAllByText("完成一个可以恢复的多 Agent 任务").length).toBeGreaterThan(0));
  });

  it("advances RUNNING to completed/review state without a manual reload", async () => {
    await homeReady();
    expect(screen.getByText("Agent 正在执行")).toBeInTheDocument();
    const client = makeClient();
    render(<HomePage />, { factory: () => client });
    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });
    await act(async () => {
      vi.mocked(platformClient.fetchGoal).mockResolvedValue(makeGoalData("COMPLETED", COMPLETED_LINKS));
      await client.refetchQueries({ queryKey: ["goals", DEMO_ID] });
      globalThis.dispatchEvent(new Event("focus"));
    });
    await vi.waitFor(() => {
      expect(screen.getAllByText("结果已验证").length).toBeGreaterThan(0);
      expect(screen.queryByText("Agent 正在执行")).not.toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it("advances RUNNING to BLOCKED state without a manual reload", async () => {
    const client = makeClient();
    render(<HomePage />, { factory: () => client });
    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });
    await act(async () => {
      vi.mocked(platformClient.fetchGoal).mockResolvedValue(makeGoalData("BLOCKED", BLOCKED_LINKS));
      await client.refetchQueries({ queryKey: ["goals", DEMO_ID] });
    });
    await vi.waitFor(() => {
      expect(screen.getByText("需要处理阻塞")).toBeInTheDocument();
      expect(screen.getByText("BLOCKED")).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it("reconciles authoritative state immediately after window focus", async () => {
    const client = makeClient();
    render(<HomePage />, { factory: () => client });
    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });
    await act(async () => {
      vi.mocked(platformClient.fetchGoal).mockResolvedValue(makeGoalData("COMPLETED", COMPLETED_LINKS));
      await client.refetchQueries({ queryKey: ["goals", DEMO_ID] });
      globalThis.dispatchEvent(new Event("focus"));
    });
    await vi.waitFor(() => expect(screen.getAllByText("结果已验证").length).toBeGreaterThan(0), { timeout: 5000 });
  });

  it("reconciles authoritative state immediately after reconnect", async () => {
    const client = makeClient();
    render(<HomePage />, { factory: () => client });
    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });
    await act(async () => {
      vi.mocked(platformClient.fetchGoal).mockResolvedValue(makeGoalData("BLOCKED", CANCELLED_LINKS));
      await client.refetchQueries({ queryKey: ["goals", DEMO_ID] });
      vi.spyOn(globalThis.navigator, "onLine", "get").mockReturnValue(true);
      globalThis.dispatchEvent(new Event("online"));
    });
    await vi.waitFor(() => {
      expect(screen.getByText("需要处理阻塞")).toBeInTheDocument();
      expect(screen.getByText("BLOCKED")).toBeInTheDocument();
    }, { timeout: 5000 });
    vi.restoreAllMocks();
  });

  it("stops active-rate polling once the selected goal reaches a terminal state", async () => {
    const client = makeClient();
    render(<HomePage />, { factory: () => client });
    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });
    await act(async () => {
      vi.mocked(platformClient.fetchGoal).mockResolvedValue(makeGoalData("COMPLETED", COMPLETED_LINKS));
      await client.refetchQueries({ queryKey: ["goals", DEMO_ID] });
    });
    await vi.waitFor(() => {
      expect(screen.getAllByText("结果已验证").length).toBeGreaterThan(0);
      expect(screen.queryByText("Agent 正在执行")).not.toBeInTheDocument();
    }, { timeout: 5000 });
    expect(screen.getAllByText("COMPLETED").length).toBeGreaterThan(0);
  });

  it("uses the selected goal detail query for Current Execution", async () => {
    const client = seededClient("COMPLETED", COMPLETED_LINKS);
    render(<HomePage />, { factory: () => client });
    await waitFor(() => expect(screen.getByText("Agent progress")).toBeInTheDocument(), { timeout: 4000 });
    expect(screen.getByTestId("current-execution-section")).toContainElement(screen.getByText("分析目标与代码库"));
    expect(screen.getByTestId("current-execution-section")).toContainElement(screen.getByText("验证并准备证据"));
    expect(screen.getAllByText("结果已验证").length).toBeGreaterThan(0);
  });

  it("keeps Recent Goals capped at 3 entries even with more goals", async () => {
    await homeReady();
    const recentSection = screen.getByTestId("recent-goals-section");
    const recentButtons = recentSection.querySelectorAll("button[type='button']");
    expect(recentButtons.length).toBeLessThanOrEqual(3);
  });
});
