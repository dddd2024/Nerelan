import type { PlatformStatus } from "@/lib/platform-client";
import { cn } from "@/lib/cn";
import { diskHoldLine, diskFreeLine } from "@/lib/disk-status";
import { runtimeMessage } from "@/lib/runtime-labels";
import { useEffect, useState } from "react";

/** Disk first, also when no window runs: a full disk needs the Owner either way. */
export function UnattendedStatus(props: {
  status: PlatformStatus;
  now?: number;
  quietWhenRunning?: boolean;
}) {
  const disk = props.status.coordinator.disk;
  const hold = diskHoldLine(disk);
  const line = hold || (disk?.low ? `磁盘空间偏低 · ${diskFreeLine(disk)}` : "");
  return (
    <>
      {line && (
        <div
          role="status"
          data-testid="disk-status"
          className={cn(
            "shrink-0 border-b px-4 py-3 text-sm sm:px-5",
            hold ? "border-ra-status-warning/30 bg-ra-status-warning/10 text-ra-status-warning" : "border-ra-border text-ra-text-secondary",
          )}
        >
          {line}
        </div>
      )}
      <WindowStatus {...props} />
    </>
  );
}

function WindowStatus({ status, now: fixedNow, quietWhenRunning = false }: {
  status: PlatformStatus;
  now?: number;
  /** Render nothing while the window runs normally (a goal page says it in its header). */
  quietWhenRunning?: boolean;
}) {
  const [clock, setClock] = useState(Date.now);
  useEffect(() => {
    if (fixedNow !== undefined) return;
    // Unchanged poll responses may not rerender; keep elapsed time moving locally.
    const timer = setInterval(() => setClock(Date.now()), 30_000);
    return () => clearInterval(timer);
  }, [fixedNow]);
  const now = fixedNow ?? clock;
  const window = status.autonomy.active_window ?? status.autonomy.latest_window;
  // The backend's active_window already applies expiry and start time; a stale ACTIVE row is not running.
  const active = window != null && window === status.autonomy.active_window;
  const minutesSince = (value: string | undefined | null) => {
    const timestamp = value ? Date.parse(value) : NaN;
    return Number.isFinite(timestamp) ? Math.max(0, Math.floor((now - timestamp) / 60_000)) : null;
  };
  // Keep a stopped window visible for one day so its explanation survives reloads.
  const stoppedAge = minutesSince(window?.updated_at);
  const recent = active || (window && stoppedAge !== null && stoppedAge < 24 * 60);
  const progressAge = minutesSince(status.autonomy.last_progress_at);
  const idleAge = progressAge ?? minutesSince(window?.starts_at);
  // Startup escalation sweep is non-blocking (#1622); show honest recovery instead of a false stop warning.
  const coordinatorRecovering = Boolean(
    active
    && status.coordinator.enabled
    && (status.coordinator.recovering === true || status.coordinator.lifecycle === "RECOVERING"),
  );
  // Only warn while work is still waiting; an unused task budget with an empty queue is not a stall.
  // A disk hold already explains why nothing progresses.
  const stalled = active && !coordinatorRecovering && !status.coordinator.disk?.hold && (status.autonomy.unfinished_tasks ?? 0) > 0 && idleAge !== null && idleAge >= 15;
  const coordinatorStopped = active && !coordinatorRecovering
    && (!status.coordinator.enabled || status.coordinator.accepting_work === false);
  const warning = stalled || coordinatorStopped || Boolean(recent && !active);
  const timeLeft = window ? Math.max(0, Math.ceil((Date.parse(window.expires_at) - now) / 60_000)) : 0;
  const reason = window?.stop_reason || status.coordinator.last_error;
  const left = timeLeft >= 90 ? `${Math.round(timeLeft / 60)} 小时` : `${Number.isFinite(timeLeft) ? timeLeft : 0} 分钟`;
  // Nothing running and nothing recently stopped: no banner at all.
  if (!recent) return null;
  if (quietWhenRunning && !warning && !coordinatorRecovering) return null;
  return (
    <div role="status" className={cn(
      "shrink-0 border-b px-4 py-3 text-sm sm:px-5",
      warning ? "border-ra-status-warning/30 bg-ra-status-warning/10 text-ra-status-warning" : "border-ra-border text-ra-text-secondary",
    )}>
      {active && coordinatorRecovering
        ? "协调器启动恢复中 · 正在检查已有目标后再派发任务"
        : active && !coordinatorStopped
        // tasks_completed counts finished claims, failed ones included: "已结束", never "完成".
        ? window.continuous ? `持续运行中 · 已结束 ${window.tasks_completed} 个任务` : `执行窗口运行中 · 剩 ${left} · 已结束 ${window.tasks_completed} 个任务`
        : `执行窗口已停止 · ${coordinatorStopped ? "协调器未在接收任务" : (reason ? runtimeMessage(reason).label : "") || "本次运行已结束"}。需要继续时在目标页重试，或开一个新窗口。`}
      {/* Progress only matters while the window can still make some. */}
      {active && !coordinatorRecovering && !coordinatorStopped && (stalled ? ` · 已有 ${idleAge} 分钟没有进展，请检查运行记录和账号状态。`
        : progressAge !== null ? ` · 上次进展：${progressAge === 0 ? "刚刚" : `${progressAge} 分钟前`}` : "")}
      {active && !status.coordinator.disk?.low && diskFreeLine(status.coordinator.disk) && ` · ${diskFreeLine(status.coordinator.disk)}`}
    </div>
  );
}
