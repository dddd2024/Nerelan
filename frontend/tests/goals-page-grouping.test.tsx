import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as client from "@/lib/platform-client";
import type { PlatformGoal } from "@/lib/platform-client";
import { GoalsPage, groupGoals } from "@/routes/goals";

function goal(id: string, title: string, status: string, updated: string, extra: Partial<PlatformGoal> = {}): PlatformGoal {
  return { id, title, objective: "", status, repository: "org/alpha", updated_at: updated, tasks: [], task_links: [], ...extra } as unknown as PlatformGoal;
}

const goals = [
  goal("g-plan", "写一份设计", "PLANNED", "2026-08-05T08:00:00Z"),
  goal("g-run", "#1488 [Runtime] Detect stalls", "RUNNING", "2026-08-04T08:00:00Z", {
    task_links: [{ task_id: "t1", plan_task_id: "T001", status: "RUNNING", title: "x" }] as never }),
  goal("g-stop", "#1490 [Owner] Fix upload", "BLOCKED", "2026-08-03T08:00:00Z", {
    task_links: [{ task_id: "t2", plan_task_id: "T001", status: "FAILED", title: "x" }] as never }),
  // Same issue as g-stop, older: folded under it instead of getting its own row.
  goal("g-stop-old", "#1490 [Owner] Fix upload", "BLOCKED", "2026-08-01T08:00:00Z", {
    task_links: [{ task_id: "t3", plan_task_id: "T001", status: "FAILED", title: "x" }] as never }),
  goal("g-cancel", "#1491 Old idea", "BLOCKED", "2026-07-30T08:00:00Z", {
    task_links: [{ task_id: "t4", plan_task_id: "T001", status: "CANCELLED", title: "x" }] as never }),
];

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

function mount(items: PlatformGoal[], next: string | null = null) {
  vi.spyOn(client, "fetchGoalsPage").mockResolvedValue({ items, total: items.length, next_cursor: next });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } });
  return render(<QueryClientProvider client={queryClient}><MemoryRouter><GoalsPage /></MemoryRouter></QueryClientProvider>);
}

describe("goals page grouping", () => {
  it("groups by what needs the Owner and keeps one row per issue", () => {
    const groups = groupGoals(goals);
    expect(groups.needs_you.map((row) => row.goal.id)).toEqual(["g-plan"]);
    expect(groups.active.map((row) => row.goal.id)).toEqual(["g-run"]);
    expect(groups.stopped.map((row) => row.goal.id)).toEqual(["g-stop"]);
    expect(groups.stopped[0].older.map((item) => item.id)).toEqual(["g-stop-old"]);
    expect(groups.ended.map((row) => row.goal.id)).toEqual(["g-cancel"]);
  });

  it("renders the four sections with clean titles, folded older goals and no pagination for one page", async () => {
    mount(goals);
    expect(screen.getByRole("heading", { name: "目标" })).toBeInTheDocument();
    await screen.findByRole("region", { name: "需要你处理" });
    for (const name of ["需要你处理", "进行中", "已停下", "已结束"]) {
      expect(screen.getByRole("region", { name })).toBeInTheDocument();
    }
    const stopped = within(screen.getByRole("region", { name: "已停下" }));
    expect(stopped.getByText("Fix upload")).toBeInTheDocument();
    expect(stopped.getByText("#1490")).toBeInTheDocument();
    expect(stopped.getByText("之前还有 1 个同一 Issue 的旧目标")).toBeInTheDocument();
    expect(screen.getAllByText("Fix upload")).toHaveLength(1);
    expect(screen.getByTestId("goal-row-g-cancel")).toHaveTextContent("已取消");
    // A goal that has not started continues on the approvals page.
    expect(screen.getByTestId("goal-row-g-plan").querySelector("a")).toHaveAttribute("href", "/approvals?goal=g-plan");
    expect(screen.getByTestId("goal-row-g-run").querySelector("a")).toHaveAttribute("href", "/?goal=g-run");
    expect(screen.queryByRole("button", { name: "下一页" })).not.toBeInTheDocument();
  });

  it("shows pagination when the server has another page", async () => {
    mount(goals, "older");
    expect(await screen.findByRole("button", { name: "下一页" })).toBeEnabled();
  });
});
