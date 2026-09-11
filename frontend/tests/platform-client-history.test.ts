import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchGoals, fetchGoalsPage, fetchRuns, fetchRunsPage, startGoal } from "@/lib/platform-client";

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.useRealTimers(); });

describe("history page client contracts", () => {
  it("preserves metadata and encodes opaque positions while legacy array reads remain compatible", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const positions: string[] = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input));
      positions.push(url.searchParams.get("cursor") ?? "");
      return new Response(JSON.stringify({ goals: [{ id: "old-goal" }], runs: [{ task_id: "old-run" }], total: 151, next_cursor: "next +/?=&" }), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const goalPage = await fetchGoalsPage({ cursor: "previous +/?=&", limit: 37 });
    expect(goalPage).toEqual({ items: [{ id: "old-goal" }], total: 151, next_cursor: "next +/?=&" });
    expect(new URL(String(fetchMock.mock.calls[0][0])).searchParams.get("limit")).toBe("37");
    expect((await fetchRunsPage({ cursor: "run-position" })).total).toBe(151);
    expect(await fetchGoals()).toEqual([{ id: "old-goal" }]);
    expect(await fetchRuns()).toEqual([{ task_id: "old-run" }]);
    expect(positions).toEqual(["previous +/?=&", "run-position", "", ""]);
  });

  it("does not fabricate a total when an older response omits metadata", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ runs: [{ task_id: "run" }] }))));
    expect(await fetchRunsPage()).toEqual({ items: [{ task_id: "run" }], total: null, next_cursor: null });
  });

  it("propagates an HTTP failure rather than reporting an empty page", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ error: "unavailable" }), { status: 500 })));
    await expect(fetchGoalsPage()).rejects.toThrow();
    await expect(fetchRunsPage()).rejects.toThrow();
  });

  it("keeps mock history bounded and stable for 151 new Goals and their Runs", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2030-01-01T00:00:00Z"));
    let identity = Date.now();
    vi.spyOn(Date, "now").mockImplementation(() => ++identity);
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Unexpected HTTP")));
    const create = (index: number) => startGoal({ objective: `History ${index}`, repository: "owner/repo", executorKind: "deterministic_fixture", bindingRef: "", autonomyHours: 1 });
    for (let index = 0; index < 151; index++) await create(index);
    const originalGoals = new Set((await fetchGoals()).map((goal) => goal.id));
    const originalRuns = new Set((await fetchRuns()).map((run) => run.task_id));
    let goalPage = await fetchGoalsPage({ limit: 37 });
    let runPage = await fetchRunsPage({ limit: 37 });
    const goalIds = goalPage.items.map((goal) => goal.id);
    const runIds = runPage.items.map((run) => run.task_id);
    vi.setSystemTime(new Date("2031-01-01T00:00:00Z"));
    await create(152);
    while (goalPage.next_cursor) {
      goalPage = await fetchGoalsPage({ limit: 37, cursor: goalPage.next_cursor });
      expect(goalPage.items.length).toBeLessThanOrEqual(37);
      goalIds.push(...goalPage.items.map((goal) => goal.id));
    }
    while (runPage.next_cursor) {
      runPage = await fetchRunsPage({ limit: 37, cursor: runPage.next_cursor });
      expect(runPage.items.length).toBeLessThanOrEqual(37);
      runIds.push(...runPage.items.map((run) => run.task_id));
    }
    expect(new Set(goalIds)).toEqual(originalGoals);
    expect(goalIds).toHaveLength(originalGoals.size);
    expect(new Set(runIds)).toEqual(originalRuns);
    expect(runIds).toHaveLength(originalRuns.size);
    expect(fetch).not.toHaveBeenCalled();
  });
});
