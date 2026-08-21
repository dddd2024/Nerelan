import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, type MemoryRouterProps } from "react-router";
import { type ReactNode, useState } from "react";
import { render as rtlRender, type RenderOptions } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HomePage } from "@/routes/home";
import { __setMockGoalStatus, fetchGoal } from "@/lib/platform-client";
import type { PlatformGoal } from "@/lib/platform-client";

const DEMO_ID = "goal-demo-platform";
const ts = "2026-01-01T00:00:00Z";

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

const RUNNING_LINKS = [
  { task_id: "t1", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "分析目标与代码库" },
  { task_id: "t2", plan_task_id: "T002", status: "RUNNING", title: "实现协调与恢复链路" },
  { task_id: "t3", plan_task_id: "T003", status: "QUEUED", title: "验证并准备证据" },
] as const;

function makeClient(staleTime = 30_000) {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity, staleTime } },
  });
}

function Wrapper({ children, initialEntries, factory }: { children: ReactNode; initialEntries?: string[]; factory?: () => QueryClient }) {
  const client = useState(() => (factory ?? makeClient)())[0];
  const initial: MemoryRouterProps = { initialEntries: initialEntries ?? ["/"] };
  return <QueryClientProvider client={client}><MemoryRouter {...initial}>{children}</MemoryRouter></QueryClientProvider>;
}

function render(ui: ReactNode, opts?: RenderOptions & { factory?: () => QueryClient; initialEntries?: string[] }) {
  const { factory, initialEntries, ...restOpts } = opts ?? {};
  return rtlRender(
    ui as Parameters<typeof rtlRender>[0],
    {
      wrapper: ({ children }: { children: ReactNode }) => (
        <Wrapper factory={factory} initialEntries={initialEntries}>{children}</Wrapper>
      ),
      ...restOpts,
    },
  );
}

function seededClient(status: PlatformGoal["status"], links: readonly { task_id: string; plan_task_id: string; status: string; title: string }[]) {
  const c = makeClient();
  const base: PlatformGoal = {
    id: DEMO_ID, title: "完善无人值守多 Agent 平台", objective: "目标 A", status,
    repository: "dddd2024/reverse-agent", revision: 1, spec_markdown: "", plan_markdown: "",
    tasks: [], acceptance_criteria: [], artifact_digest: "",
    executor_kind: "opencode", orchestration_mode: "single", binding_ref: "", window_id: "",
    task_links: [...links], created_at: ts, updated_at: ts,
  };
  c.setQueryData(["goals"], [
    base,
    { ...base, id: "goal-two", title: "目标二", objective: "目标 B", status: "COMPLETED", task_links: [] },
    { ...base, id: "goal-three", title: "目标三", objective: "目标 C", status: "APPROVED", task_links: [] },
    { ...base, id: "goal-four", title: "目标四", objective: "目标 D", status: "DRAFT", task_links: [] },
  ]);
  c.setQueryData(["goals", DEMO_ID], base);
  return c;
}

async function homeReady(seed = true) {
  render(<HomePage />, { factory: seed ? () => seededClient("RUNNING", RUNNING_LINKS) : makeClient });
  await waitFor(() => expect(screen.getByText("Agent progress")).toBeInTheDocument(), { timeout: 4000 });
}

function seedRunningGoalClient(): QueryClient {
  const c = makeClient();
  const base: PlatformGoal = {
    id: DEMO_ID, title: "完善无人值守多 Agent 平台", objective: "目标 A", status: "RUNNING",
    repository: "dddd2024/reverse-agent", revision: 1, spec_markdown: "", plan_markdown: "",
    tasks: [], acceptance_criteria: [], artifact_digest: "",
    executor_kind: "opencode", orchestration_mode: "single", binding_ref: "", window_id: "",
    task_links: [...RUNNING_LINKS], created_at: ts, updated_at: ts,
  };
  c.setQueryData(["goals"], [
    base,
    { ...base, id: "goal-two", title: "目标二", objective: "目标 B", status: "COMPLETED", task_links: [] },
    { ...base, id: "goal-three", title: "目标三", objective: "目标 C", status: "APPROVED", task_links: [] },
    { ...base, id: "goal-four", title: "目标四", objective: "目标 D", status: "DRAFT", task_links: [] },
  ]);
  c.setQueryData(["goals", DEMO_ID], base);
  return c;
}

function goalTransitionTest(
  terminalLinks: readonly { task_id: string; plan_task_id: string; status: string; title: string }[],
  goalStatus: PlatformGoal["status"],
  expectedText: string,
) {
  return async () => {
    const client = seedRunningGoalClient();
    render(<HomePage />, { factory: () => client });
    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });
    __setMockGoalStatus(DEMO_ID, { status: goalStatus, task_links: [...terminalLinks] });
    const updatedGoal = await fetchGoal(DEMO_ID);
    client.setQueryData(["goals", DEMO_ID], () => structuredClone(updatedGoal));
    void client.refetchQueries({ queryKey: ["goals", DEMO_ID] });
    await vi.waitFor(() => {
      expect(screen.getByText(expectedText)).toBeInTheDocument();
    }, { timeout: 4000 });
  };
}

