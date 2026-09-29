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

/*
 * Status surfaces are token-driven, never palette-driven.
 *
 * These previously returned Tailwind's *light* ramp (`bg-emerald-50`,
 * `text-emerald-700`, ...). Those are absolute colors, so in the dark theme
 * every badge rendered as a pale mint/amber chip on a dark workspace: the
 * single loudest element on an otherwise quiet page, and the opposite of the
 * contract's "neutral surfaces, sparse accent color".
 *
 * The tinted look is kept, but derived from theme-aware tokens with an alpha
 * surface, so light and dark both resolve to their own ramp.
 */

/** `success` tinted chip: green semantics. */
export const TONE_SUCCESS = "border-ra-status-success/35 bg-ra-status-success/10 text-ra-status-success";
/** `active` tinted chip: the accent, i.e. work is moving. */
export const TONE_ACTIVE = "border-ra-accent/35 bg-ra-accent/10 text-ra-accent";
/** `attention` tinted chip: needs a human, but nothing is broken. */
export const TONE_WARNING = "border-ra-status-warning/35 bg-ra-status-warning/10 text-ra-status-warning";
/** `failure` tinted chip. */
export const TONE_ERROR = "border-ra-status-error/35 bg-ra-status-error/10 text-ra-status-error";
/** Ordinary chip: deliberately quiet, for states that are not exceptional. */
export const TONE_NEUTRAL = "border-ra-border bg-ra-tertiary text-ra-text-secondary";

/*
 * Borderless variants.
 *
 * A status that is rendered *inside* an already-bordered surface (a card, a
 * row, a list item) must not add a second outline: nested borders read as
 * visual noise and fight the card's own edge. These carry only the tint and
 * the foreground colour.
 */
export const TONE_SUCCESS_FLAT = "bg-ra-status-success/12 text-ra-status-success";
export const TONE_ACTIVE_FLAT = "bg-ra-accent/12 text-ra-accent";
export const TONE_WARNING_FLAT = "bg-ra-status-warning/12 text-ra-status-warning";
export const TONE_ERROR_FLAT = "bg-ra-status-error/12 text-ra-status-error";
export const TONE_NEUTRAL_FLAT = "bg-ra-light text-ra-text-secondary";
export const TONE_MUTED_FLAT = "bg-ra-light text-ra-text-tertiary";

export function runStateStyle(state: RunState | string): StateStyle {
  switch (state) {
    case "READY_FOR_HUMAN":
      /*
       * The Runs page used to carry its own `STATE_LABELS` table, so this one
       * state read "等待人工处理" on the task list and "等待人工审查" on /runs.
       * #448 §9 forbids presenting one authoritative state two ways, so the
       * two tables were collapsed into this mapping. The Runs wording won
       * because it is already pinned by the committed contract tests
       * (`e2e/states.spec.ts`, `tests/runs.test.tsx`) and because "审查"
       * describes a review gate, whereas "处理" collides with the
       * OWNER_ACTION_REQUIRED liveness label "需要 Owner 处理".
       */
      return { label: "等待人工审查", badge: TONE_SUCCESS, dot: "bg-ra-status-success" };
    case "RUNNING":
      return { label: "运行中", badge: TONE_ACTIVE, dot: "bg-ra-accent" };
    case "BLOCKED_EXTERNAL":
      // "Blocked" is an error treatment across the product, not a caution:
      // the Home activity stream, the task list and the Goal header all
      // report it in the error tone. Using the warning tone here made the
      // same state render amber in one table and red in another.
      return { label: "外部阻塞", badge: TONE_ERROR, dot: "bg-ra-status-error" };
    case "REWORK_REQUIRED":
      return { label: "需要返工", badge: TONE_WARNING, dot: "bg-ra-status-warning" };
    case "FAILED_TERMINAL":
      return { label: "终态失败", badge: TONE_ERROR, dot: "bg-ra-status-error" };
    case "WAITING_FOR_OWNER":
      return { label: "等待 Owner", badge: TONE_WARNING, dot: "bg-ra-status-warning" };
    default:
      /*
       * Total function on purpose: the platform run read-model and the task
       * read-model do not share a TypeScript enum, and an unrecognised state
       * must still render as quiet text rather than as `undefined`.
       */
      return { label: state, badge: TONE_NEUTRAL, dot: "bg-ra-status-stopped" };
  }
}

/**
 * The tone family a run state belongs to.
 *
 * Surfaces that need a differently-shaped rendition of the same state (the
 * Runs page renders a borderless chip inside an already-bordered card) read
 * the tone instead of keeping a second copy of the whole colour table.
 */
export function runStateTone(
  state: RunState | string,
): "success" | "accent" | "warning" | "error" {
  switch (state) {
    case "READY_FOR_HUMAN":
      return "success";
    case "RUNNING":
      return "accent";
    case "BLOCKED_EXTERNAL":
    case "FAILED_TERMINAL":
      return "error";
    case "REWORK_REQUIRED":
    case "WAITING_FOR_OWNER":
      return "warning";
    default:
      return "warning";
  }
}

export function riskTierStyle(tier: RiskTier): StateStyle {
  switch (tier) {
    case "R0":
      return { label: "R0 · 只读", badge: TONE_NEUTRAL, dot: "bg-ra-status-stopped" };
    case "R1":
      return { label: "R1 · 受限编辑", badge: TONE_NEUTRAL, dot: "bg-ra-status-stopped" };
    case "R2":
      return { label: "R2 · 工作流", badge: TONE_WARNING, dot: "bg-ra-status-warning" };
    case "R3":
      return { label: "R3 · 特权", badge: TONE_ERROR, dot: "bg-ra-status-error" };
    case "UNKNOWN":
      // Healthy/unknown state stays implicit; only elevated tiers get colour.
      return { label: "风险未提供", badge: TONE_NEUTRAL, dot: "bg-ra-status-stopped" };
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
