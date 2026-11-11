import type { PlatformStatus } from "@/lib/platform-client";
import { cn } from "@/lib/cn";
import { useEffect, useState } from "react";

const STOP_REASONS: Record<string, string> = {
  owner_stopped: "你已停止本次运行",
  window_expired: "运行时间已到期",
  usage_budget_reached: "用量预算已耗尽",
  usage_unknown_budget_reached: "无法确认用量，预算保护已触发",
  usage_unknown: "无法确认用量",
  usage_reservation_overrun: "实际用量超出预留预算",
  receipt_persistence_failed: "运行记录保存失败",
};

export function UnattendedStatus({ status, now: fixedNow }: { status: PlatformStatus; now?: number }) {
  const [clock, setClock] = useState(Date.now);
  useEffect(() => {
    if (fixedNow !== undefined) return;
    // Unchanged poll responses may not rerender; keep elapsed time moving locally.
    const timer = setInterval(() => setClock(Date.now()), 30_000);
    return () => clearInterval(timer);
  }, [fixedNow]);
  const now = fixedNow ?? clock;
  const window = status.autonomy.active_window ?? status.autonomy.latest_window;
  const active = window?.status === "ACTIVE";
  const minutesSince = (value: string | undefined | null) => {
    const timestamp = value ? Date.parse(value) : NaN;
    return Number.isFinite(timestamp) ? Math.max(0, Math.floor((now - timestamp) / 60_000)) : null;
  };
  // Keep a stopped window visible for one day so its explanation survives reloads.
  const stoppedAge = minutesSince(window?.updated_at);
  const recent = active || (window && stoppedAge !== null && stoppedAge < 24 * 60);
  const progressAge = minutesSince(status.autonomy.last_progress_at);
  const idleAge = progressAge ?? minutesSince(window?.starts_at);
  const stalled = active && window.tasks_completed < window.max_tasks && idleAge !== null && idleAge >= 15;
  const coordinatorStopped = active && (!status.coordinator.enabled || status.coordinator.accepting_work === false);
  const warning = stalled || coordinatorStopped || Boolean(recent && !active);
  const timeLeft = window ? Math.max(0, Math.ceil((Date.parse(window.expires_at) - now) / 60_000)) : 0;
  const reason = window?.stop_reason || status.coordinator.last_error;
  return (
    <div role="status" className={cn(
      "shrink-0 border-b px-4 py-3 text-sm sm:px-5",
      warning ? "border-ra-status-warning/30 bg-ra-status-warning/10 text-ra-status-warning" : "border-ra-border text-ra-text-secondary",
    )}>
      {!recent ? "当前没有无人值守任务在运行。" : <>
        {active && !coordinatorStopped
          ? `无人值守运行中 · 剩余 ${Number.isFinite(timeLeft) ? timeLeft : 0} 分钟 · ${window.tasks_completed} 个任务完成`
          : `无人值守已停止 · ${coordinatorStopped ? "协调器未在接收任务" : (STOP_REASONS[reason || ""] ?? reason) || "本次运行已结束"}。请检查运行记录，处理后重新启动或继续目标。`}
        {stalled ? ` · 已有 ${idleAge} 分钟没有进展，请检查运行记录和账号状态。`
          : progressAge !== null ? ` · 上次进展：${progressAge === 0 ? "刚刚" : `${progressAge} 分钟前`}`
            : " · 尚无任务进展记录"}
      </>}
      {Boolean(status.coordinator.stranded_goals?.length) && " · 有未完成目标等待你重新启动。"}
    </div>
  );
}
