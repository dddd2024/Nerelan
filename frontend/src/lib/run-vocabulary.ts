/**
 * Single source of truth for run/liveness/activity vocabulary.
 *
 * `#280` owns structured execution observability and `#281` owns authoritative
 * state convergence, but the two surfaces that render that truth — the Home
 * activity stream and the Agent Runs page — had grown *two* independent copies
 * of the same label and tone tables. They had already drifted: the same
 * `OWNER_ACTION_REQUIRED` liveness read red on Home and amber on Runs, and the
 * same `BLOCKED` activity category read red on Home and amber on Runs.
 *
 * `#448` §9 forbids contradictory state presentation, so the mapping now lives
 * here and both surfaces consume it.
 *
 * Tone vocabulary (`#448` §10 — normal is quiet, exceptional is explicit):
 *
 * - `accent`    the accent token: work is moving.
 * - `success`   a verified, positive outcome.
 * - `warning`   a human is needed, but nothing is broken.
 * - `error`     something failed or is suspected stale.
 * - `neutral`   ordinary, non-exceptional information.
 */
import {
  TONE_SUCCESS,
  TONE_ACTIVE,
  TONE_WARNING,
  TONE_ERROR,
  TONE_NEUTRAL,
  TONE_SUCCESS_FLAT,
  TONE_ACTIVE_FLAT,
  TONE_WARNING_FLAT,
  TONE_ERROR_FLAT,
  TONE_NEUTRAL_FLAT,
} from "@/lib/format";
import { cn } from "@/lib/cn";

export type RunTone = "accent" | "success" | "warning" | "error" | "neutral";

/** Tinted + outlined chip, for a status that stands on its own surface. */
const TONE_BADGE: Record<RunTone, string> = {
  accent: TONE_ACTIVE,
  success: TONE_SUCCESS,
  warning: TONE_WARNING,
  error: TONE_ERROR,
  neutral: TONE_NEUTRAL,
};

/** Tinted chip without its own outline, for use inside an existing surface. */
const TONE_BADGE_FLAT: Record<RunTone, string> = {
  accent: TONE_ACTIVE_FLAT,
  success: TONE_SUCCESS_FLAT,
  warning: TONE_WARNING_FLAT,
  error: TONE_ERROR_FLAT,
  neutral: TONE_NEUTRAL_FLAT,
};

/** Foreground-only tone, for dots and inline icons. */
const TONE_TEXT: Record<RunTone, string> = {
  accent: "text-ra-accent",
  success: "text-ra-status-success",
  warning: "text-ra-status-warning",
  error: "text-ra-status-error",
  neutral: "text-ra-text-tertiary",
};

const TONE_DOT: Record<RunTone, string> = {
  accent: "bg-ra-accent",
  success: "bg-ra-status-success",
  warning: "bg-ra-status-warning",
  error: "bg-ra-status-error",
  neutral: "bg-ra-text-tertiary",
};

export function toneBadge(tone: RunTone, flat = false): string {
  return (flat ? TONE_BADGE_FLAT : TONE_BADGE)[tone];
}

export function toneText(tone: RunTone): string {
  return TONE_TEXT[tone];
}

export function toneDot(tone: RunTone): string {
  return TONE_DOT[tone];
}

/* ------------------------------------------------------------------------ */
/* Liveness                                                                  */
/* ------------------------------------------------------------------------ */

const LIVENESS: Record<string, { label: string; tone: RunTone }> = {
  ACTIVE: { label: "有新活动", tone: "accent" },
  WAITING: { label: "等待中", tone: "neutral" },
  VALIDATING: { label: "验证中", tone: "accent" },
  BLOCKED: { label: "已阻塞", tone: "error" },
  OWNER_ACTION_REQUIRED: { label: "需要 Owner 处理", tone: "warning" },
  STALE: { label: "疑似停滞", tone: "error" },
  TERMINAL: { label: "已结束", tone: "neutral" },
  UNKNOWN: { label: "活跃度未知", tone: "neutral" },
};

/** Normalize a runtime enum value for table lookup. */
export function enumKey(value: string | undefined): string {
  return String(value ?? "UNKNOWN").toUpperCase();
}

export function livenessLabel(value: string | undefined): string {
  return LIVENESS[enumKey(value)]?.label ?? LIVENESS.UNKNOWN.label;
}

export function livenessTone(value: string | undefined): RunTone {
  return LIVENESS[enumKey(value)]?.tone ?? "neutral";
}

export function livenessBadgeClass(value: string | undefined, flat = false): string {
  return toneBadge(livenessTone(value), flat);
}

export function livenessDotClass(value: string | undefined): string {
  return toneDot(livenessTone(value));
}

