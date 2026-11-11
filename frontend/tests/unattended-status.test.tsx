import { act, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { UnattendedStatus } from "@/components/unattended-status";
import type { PlatformStatus, PlatformWindow } from "@/lib/platform-client";

const now = Date.parse("2026-11-11T12:00:00Z");
const window: PlatformWindow = {
  id: "window", policy_id: "policy", status: "ACTIVE",
  starts_at: "2026-11-11T11:00:00Z", expires_at: "2026-11-11T13:00:00Z",
  updated_at: "2026-11-11T11:59:00Z", repositories: [], capabilities: [],
  max_tasks: 8, tasks_started: 3, tasks_completed: 2,
  max_token_units: 0, max_cost_micro_units: 0, per_task_token_reservation: 0,
  per_task_cost_reservation: 0, provider_quota_state: "NOT_CONFIGURED",
  enforcement_class: "POST_RUN_OBSERVED", observed_token_units: 0,
  observed_cost_micro_units: 0, unknown_observation_count: 0,
};
function status(active: PlatformWindow | null = window, progress: string | null = "2026-11-11T11:58:00Z"): PlatformStatus {
  return {
    service: "test", autonomy: { autonomy_enabled: Boolean(active), active_window: active,
      mode: "test", last_progress_at: progress },
    coordinator: { enabled: true, last_error: "", active_window_id: active?.id ?? "" },
    task_count: 3, goal_count: 1, capability_count: 1, live_model_calls: false,
  };
}

describe("UnattendedStatus", () => {
  it("explains that no window is running", () => {
    render(<UnattendedStatus status={status(null)} now={now} />);
    expect(screen.getByRole("status")).toHaveTextContent("当前没有无人值守任务在运行");
  });
  it("shows active progress and remaining time", () => {
    render(<UnattendedStatus status={status()} now={now} />);
    expect(screen.getByRole("status")).toHaveTextContent("运行中 · 剩余 60 分钟 · 2 个任务完成 · 上次进展：2 分钟前");
    expect(screen.getByRole("status")).not.toHaveClass("text-ra-status-warning");
  });
  it("warns at the 15 minute boundary", () => {
    render(<UnattendedStatus status={status(window, "2026-11-11T11:45:00Z")} now={now} />);
    expect(screen.getByRole("status")).toHaveTextContent("已有 15 分钟没有进展");
    expect(screen.getByRole("status")).toHaveClass("text-ra-status-warning");
  });
  it("updates the warning even when the polled data stays unchanged", () => {
    vi.useFakeTimers();
    vi.setSystemTime(now);
    const view = render(<UnattendedStatus status={status(window, "2026-11-11T11:46:00Z")} />);
    try {
      expect(screen.getByRole("status")).not.toHaveTextContent("没有进展");
      act(() => vi.advanceTimersByTime(60_000));
      expect(screen.getByRole("status")).toHaveTextContent("已有 15 分钟没有进展");
    } finally {
      view.unmount();
      vi.useRealTimers();
    }
  });
  it("uses the window start when no task has reported progress", () => {
    render(<UnattendedStatus status={status(window, null)} now={now} />);
    expect(screen.getByRole("status")).toHaveTextContent("已有 60 分钟没有进展");
  });
  it("does not warn when all tasks have completed", () => {
    render(<UnattendedStatus status={status({ ...window, tasks_completed: 8 }, "2026-11-11T11:00:00Z")} now={now} />);
    expect(screen.getByRole("status")).not.toHaveTextContent("没有进展");
  });
  it.each([["window_expired", "运行时间已到期"], ["new_reason", "new_reason"]])("explains a stopped window (%s) and the next action", (code, label) => {
    const stopped = status(null);
    stopped.autonomy.latest_window = { ...window, status: "EXPIRED", stop_reason: code };
    render(<UnattendedStatus status={stopped} now={now} />);
    expect(screen.getByRole("status")).toHaveTextContent(`无人值守已停止 · ${label}`);
    expect(screen.getByRole("status")).toHaveTextContent("处理后重新启动或继续目标");
  });
  it("does not keep an old stop notice forever", () => {
    const stopped = status(null);
    stopped.autonomy.latest_window = { ...window, status: "STOPPED", updated_at: "2026-11-09T12:00:00Z" };
    render(<UnattendedStatus status={stopped} now={now} />);
    expect(screen.getByRole("status")).toHaveTextContent("当前没有无人值守任务在运行");
  });
  it("shows a stopped coordinator and stranded goals", () => {
    const stopped = status();
    stopped.coordinator.enabled = false;
    stopped.coordinator.stranded_goals = [{ goal_id: "goal" }];
    render(<UnattendedStatus status={stopped} now={now} />);
    expect(screen.getByRole("status")).toHaveTextContent("协调器未在接收任务");
    expect(screen.getByRole("status")).toHaveTextContent("有未完成目标等待你重新启动");
  });
});
