import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import type { ReactElement } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as client from "@/lib/platform-client";
import type { PlatformGoal, PlatformInboxItem, PlatformRoadmapPhase, PlatformStatus } from "@/lib/platform-client";
import { HomePage } from "@/routes/home";
import { InboxPage } from "@/routes/inbox";
import { RoadmapPage } from "@/routes/roadmap";

const timestamp = "2026-09-11T00:00:00Z";
const goal: PlatformGoal = {
  id: "saved-goal", title: "Saved goal", objective: "Keep this Goal identity",
  repository: "dddd2024/Nerelan", status: "RUNNING", revision: 1,
  spec_markdown: "", plan_markdown: "", tasks: [], acceptance_criteria: [],
  artifact_digest: "", executor_kind: "deterministic_fixture", orchestration_mode: "single",
  binding_ref: "", window_id: "", created_at: timestamp, updated_at: timestamp,
};
const inbox: PlatformInboxItem[] = [{
  id: "saved-idea", title: "Saved idea", objective: "Keep cached idea", repository: goal.repository,
  status: "CAPTURED", promoted_goal_id: "", created_at: timestamp, updated_at: timestamp,
}];
const roadmap: PlatformRoadmapPhase[] = [{
  id: "saved-phase", title: "Saved phase", position: 0, description: "", derived_status: "PLANNED", goals: [],
  created_at: timestamp, updated_at: timestamp,
}];
const clients: QueryClient[] = [];
let platform: PlatformStatus;

function mount(page: ReactElement, seeds: Array<[unknown[], unknown]> = []) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } });
  clients.push(queryClient);
  for (const [key, data] of seeds) queryClient.setQueryData(key, data, { updatedAt: 1 });
  render(<QueryClientProvider client={queryClient}><MemoryRouter>{page}</MemoryRouter></QueryClientProvider>);
  return queryClient;
}

beforeEach(async () => {
  platform = await client.fetchPlatformStatus();
  vi.spyOn(client, "fetchPlatformStatus").mockResolvedValue(platform);
  vi.spyOn(client, "fetchGoals").mockResolvedValue([goal]);
  vi.spyOn(client, "fetchGoal").mockResolvedValue(goal);
  vi.spyOn(client, "fetchRuns").mockResolvedValue([]);
});
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((queryClient) => queryClient.clear());
  vi.restoreAllMocks();
});

const cases = [
  { name: "Inbox", page: <InboxPage />, key: ["inbox"], data: inbox, saved: "Saved idea", label: "想法", empty: "没有待处理的想法。", spy: () => vi.spyOn(client, "fetchInbox") },
  { name: "Roadmap", page: <RoadmapPage />, key: ["roadmap"], data: roadmap, saved: "Saved phase", label: "路线图", empty: "还没有路线图阶段。", spy: () => vi.spyOn(client, "fetchRoadmap") },
  { name: "Home goals", page: <HomePage />, key: ["goals"], data: [goal], saved: "Saved goal", label: "目标列表", empty: "还没有目标。", spy: () => vi.spyOn(client, "fetchGoals") },
];

describe.each(cases)("$name query feedback", (scenario) => {
  it("does not show empty data while the first read is pending", () => {
    scenario.spy().mockReset().mockImplementation(() => new Promise<never>(() => {}));
    mount(scenario.page);
    expect(screen.getByText(`正在加载${scenario.label}…`)).toBeInTheDocument();
    expect(screen.queryByText(scenario.empty)).not.toBeInTheDocument();
    expect(screen.queryByText("第一个目标会在这里显示 Agent 的执行进度。")).not.toBeInTheDocument();
  });

  it("distinguishes a failed initial read and recovers through explicit retry", async () => {
    const spy = scenario.spy().mockReset().mockRejectedValueOnce(new Error("Read unavailable")).mockResolvedValueOnce([]);
    const user = userEvent.setup();
    mount(scenario.page);
    expect(await screen.findByText(`${scenario.label}加载失败`)).toBeInTheDocument();
    expect(screen.queryByText(scenario.empty)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "重试" }));
    expect(await screen.findByText(scenario.empty)).toBeInTheDocument();
    expect(spy).toHaveBeenCalledTimes(2);
    expect(screen.queryByText(`${scenario.label}加载失败`)).not.toBeInTheDocument();
  });

  it("shows a truthful successful empty state", async () => {
    scenario.spy().mockReset().mockResolvedValue([]);
    mount(scenario.page);
    expect(await screen.findByText(scenario.empty)).toBeInTheDocument();
    expect(screen.queryByText(`${scenario.label}加载失败`)).not.toBeInTheDocument();
  });

  it("preserves cached data during a background failure, then clears stale feedback after retry", async () => {
    const spy = scenario.spy().mockReset().mockRejectedValueOnce(new Error("Background unavailable")).mockResolvedValueOnce([]);
    const user = userEvent.setup();
    mount(scenario.page, [[scenario.key, scenario.data]]);
    expect(await screen.findByText(`${scenario.label}更新失败，显示上次内容`)).toBeInTheDocument();
    expect(screen.getAllByText(scenario.saved).length).toBeGreaterThan(0);
    await user.click(screen.getByRole("button", { name: "重试" }));
    await waitFor(() => expect(screen.queryByText(`${scenario.label}更新失败，显示上次内容`)).not.toBeInTheDocument());
    expect(spy).toHaveBeenCalledTimes(2);
  });
});

describe("Home independent reads", () => {
  it("does not claim cached coordinator status is fresh after a status read fails", async () => {
    vi.mocked(client.fetchPlatformStatus).mockRejectedValue(new Error("Status unavailable"));
    mount(<HomePage />, [[["platform", "status"], platform]]);
    expect(await screen.findByText("平台状态更新失败，显示上次内容")).toBeInTheDocument();
    expect(screen.getByText("平台状态待刷新")).toBeInTheDocument();
    expect(screen.queryByText("协调器在线")).not.toBeInTheDocument();
  });

  it("reports unavailable run activity without removing the selected Goal", async () => {
    vi.mocked(client.fetchRuns).mockRejectedValue(new Error("Runs unavailable"));
    mount(<HomePage />);
    expect(await screen.findByText("运行活动加载失败")).toBeInTheDocument();
    expect(screen.getByTestId("active-goal-stream")).toBeInTheDocument();
    expect(screen.getByTestId("active-goal-header")).toHaveTextContent(goal.title);
  });

  it("retains the same cached Goal detail and exposes a retry after background failure", async () => {
    vi.mocked(client.fetchGoal).mockRejectedValue(new Error("Goal detail unavailable"));
    mount(<HomePage />, [[["goals", goal.id], goal]]);
    expect(await screen.findByText("目标详情更新失败，显示上次内容")).toBeInTheDocument();
    expect(screen.getByTestId("active-goal-stream")).toBeInTheDocument();
    expect(screen.getByTestId("active-goal-header")).toHaveTextContent(goal.title);
    expect(within(screen.getByTestId("current-execution-section")).getByRole("button", { name: "重试" })).toBeInTheDocument();
  });
});
