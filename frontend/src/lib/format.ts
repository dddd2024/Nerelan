import type { RiskTier, RunState } from "@/types";

// ---------------------------------------------------------------------------
// Time formatting
// ---------------------------------------------------------------------------

/** Format an ISO timestamp as a short relative time (e.g. "3分钟前"). */
export function formatRelativeTime(iso: string, now: Date = new Date()): string {
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return iso;
  const diffMs = now.getTime() - then;
  const sec = Math.round(diffMs / 1000);
  if (sec < 60) return "刚刚";
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}分钟前`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}小时前`;
  const day = Math.round(hr / 24);
  if (day < 30) return `${day}天前`;
  const month = Math.round(day / 30);
  if (month < 12) return `${month}个月前`;
  const yr = Math.round(month / 12);
  return `${yr}年前`;
}

/** Format an ISO timestamp as a localized absolute time. */
export function formatAbsolute(iso: string): string {
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return iso;
  const d = new Date(then);
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Format an ISO time as a short HH:MM clock time. */
export function formatClock(iso: string): string {
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return iso;
  const d = new Date(then);
  return d.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// State colors & labels
// ---------------------------------------------------------------------------

export interface StateStyle {
  label: string;
  badge: string;
  dot: string;
}

export function runStateStyle(state: RunState): StateStyle {
  switch (state) {
    case "READY_FOR_HUMAN":
      return {
        label: "等待人工处理",
        badge: "bg-emerald-50 text-emerald-700 border-emerald-200",
        dot: "bg-emerald-500",
      };
    case "RUNNING":
      return {
        label: "运行中",
        badge: "bg-sky-50 text-sky-700 border-sky-200",
        dot: "bg-sky-500",
      };
    case "BLOCKED_EXTERNAL":
      return {
        label: "外部阻塞",
        badge: "bg-amber-50 text-amber-700 border-amber-200",
        dot: "bg-amber-500",
      };
    case "REWORK_REQUIRED":
      return {
        label: "需要返工",
        badge: "bg-orange-50 text-orange-700 border-orange-200",
        dot: "bg-orange-500",
      };
    case "FAILED_TERMINAL":
      return {
        label: "终态失败",
        badge: "bg-rose-50 text-rose-700 border-rose-200",
        dot: "bg-rose-500",
      };
    case "WAITING_FOR_OWNER":
      return {
        label: "等待 Owner",
        badge: "bg-violet-50 text-violet-700 border-violet-200",
        dot: "bg-violet-500",
      };
  }
}

export function riskTierStyle(tier: RiskTier): StateStyle {
  switch (tier) {
    case "R0":
      return {
        label: "R0 · 只读",
        badge: "bg-slate-50 text-slate-700 border-slate-200",
        dot: "bg-slate-400",
      };
    case "R1":
      return {
        label: "R1 · 受限编辑",
        badge: "bg-sky-50 text-sky-700 border-sky-200",
        dot: "bg-sky-400",
      };
    case "R2":
      return {
        label: "R2 · 工作流",
        badge: "bg-amber-50 text-amber-700 border-amber-200",
        dot: "bg-amber-400",
      };
    case "R3":
      return {
        label: "R3 · 特权",
        badge: "bg-rose-50 text-rose-700 border-rose-200",
        dot: "bg-rose-400",
      };
    case "UNKNOWN":
      return {
        label: "风险未提供",
        badge: "bg-slate-50 text-slate-600 border-slate-200",
        dot: "bg-slate-400",
      };
  }
}

export function riskTierLabel(tier: RiskTier): string {
  return riskTierStyle(tier).label;
}

export function permissionModeLabel(mode: string): string {
  switch (mode) {
    case "ASK_FOR_APPROVAL":
      return "请求批准";
    case "CONTROLLER_REVIEW":
      return "主控代审";
    case "OWNER_CONTROL":
      return "Owner托管";
    case "CUSTOM":
      return "自定义";
    default:
      return mode;
  }
}
