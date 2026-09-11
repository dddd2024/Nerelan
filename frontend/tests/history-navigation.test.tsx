import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as client from "@/lib/platform-client";
import type { PlatformAgentRunDetail, PlatformGoal } from "@/lib/platform-client";
import { GoalsPage } from "@/routes/goals";
import { HomePage } from "@/routes/home";
import { RunsPage } from "@/routes/runs";

let goals: PlatformGoal[];
let runs: PlatformAgentRunDetail[];
const clients: QueryClient[] = [];

function Location() {
  const location = useLocation();
  return <output data-testid="location">{location.pathname}{location.search}</output>;
}
function mount(path: string, seed?: [unknown[], unknown]) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } });
  clients.push(queryClient);
  if (seed) queryClient.setQueryData(seed[0], seed[1], { updatedAt: 1 });
  return render(<QueryClientProvider client={queryClient}><MemoryRouter initialEntries={[path]}>
    <Location /><Routes><Route path="/" element={<HomePage />} /><Route path="/goals" element={<GoalsPage />} /><Route path="/runs" element={<RunsPage />} /></Routes>
  </MemoryRouter></QueryClientProvider>);
}

beforeEach(async () => {
  const goal = await client.fetchGoal("goal-demo-platform");
  const run = await client.fetchRun("task-demo-1");
  goals = Array.from({ length: 151 }, (_, index) => ({ ...goal, id: `history-goal-${index}`, title: `History Goal ${index}`, tasks: [], task_links: [] }));
  runs = Array.from({ length: 151 }, (_, index) => ({ ...run, task_id: `history-run-${index}`, title: `History Run ${index}` }));
  vi.spyOn(client, "fetchGoals").mockResolvedValue(goals.slice(0, 3));
  vi.spyOn(client, "fetchRuns").mockResolvedValue([]);
  vi.spyOn(client, "fetchGoal").mockImplementation(async (id) => {
    const goal = goals.find((item) => item.id === id);
    if (!goal) throw new Error("Goal unavailable");
    return goal;
  });
  vi.spyOn(client, "fetchGoalsPage").mockImplementation(async ({ cursor } = {}) => ({ items: cursor ? goals.slice(100) : goals.slice(0, 100), total: 151, next_cursor: cursor ? null : "older-goals" }));
  vi.spyOn(client, "fetchRunsPage").mockImplementation(async ({ cursor } = {}) => ({ items: cursor ? runs.slice(100) : runs.slice(0, 100), total: 151, next_cursor: cursor ? null : "older-runs" }));
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Unexpected mutation")));
});
afterEach(() => {
  cleanup(); clients.splice(0).forEach((queryClient) => queryClient.clear());
  vi.restoreAllMocks(); vi.unstubAllGlobals();
});