/* ------------------------------------------------------------------------ */
/* Execution stage                                                           */
/* ------------------------------------------------------------------------ */

const STAGES: Record<string, string> = {
  PLAN: "计划",
  PREPARE: "准备",
  EXECUTE: "执行",
  VERIFY: "验证",
  REVIEW: "审查",
  RECOVERY: "恢复",
  PUBLISH: "发布",
  COMPLETE: "完成",
  TERMINAL: "终态",
  UNKNOWN: "未知阶段",
};

export function executionStageLabel(value: string | undefined): string {
  return STAGES[enumKey(value)] ?? STAGES.UNKNOWN;
}

/* ------------------------------------------------------------------------ */
/* Activity category                                                         */
/* ------------------------------------------------------------------------ */

const ACTIVITY_CATEGORIES: Record<string, { label: string; tone: RunTone }> = {
  PLAN: { label: "计划", tone: "neutral" },
  READ: { label: "读取", tone: "neutral" },
  SEARCH: { label: "搜索", tone: "neutral" },
  EDIT: { label: "编辑", tone: "neutral" },
  COMMAND: { label: "命令", tone: "accent" },
  TEST: { label: "测试", tone: "success" },
  VERIFY: { label: "验证", tone: "success" },
  AGENT_STARTED: { label: "Agent 开始", tone: "accent" },
  AGENT_WAITING: { label: "Agent 等待", tone: "neutral" },
  AGENT_COMPLETED: { label: "Agent 完成", tone: "neutral" },
  CHECKPOINT: { label: "检查点", tone: "success" },
  RECOVERY: { label: "恢复", tone: "warning" },
  BLOCKED: { label: "阻塞", tone: "error" },
  OWNER_ACTION_REQUIRED: { label: "需要 Owner 处理", tone: "warning" },
  PUBLICATION: { label: "发布", tone: "success" },
};

export function activityCategoryLabel(value: string | undefined): string {
  return ACTIVITY_CATEGORIES[enumKey(value)]?.label ?? "活动";
}

/** Foreground tone for an activity row's dot/icon. */
export function activityCategoryClass(value: string | undefined): string {
  return cn(toneText(ACTIVITY_CATEGORIES[enumKey(value)]?.tone ?? "neutral"));
}

/* ------------------------------------------------------------------------ */
/* Server activity titles                                                    */
/* ------------------------------------------------------------------------ */

/**
 * The generic `current_activity.title` the run read-model emits per category.
 *
 * `reverse_agent/platform_v1/run_read_model.py::_activity_title` derives the
 * title from the category and nothing else, so the title is a static English
 * humanisation rather than authored per-instance content: `AGENT_COMPLETED` is
 * always "Agent completed". The product already owns a better, product-language
 * name for exactly that fact, so echoing both printed one fact twice in two
 * languages — live data read `当前活动：Agent completed · Agent 完成`, with the
 * readable half demoted to the quieter slot.
 *
 * Kept as an explicit map instead of a heuristic so the failure direction stays
 * safe: a title that is not listed here is treated as authored content and is
 * shown *next to* the label. The dangerous mistake — hiding text the server
 * actually wrote — cannot happen here; the worst case is the duplicate this map
 * exists to remove.
 */
const GENERIC_ACTIVITY_TITLES: Record<string, string> = {
  PLAN: "Task planned",
  READ: "Repository read",
  SEARCH: "Repository search",
  EDIT: "Repository change",
  COMMAND: "Approved command",
  TEST: "Validation command",
  VERIFY: "Validation result",
  AGENT_STARTED: "Agent started",
  AGENT_WAITING: "Agent waiting",
  AGENT_COMPLETED: "Agent completed",
  CHECKPOINT: "Checkpoint accepted",
  RECOVERY: "Recovery activity",
  BLOCKED: "Run blocked",
  OWNER_ACTION_REQUIRED: "Owner action required",
  PUBLICATION: "Publication activity",
};

/** The read-model's `.get(category, "Run activity")` fallback. */
const GENERIC_ACTIVITY_FALLBACK_TITLE = "Run activity";

/**
 * True when the server title only restates the category, i.e. when rendering it
 * beside the label would print the same fact twice.
 *
 * An absent title is also a restatement: there is nothing to show but the label.
 * The mock fixtures deliberately carry authored titles ("运行集成测试"), which
 * this function reports as `false`, so those keep their current presentation.
 */
export function activityTitleRestatesCategory(
  category: string | undefined,
  title: string | undefined,
): boolean {
  const value = (title ?? "").trim();
  if (value === "") return true;
  return (
    value === GENERIC_ACTIVITY_TITLES[enumKey(category)] ||
    value === GENERIC_ACTIVITY_FALLBACK_TITLE
  );
}