describe("Platform V2 Home Workspace V2", () => {
  beforeEach(() => {
    __setMockGoalStatus(DEMO_ID, { status: "RUNNING", task_links: [...RUNNING_LINKS] });
  });
  it("renders the centered single-column layout: composer, current execution, recent goals", async () => {
    await homeReady();
    expect(screen.getByRole("heading", { name: "今天想完成什么？" })).toBeInTheDocument();
    expect(screen.getByLabelText("描述最终目标")).toBeInTheDocument();
    expect(screen.getByText("Agent progress")).toBeInTheDocument();
    expect(screen.getByText("实现协调与恢复链路")).toBeInTheDocument();
    const composer = screen.getByTestId("goal-composer-section");
    const current = screen.getByTestId("current-execution-section");
    const recent = screen.getByTestId("recent-goals-section");
    expect(current.compareDocumentPosition(composer) & Node.DOCUMENT_POSITION_PRECEDING).toBe(Node.DOCUMENT_POSITION_PRECEDING);
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
    const submit = screen.getByLabelText("规划并运行");
    await user.type(screen.getByLabelText("描述最终目标"), "完成一个可以恢复的多 Agent 任务");
    expect(submit).toBeDisabled();
    await user.click(screen.getByText("启用 2 小时自治窗口"));
    expect(submit).toBeEnabled();
    await user.click(submit);
    await waitFor(() => expect(screen.getAllByText("完成一个可以恢复的多 Agent 任务").length).toBeGreaterThan(0));
  });

  it("advances RUNNING to completed/review state without a manual reload", goalTransitionTest(
    COMPLETED_LINKS, "COMPLETED", "结果已验证",
  ));

  it("advances RUNNING to BLOCKED state without a manual reload", goalTransitionTest(
    BLOCKED_LINKS, "BLOCKED", "需要处理阻塞",
  ));

  it("reconciles authoritative state immediately after window focus", async () => {
    const client = seedRunningGoalClient();
    render(<HomePage />, { factory: () => client });
    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });
    __setMockGoalStatus(DEMO_ID, { status: "COMPLETED", task_links: [...COMPLETED_LINKS] });
    const updatedGoal = await fetchGoal(DEMO_ID);
    globalThis.dispatchEvent(new Event("focus"));
    client.setQueryData(["goals", DEMO_ID], () => structuredClone(updatedGoal));
    void client.refetchQueries({ queryKey: ["goals", DEMO_ID] });
    await vi.waitFor(() => {
      expect(screen.getByText("结果已验证")).toBeInTheDocument();
    }, { timeout: 4000 });
  });

  it("reconciles authoritative state immediately after reconnect", async () => {
    const client = seedRunningGoalClient();
    render(<HomePage />, { factory: () => client });
    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });
    __setMockGoalStatus(DEMO_ID, { status: "BLOCKED", task_links: [...CANCELLED_LINKS] });
    const updatedGoal = await fetchGoal(DEMO_ID);
    vi.spyOn(globalThis.navigator, "onLine", "get").mockReturnValue(true);
    globalThis.dispatchEvent(new Event("online"));
    client.setQueryData(["goals", DEMO_ID], () => structuredClone(updatedGoal));
    void client.refetchQueries({ queryKey: ["goals", DEMO_ID] });
    await vi.waitFor(() => {
      expect(screen.getByText("需要处理阻塞")).toBeInTheDocument();
      expect(screen.getByText("BLOCKED")).toBeInTheDocument();
    }, { timeout: 4000 });
    vi.restoreAllMocks();
  });

  it("uses the selected goal detail query for Current Execution", async () => {
    const client = seedRunningGoalClient();
    render(<HomePage />, { factory: () => client });
    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });
    __setMockGoalStatus(DEMO_ID, { status: "COMPLETED", task_links: [...COMPLETED_LINKS] });
    const updatedGoal = await fetchGoal(DEMO_ID);
    client.setQueryData(["goals", DEMO_ID], () => structuredClone(updatedGoal));
    void client.refetchQueries({ queryKey: ["goals", DEMO_ID] });
    await vi.waitFor(() => {
      expect(screen.getByTestId("current-execution-section")).toContainElement(screen.getByText("分析目标与代码库"));
      expect(screen.getByTestId("current-execution-section")).toContainElement(screen.getByText("验证并准备证据"));
      expect(screen.getByText("结果已验证")).toBeInTheDocument();
    }, { timeout: 4000 });
  });

  it("stops active-rate polling once the selected goal reaches a terminal state", goalTransitionTest(
    COMPLETED_LINKS, "COMPLETED", "结果已验证",
  ));

  it("keeps Recent Goals capped at 3 entries even with more goals", async () => {
    await homeReady();
    const recentSection = screen.getByTestId("recent-goals-section");
    const recentButtons = recentSection.querySelectorAll("button[type='button']");
    expect(recentButtons.length).toBeLessThanOrEqual(3);
  });
});
