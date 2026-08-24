import {
  focusManager,
  onlineManager,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { MemoryRouter, type MemoryRouterProps } from "react-router";
import { type ReactNode, useState } from "react";
import { act, render as rtlRender, type RenderOptions } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, type Mock, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import * as platformClient from "@/lib/platform-client";
import { __setMockGoalStatus } from "@/lib/platform-client";
import { HomePage } from "@/routes/home";
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

const RUNNING_GOAL: PlatformGoal = {
  id: DEMO_ID,
  title: "完善无人值守多 Agent 平台",
  objective: "目标 A",
  status: "RUNNING",
  repository: "dddd2024/reverse-agent",
  revision: 1,
  spec_markdown: "",
  plan_markdown: "",
  tasks: [],
  acceptance_criteria: [],
  artifact_digest: "",
  executor_kind: "opencode",
  orchestration_mode: "single",
  binding_ref: "",
  window_id: "",
  task_links: [...RUNNING_LINKS],
  created_at: ts,
  updated_at: ts,
};

const SIBLING_GOALS = [
  { id: "goal-two", title: "目标二", objective: "目标 B", status: "COMPLETED" as const, task_links: [] },
  { id: "goal-three", title: "目标三", objective: "目标 C", status: "APPROVED" as const, task_links: [] },
  { id: "goal-four", title: "目标四", objective: "目标 D", status: "DRAFT" as const, task_links: [] },
];

function makeGoal(status: PlatformGoal["status"], links: PlatformGoal["task_links"]) {
  return {
    ...RUNNING_GOAL,
    status,
    task_links: links,
  };
}

function makeClient(options: { staleTime?: number } = {}) {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: Infinity,
        staleTime: options.staleTime ?? 0,
      },
    },
  });
}

