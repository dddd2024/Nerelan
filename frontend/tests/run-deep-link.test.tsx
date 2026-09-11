import { cleanup, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as client from "@/lib/platform-client";
import type { PlatformAgentRunDetail } from "@/lib/platform-client";
import { RunsPage } from "@/routes/runs";
import { renderWithProviders } from "./test-utils";

const taskId = "task/a ?&";
function run(id = taskId, available = false) {
  return {
    task_id: id, title: `Interrupted ${id}`, repository: "dddd2024/Nerelan",
    status: "INTERRUPTED", state: "INTERRUPTED", executor_kind: "opencode",
    orchestration_mode: "langgraph", created_at: "2026-09-11T00:00:00Z",
    updated_at: "2026-09-11T00:01:00Z", failure_classification: "",
    goal_id: "goal-one", goal_title: "Same Goal", window_id: "window-one",
    events: [], changed_files: [], budget: null, publication: null,
    usage: { status: "USAGE_UNKNOWN" as const, input_units: 0, output_units: 0,
      reasoning_units: 0, cache_read_units: 0, cache_write_units: 0, cost_micro_units: 0,
      total_token_units: 0, observation_count: 0, unknown_observation_count: 0,
      provenance_ids: [], per_role: [] },
    controls: {
      cancel: { action: "CANCEL" as const, scope: "QUEUE_ONLY" as const,
        availability: "UNAVAILABLE" as const, reason_code: "STATUS_NOT_CANCELLABLE" as const },
      resume: { action: "RESUME" as const, scope: "DURABLE_RECOVERY" as const,
        availability: available ? "AVAILABLE" as const : "UNAVAILABLE" as const,
        reason_code: available ? "INTERRUPTED_DURABLE_READY" as const : "NO_DURABLE_RUN" as const },
    },
  } satisfies PlatformAgentRunDetail & { controls: { resume: unknown } };
}
function mount() {
  return renderWithProviders(<RunsPage />, { initialEntries: [`/runs?task=${encodeURIComponent(taskId)}`] });
}
beforeEach(() => {
  vi.spyOn(client, "fetchRunsPage").mockResolvedValue({ items: [], total: 0, next_cursor: null });
  vi.spyOn(client, "fetchRun").mockResolvedValue(run());
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Unexpected mutation")));
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe("Runs task deep link", () => {
  it("loads an older exact task independently of the list and restores it after refresh", async () => {
    const first = mount();
    expect(await screen.findByTestId(`run-overview-${taskId}`)).toBeInTheDocument();
    expect(client.fetchRun).toHaveBeenCalledWith(taskId);
    expect(screen.getByTestId(`run-toggle-${taskId}`)).toHaveAttribute("aria-expanded", "true");
    first.unmount();
    mount();
    expect(await screen.findByTestId(`run-overview-${taskId}`)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("renders a selected list member only once", async () => {
    vi.mocked(client.fetchRunsPage).mockResolvedValue({ items: [run(), run("other")], total: 2, next_cursor: null });
    mount();
    await screen.findByTestId(`run-overview-${taskId}`);
    expect(screen.getAllByTestId(`run-${taskId}`)).toHaveLength(1);
    expect(screen.getByTestId("run-other")).toBeInTheDocument();
  });

  it("keeps a pending selected task distinct from an empty history", () => {
    vi.mocked(client.fetchRun).mockImplementation(() => new Promise<never>(() => {}));
    mount();
    expect(screen.getByText("正在加载选中运行…")).toBeInTheDocument();
    expect(screen.queryByText("还没有 Agent 运行记录。")).not.toBeInTheDocument();
  });

  it("retries an unavailable task without selecting an unrelated record", async () => {
    vi.mocked(client.fetchRun).mockRejectedValueOnce(new Error("Task unavailable")).mockResolvedValue(run());
    vi.mocked(client.fetchRunsPage).mockResolvedValue({ items: [run("other")], total: 1, next_cursor: null });
    const user = userEvent.setup();
    mount();
    expect(await screen.findByText("选中运行加载失败")).toBeInTheDocument();
    const selected = screen.getByRole("region", { name: "选中运行" });
    expect(within(selected).queryByTestId("run-other")).not.toBeInTheDocument();
    await user.click(within(selected).getByRole("button", { name: "重试" }));
    expect(await screen.findByTestId(`run-overview-${taskId}`)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("rejects a detail response for a different task", async () => {
    vi.mocked(client.fetchRun).mockResolvedValue(run("wrong-task"));
    mount();
    expect(await screen.findByText("选中运行加载失败")).toBeInTheDocument();
    expect(screen.queryByTestId("run-wrong-task")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "恢复运行" })).not.toBeInTheDocument();
  });

  it.each([false, true])("preserves server recovery availability=%s without auto-resuming", async (available) => {
    vi.mocked(client.fetchRun).mockResolvedValue(run(taskId, available));
    mount();
    const button = await screen.findByTestId(`run-resume-${taskId}`);
    if (available) expect(button).toBeEnabled();
    else expect(button).toBeDisabled();
    expect(fetch).not.toHaveBeenCalled();
  });
});
