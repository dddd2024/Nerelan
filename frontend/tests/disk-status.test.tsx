import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { TaskInbox } from "@/components/task-inbox";
import { UnattendedStatus } from "@/components/unattended-status";
import { diskFreeLine, diskHoldLine } from "@/lib/disk-status";
import type { DiskState, PlatformStatus } from "@/lib/platform-client";
import type { Task } from "@/types";

const now = Date.parse("2026-11-24T12:00:00Z");
const healthy: DiskState = {
  free_gb: 50, total_gb: 100, low: false, floor_gb: 2, resume_gb: 2.5, hold: false, reason: "",
  held_since: null, waiting_task_count: 0, waiting_task_ids: [],
};
const held: DiskState = {
  ...healthy, free_gb: 1.8, low: true, hold: true, reason: "disk_space_critical",
  held_since: "2026-11-24T11:00:00Z", waiting_task_count: 3, waiting_task_ids: ["a", "b", "c"],
};

function status(disk: DiskState | null | undefined, active = true): PlatformStatus {
  const window = {
    id: "window", policy_id: "policy", status: "ACTIVE", continuous: true,
    starts_at: "2026-11-24T09:00:00Z", expires_at: "", updated_at: "2026-11-24T11:59:00Z",
    repositories: [], capabilities: [], max_tasks: 8, tasks_started: 3, tasks_completed: 2,
  } as unknown as NonNullable<PlatformStatus["autonomy"]["active_window"]>;
  return {
    service: "test",
    autonomy: { autonomy_enabled: active, active_window: active ? window : null, mode: "test",
      last_progress_at: "2026-11-24T10:00:00Z", unfinished_tasks: 3 },
    coordinator: { enabled: true, last_error: "", active_window_id: "", disk },
    task_count: 3, goal_count: 1, capability_count: 1, live_model_calls: false,
  };
}

describe("disk status", () => {
  it("explains the hold, what waits and that it ends by itself", () => {
    render(<UnattendedStatus status={status(held)} now={now} quietWhenRunning />);
    const banner = screen.getByTestId("disk-status");
    expect(banner).toHaveAttribute("role", "alert");
    expect(banner).toHaveTextContent(
      "磁盘空间不足，暂停启动新任务，3 个任务等待中 · 磁盘剩 1.8 GB（共 100 GB），低于下限 2 GB。正在运行的任务继续；空间恢复到 2.5 GB 后自动继续，不消耗重试次数。",
    );
    // The hold is the explanation; a second "no progress" warning would mislead.
    expect(screen.queryByText(/没有进展/)).toBeNull();
  });
  it("keeps the stall warning without a hold", () => {
    render(<UnattendedStatus status={status(healthy)} now={now} quietWhenRunning />);
    expect(screen.getByRole("status")).toHaveTextContent("没有进展");
    expect(screen.getByRole("status")).toHaveTextContent("磁盘剩 50 GB（共 100 GB）");
    expect(screen.queryByTestId("disk-status")).toBeNull();
  });
  it("shows low space quietly, also without a window", () => {
    render(<UnattendedStatus status={status({ ...healthy, free_gb: 4.8, low: true }, false)} now={now} />);
    expect(screen.getByTestId("disk-status")).toHaveTextContent("磁盘空间偏低 · 磁盘剩 4.8 GB（共 100 GB）");
    expect(screen.getByTestId("disk-status")).not.toHaveClass("text-ra-status-warning");
  });
  it("renders nothing for an older host or an unreadable disk", () => {
    expect(diskHoldLine(undefined)).toBe("");
    expect(diskFreeLine(null)).toBe("");
    expect(diskFreeLine({ ...healthy, free_gb: null })).toBe("");
    expect(diskHoldLine({ ...held, free_gb: null })).toContain("剩余空间暂时读不到");
    const { container } = render(<UnattendedStatus status={status(undefined, false)} now={now} />);
    expect(container).toBeEmptyDOMElement();
  });
  it("gives queued tasks the reason in the task list", () => {
    const task = { id: "t", title: "排队任务", state: "WAITING_FOR_OWNER", nextAction: "Waiting for executor dispatch", activity: [], changes: [], evidence: [] } as unknown as Task;
    const inbox = (queueHold?: string) => (
      <MemoryRouter><TaskInbox tasks={[task]} isLoading={false} isError={false} queueHold={queueHold} /></MemoryRouter>
    );
    const view = render(inbox(diskHoldLine(held)));
    expect(screen.getByTestId("section-queued")).toHaveTextContent("磁盘空间不足，暂停启动新任务");
    view.rerender(inbox(""));
    expect(screen.getByTestId("section-queued")).toHaveTextContent("执行窗口开启后会自动派发");
  });
});