describe("Goal history journey", () => {
  it("finds an older Goal from Home and preserves exact identity on refresh", async () => {
    const user = userEvent.setup();
    const first = mount("/");
    await screen.findByRole("heading", { name: "History Goal 0" });
    await user.click(screen.getByRole("link", { name: "所有目标" }));
    expect(await screen.findByRole("link", { name: /History Goal 3 / })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /History Goal 150 / })).not.toBeInTheDocument();
    expect(screen.getByText(/共 151 条/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "下一页" }));
    const older = await screen.findByRole("link", { name: /History Goal 150 / });
    expect(client.fetchGoalsPage).toHaveBeenCalledWith({ cursor: "older-goals" });
    expect(screen.getByRole("button", { name: "下一页" })).toBeDisabled();
    await user.click(older);
    expect(await screen.findByRole("heading", { name: "History Goal 150" })).toBeInTheDocument();
    const url = screen.getByTestId("location").textContent!;
    expect(url).toBe("/?goal=history-goal-150");
    first.unmount();
    mount(url);
    expect(await screen.findByRole("heading", { name: "History Goal 150" })).toBeInTheDocument();
    expect(client.fetchGoal).toHaveBeenCalledWith("history-goal-150");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("rejects a mismatched selected Goal response instead of falling back", async () => {
    vi.mocked(client.fetchGoal).mockResolvedValue(goals[0]);
    mount("/?goal=missing-goal");
    expect(await screen.findByText("当前所选目标的执行进度暂时无法加载，请重试。")).toBeInTheDocument();
    expect(screen.queryByTestId("active-goal-stream")).not.toBeInTheDocument();
    expect(screen.getByTestId("location")).toHaveTextContent("/?goal=missing-goal");
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe.each(["goals", "runs"] as const)("%s history feedback and navigation", (kind) => {
  const empty = kind === "goals" ? "这一页没有目标。" : "还没有 Agent 运行记录。";
  const initialError = kind === "goals" ? "目标历史加载失败" : "暂时无法加载 Agent 运行。";
  const staleError = kind === "goals" ? "目标历史更新失败，显示上次内容" : "运行列表更新失败，显示上次内容";
  const saved = kind === "goals" ? "History Goal 0" : "History Run 0";
  const spy = () => kind === "goals" ? vi.mocked(client.fetchGoalsPage) : vi.mocked(client.fetchRunsPage);

  it("moves between bounded pages and returns to latest without mutations", async () => {
    const user = userEvent.setup();
    mount(`/${kind}`);
    await screen.findByText(saved);
    expect(screen.getByRole("button", { name: "上一页" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "下一页" }));
    expect(await screen.findByText(kind === "goals" ? "History Goal 150" : "History Run 150")).toBeInTheDocument();
    expect(screen.queryByText(saved)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "上一页" }));
    expect(await screen.findByText(saved)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "下一页" }));
    await screen.findByText(kind === "goals" ? "History Goal 150" : "History Run 150");
    await user.click(screen.getByRole("button", { name: "返回最新" }));
    expect(await screen.findByText(saved)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("does not show a successful empty result while pending", () => {
    spy().mockImplementation(() => new Promise<never>(() => {}));
    mount(`/${kind}`);
    expect(screen.getByText(kind === "goals" ? "正在加载目标历史…" : "正在加载 Agent 运行…")).toBeInTheDocument();
    expect(screen.queryByText(empty)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "下一页" })).toBeDisabled();
  });

  it("shows successful empty data truthfully", async () => {
    spy().mockResolvedValue({ items: [], total: 0, next_cursor: null });
    mount(`/${kind}`);
    expect(await screen.findByText(empty)).toBeInTheDocument();
    expect(screen.getByText(/共 0 条/)).toBeInTheDocument();
  });

  it("retries a failed initial page without fabricating an empty result", async () => {
    spy().mockRejectedValueOnce(new Error("Unavailable"));
    const user = userEvent.setup();
    mount(`/${kind}`);
    expect(await screen.findByText(initialError)).toBeInTheDocument();
    expect(screen.queryByText(empty)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "重试" }));
    expect(await screen.findByText(saved)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("does not call an empty page an empty history when the server reports records", async () => {
    spy().mockResolvedValue({ items: [], total: 151, next_cursor: null });
    mount(`/${kind}`);
    expect(await screen.findByText(kind === "goals" ? "这一页没有目标。" : "这一页没有 Agent 运行记录。")).toBeInTheDocument();
    expect(screen.getByText(/共 151 条/)).toBeInTheDocument();
    expect(screen.queryByText("还没有 Agent 运行记录。")).not.toBeInTheDocument();
  });

  it("retains cached rows with stale feedback during background failure", async () => {
    spy().mockRejectedValueOnce(new Error("Background unavailable"));
    const data = { items: kind === "goals" ? [goals[0]] : [runs[0]], total: 151, next_cursor: "older" };
    const user = userEvent.setup();
    mount(`/${kind}`, [[kind, "history", undefined], data]);
    expect(await screen.findByText(staleError)).toBeInTheDocument();
    expect(screen.getByText(saved)).toBeInTheDocument();
    await user.click(within(screen.getByRole("alert")).getByRole("button", { name: "重试" }));
    await waitFor(() => expect(screen.queryByText(staleError)).not.toBeInTheDocument());
  });

  it("keeps the requested older page on failure and retries that cursor", async () => {
    const user = userEvent.setup();
    mount(`/${kind}`);
    await screen.findByText(saved);
    spy().mockRejectedValueOnce(new Error("Older page unavailable"));
    await user.click(screen.getByRole("button", { name: "下一页" }));
    expect(await screen.findByText(initialError)).toBeInTheDocument();
    expect(screen.getByText("第 2 页")).toBeInTheDocument();
    expect(screen.queryByText(saved)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "重试" }));
    expect(await screen.findByText(kind === "goals" ? "History Goal 150" : "History Run 150")).toBeInTheDocument();
    expect(spy()).toHaveBeenLastCalledWith({ cursor: `older-${kind}` });
    expect(fetch).not.toHaveBeenCalled();
  });
});