function Wrapper({
  children,
  initialEntries,
  factory,
}: { children: ReactNode; initialEntries?: string[]; factory: () => QueryClient }) {
  const client = useState(factory)[0];
  const initial: MemoryRouterProps = { initialEntries: initialEntries ?? ["/"] };
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter {...initial}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

function render(
  ui: ReactNode,
  opts: RenderOptions & { factory: () => QueryClient; initialEntries?: string[] },
) {
  const { factory, initialEntries, ...restOpts } = opts;
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

function seededHomeClient(): QueryClient {
  const c = makeClient({ staleTime: 60_000 });
  c.setQueryData(["goals"], [
    RUNNING_GOAL,
    ...SIBLING_GOALS.map((sibling) => ({ ...RUNNING_GOAL, ...sibling })),
  ]);
  c.setQueryData(["goals", DEMO_ID], RUNNING_GOAL);
  return c;
}

function seedPollingClientFull(): {
  client: QueryClient;
  goalSpy: Mock;
} {
  const goalSpy = vi.spyOn(platformClient, "fetchGoal" as never) as unknown as Mock;
  const c = makeClient({ staleTime: 0 });
  c.setQueryData(["goals"], [
    RUNNING_GOAL,
    ...SIBLING_GOALS.map((sibling) => ({ ...RUNNING_GOAL, ...sibling })),
  ]);
  c.setQueryData(["goals", DEMO_ID], { ...RUNNING_GOAL });
  return { client: c, goalSpy };
}

async function homeReady() {
  render(<HomePage />, { factory: () => seededHomeClient() });
  await waitFor(() => expect(screen.getByText("Agent progress")).toBeInTheDocument(), { timeout: 4000 });
}

function getGoalDetailCacheData(client: QueryClient): PlatformGoal | undefined {
  return client.getQueryData(["goals", DEMO_ID]) as PlatformGoal | undefined;
}

function hasTextInCurrentSection(text: string) {
  const section = screen.getByTestId("current-execution-section");
  const all = screen.getAllByText(text);
  return all.some((el) => section.contains(el));
}

describe("Platform V2 Home Workspace V2", () => {
  beforeEach(() => {
    __setMockGoalStatus(DEMO_ID, { status: "RUNNING", task_links: [...RUNNING_LINKS] });
    vi.spyOn(globalThis.navigator, "onLine", "get").mockReturnValue(true);
  });

  afterEach(() => {
    vi.useRealTimers();
    focusManager.setFocused(undefined);
    onlineManager.setOnline(true);
    vi.restoreAllMocks();
  });

  it("renders the centered single-column layout: composer, current execution, recent goals", async () => {
    await homeReady();
    expect(screen.getByRole("heading", { name: "今天想完成什么？" })).toBeInTheDocument();
    expect(screen.getByLabelText("描述最终目标")).toBeInTheDocument();
    expect(screen.getByText("Agent progress")).toBeInTheDocument();
    expect(screen.getByText("实现协调与恢复链路")).toBeInTheDocument();
    expect(screen.getByTestId("goal-progress-bar")).toBeInTheDocument();
    const composer = screen.getByTestId("goal-composer-section");
    const current = screen.getByTestId("current-execution-section");
    const recent = screen.getByTestId("recent-goals-section");
    expect(current.compareDocumentPosition(composer) & Node.DOCUMENT_POSITION_PRECEDING).toBe(Node.DOCUMENT_POSITION_PRECEDING);
    expect(current.compareDocumentPosition(recent) & Node.DOCUMENT_POSITION_FOLLOWING).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
  });

  it("removes the permanent right rail, activity-stream placeholder, and keeps recent goals capped at 3", async () => {
    await homeReady();
    const main = screen.getByTestId("platform-home");
    expect(main.querySelector("[class*='grid-cols']")).toBeNull();
    expect(main.querySelector("aside")).toBeNull();
    expect(main.querySelector('[data-testid="activity-stream-slot"]')).toBeNull();
    expect(screen.queryByText("Multi-agent workspace")).not.toBeInTheDocument();
    expect(screen.queryByText(/能力$/)).not.toBeInTheDocument();
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

  it("labels a completed current goal with its semantic status", async () => {
    const completed = makeGoal("COMPLETED", [...COMPLETED_LINKS]);
    const client = makeClient({ staleTime: 60_000 });
    client.setQueryData(["goals"], [completed]);
    client.setQueryData(["goals", DEMO_ID], completed);

    render(<HomePage />, { factory: () => client });

    await waitFor(() => expect(screen.getByTestId("goal-state-label")).toBeInTheDocument());
    expect(screen.getByTestId("goal-state-label")).toHaveTextContent("已完成");
    expect(screen.getByTestId("goal-state-label")).toHaveClass("text-ra-status-running");
    expect(screen.getByTestId("goal-progress-bar").firstElementChild).toHaveClass("bg-ra-status-running");
  });

  it("labels a blocked current goal with its semantic status", async () => {
    const blocked = makeGoal("BLOCKED", [...BLOCKED_LINKS]);
    const client = makeClient({ staleTime: 60_000 });
    client.setQueryData(["goals"], [blocked]);
    client.setQueryData(["goals", DEMO_ID], blocked);

    render(<HomePage />, { factory: () => client });

    await waitFor(() => expect(screen.getByTestId("goal-state-label")).toBeInTheDocument());
    expect(screen.getByTestId("goal-state-label")).toHaveTextContent("需要处理阻塞");
    expect(screen.getByTestId("goal-state-label")).toHaveClass("text-ra-status-error");
    expect(screen.getByTestId("goal-progress-bar").firstElementChild).toHaveClass("bg-ra-status-error");
  });

  it("distinguishes selected-detail loading from the empty state", async () => {
    const detailRequest = new Promise<PlatformGoal>(() => undefined);
    const goalSpy = vi.spyOn(platformClient, "fetchGoal" as never) as unknown as Mock;
    goalSpy.mockReturnValue(detailRequest);
    const client = makeClient({ staleTime: 60_000 });
    client.setQueryData(["goals"], [RUNNING_GOAL]);

    render(<HomePage />, { factory: () => client });

    expect(await screen.findByText("正在加载所选目标的执行进度…")).toHaveAttribute("role", "status");
    expect(screen.queryByText("第一个目标会在这里显示 Agent 的执行进度。")).not.toBeInTheDocument();
  });

  it("shows an accessible selected-detail error and recovers through query retry", async () => {
    const goalSpy = vi.spyOn(platformClient, "fetchGoal" as never) as unknown as Mock;
    goalSpy.mockRejectedValueOnce(new Error("raw provider payload must stay hidden"));
    goalSpy.mockResolvedValueOnce(RUNNING_GOAL);
    const client = makeClient({ staleTime: 60_000 });
    client.setQueryData(["goals"], [RUNNING_GOAL]);

    render(<HomePage />, { factory: () => client });

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("当前所选目标的执行进度暂时无法加载，请重试。");
    expect(alert).not.toHaveTextContent("raw provider payload must stay hidden");
    const retry = screen.getByRole("button", { name: "重试加载当前目标" });
    await userEvent.setup().click(retry);

    await waitFor(() => expect(screen.getByText("Agent progress")).toBeInTheDocument());
    expect(goalSpy).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
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

  it("advances RUNNING to completed/review state via React Query polling without manual cache writes", async () => {
    vi.useFakeTimers();
    const { client, goalSpy } = seedPollingClientFull();

    render(<HomePage />, { factory: () => client });

    expect(screen.getByText("Agent 正在执行")).toBeInTheDocument();
    goalSpy.mockClear();

    __setMockGoalStatus(DEMO_ID, { status: "COMPLETED", task_links: [...COMPLETED_LINKS] });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_600);
    });

    expect(getGoalDetailCacheData(client)?.status).toBe("COMPLETED");
    expect(hasTextInCurrentSection("结果已验证")).toBe(true);
    expect(goalSpy).toHaveBeenCalledTimes(1);
  });

  it("advances RUNNING to BLOCKED state via React Query polling without manual cache writes", async () => {
    vi.useFakeTimers();
    const { client, goalSpy } = seedPollingClientFull();

    render(<HomePage />, { factory: () => client });

    expect(screen.getByText("Agent 正在执行")).toBeInTheDocument();
    goalSpy.mockClear();

    __setMockGoalStatus(DEMO_ID, { status: "BLOCKED", task_links: [...BLOCKED_LINKS] });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_600);
    });

    expect(getGoalDetailCacheData(client)?.status).toBe("BLOCKED");
    expect(hasTextInCurrentSection("需要处理阻塞")).toBe(true);
    expect(goalSpy).toHaveBeenCalledTimes(1);
  });

  it("reconciles authoritative state via React Query focus refetch without manual cache writes", async () => {
    const { client, goalSpy } = seedPollingClientFull();

    render(<HomePage />, { factory: () => client });

    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });

    __setMockGoalStatus(DEMO_ID, { status: "COMPLETED", task_links: [...COMPLETED_LINKS] });

    await client.invalidateQueries({ queryKey: ["goals", DEMO_ID], refetchType: "none" });
    goalSpy.mockClear();
    expect(goalSpy).not.toHaveBeenCalled();
    expect(getGoalDetailCacheData(client)?.status).toBe("RUNNING");
    expect(screen.getByText("Agent 正在执行")).toBeInTheDocument();

    await act(async () => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
    });

    await waitFor(() => {
      const detailCache = getGoalDetailCacheData(client);
      expect(detailCache?.status).toBe("COMPLETED");
      expect(hasTextInCurrentSection("结果已验证")).toBe(true);
      expect(goalSpy).toHaveBeenCalledTimes(1);
    }, { timeout: 4000 });
  });

  it("reconciles authoritative state via React Query reconnect refetch without manual cache writes", async () => {
    const { client, goalSpy } = seedPollingClientFull();
    const onlineGetter = vi.spyOn(globalThis.navigator, "onLine", "get");

    render(<HomePage />, { factory: () => client });

    await waitFor(() => expect(screen.getByText("Agent 正在执行")).toBeInTheDocument(), { timeout: 4000 });

    __setMockGoalStatus(DEMO_ID, { status: "BLOCKED", task_links: [...BLOCKED_LINKS] });

    await client.invalidateQueries({ queryKey: ["goals", DEMO_ID], refetchType: "none" });
    goalSpy.mockClear();
    expect(goalSpy).not.toHaveBeenCalled();
    expect(getGoalDetailCacheData(client)?.status).toBe("RUNNING");
    expect(screen.getByText("Agent 正在执行")).toBeInTheDocument();

    await act(async () => {
      onlineGetter.mockReturnValue(false);
      onlineManager.setOnline(false);
      onlineGetter.mockReturnValue(true);
      onlineManager.setOnline(true);
    });

    await waitFor(() => {
      const detailCache = getGoalDetailCacheData(client);
      expect(detailCache?.status).toBe("BLOCKED");
      expect(hasTextInCurrentSection("需要处理阻塞")).toBe(true);
      expect(goalSpy).toHaveBeenCalledTimes(1);
    }, { timeout: 4000 });
  });

  it("uses the selected goal detail query for Current Execution via reconciliation", async () => {
    vi.useFakeTimers();
    const { client, goalSpy } = seedPollingClientFull();

    render(<HomePage />, { factory: () => client });

    expect(screen.getByText("Agent 正在执行")).toBeInTheDocument();
    goalSpy.mockClear();

    __setMockGoalStatus(DEMO_ID, { status: "COMPLETED", task_links: [...COMPLETED_LINKS] });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_600);
    });

    expect(hasTextInCurrentSection("分析目标与代码库")).toBe(true);
    expect(hasTextInCurrentSection("验证并准备证据")).toBe(true);
    expect(hasTextInCurrentSection("结果已验证")).toBe(true);
    expect(goalSpy).toHaveBeenCalledTimes(1);
  });

  it("stops active-rate polling once the selected goal reaches a terminal state", async () => {
    vi.useFakeTimers();
    const { client, goalSpy } = seedPollingClientFull();

    render(<HomePage />, { factory: () => client });

    expect(screen.getByText("Agent 正在执行")).toBeInTheDocument();
    goalSpy.mockClear();

    __setMockGoalStatus(DEMO_ID, { status: "COMPLETED", task_links: [...COMPLETED_LINKS] });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_600);
    });

    expect(getGoalDetailCacheData(client)?.status).toBe("COMPLETED");
    expect(hasTextInCurrentSection("结果已验证")).toBe(true);

    const fetchesDuringTerminal = goalSpy.mock.calls.length;

    __setMockGoalStatus(DEMO_ID, { status: "BLOCKED", task_links: [...CANCELLED_LINKS] });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(7_500);
    });

    expect(goalSpy.mock.calls.length).toBe(fetchesDuringTerminal);
    expect(getGoalDetailCacheData(client)?.status).toBe("COMPLETED");
    expect(screen.queryByText("需要处理阻塞")).not.toBeInTheDocument();
  });

  it("keeps Recent Goals capped at 3 entries even with more goals", async () => {
    await homeReady();
    const recentSection = screen.getByTestId("recent-goals-section");
    const recentButtons = recentSection.querySelectorAll("button[type='button']");
    expect(recentButtons.length).toBeLessThanOrEqual(3);
  });

  it("keeps Recent Goals status badge colors for COMPLETED, RUNNING, and BLOCKED", async () => {
    const c = makeClient({ staleTime: 60_000 });
    c.setQueryData(["goals"], [
      { ...makeGoal("COMPLETED", [...COMPLETED_LINKS]), id: "goal-completed" },
      { ...makeGoal("RUNNING", [...RUNNING_LINKS]), id: "goal-running" },
      { ...makeGoal("BLOCKED", [...BLOCKED_LINKS]), id: "goal-blocked" },
      { ...RUNNING_GOAL, id: "goal-four", title: "目标四", status: "DRAFT", task_links: [] },
    ]);
    c.setQueryData(["goals", "goal-completed"], { ...makeGoal("COMPLETED", [...COMPLETED_LINKS]), id: "goal-completed" });

    render(<HomePage />, { factory: () => c });
    await waitFor(() => expect(screen.getByText("Agent progress")).toBeInTheDocument(), { timeout: 4000 });

    const recentSection = screen.getByTestId("recent-goals-section");
    const badges = recentSection.querySelectorAll("span");
    const classes = Array.from(badges).map((el) => el.className);
    expect(classes.some((cls) => cls.includes("ra-status-running"))).toBe(true);
    expect(classes.some((cls) => cls.includes("ra-accent"))).toBe(true);
    expect(classes.some((cls) => cls.includes("ra-status-error"))).toBe(true);
  });
});
