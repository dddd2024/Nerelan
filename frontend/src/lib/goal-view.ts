/**
 * How a goal reads to its Owner: one clean title, the issue it comes from, one
 * state, and what the agent is doing in plain words.
 *
 * Every list, header and sidebar uses these, so a goal never says "正在执行"
 * in one place and "已停下" in another.
 */
import type { PlatformGoal, PlatformTaskActivity } from "@/lib/platform-client";
import { displayTitle, leadingBracket } from "@/lib/display-title";
import { failureText } from "@/lib/run-explain";

/** `#1488 [Runtime] Detect …` → `Detect …`: the issue number and the tracker's bracket tags are metadata. */
export function cleanIssueTitle(title: string): string {
  let text = title.trim().replace(/^#\d+\s*/, "");
  for (let guard = 0; guard < 4; guard += 1) {
    const bracket = leadingBracket(text);
    if (!bracket || !text.slice(bracket.end).trim()) break;
    text = text.slice(bracket.end).trim();
  }
  return text.replace(/^[:：\-—\s]+/, "") || title.trim();
}

export function goalTitle(goal: Pick<PlatformGoal, "title">, maxLength = 80): string {
  const title = cleanIssueTitle(displayTitle(goal.title, 400));
  return title.length > maxLength ? `${title.slice(0, maxLength - 1)}…` : title;
}

export interface IssueRef {
  number: number;
  url: string;
}

/** The GitHub issue a goal resolves: from the "Resolve https://…/issues/N" objective or a "#N" title. */
export function issueRef(goal: Pick<PlatformGoal, "title" | "objective" | "repository">): IssueRef | null {
  const link = /https:\/\/github\.com\/([\w.-]+\/[\w.-]+)\/issues\/(\d+)/.exec(goal.objective ?? "");
  if (link) return { number: Number(link[2]), url: link[0] };
  const number = /^#(\d+)\b/.exec(goal.title ?? "")?.[1];
  if (number && goal.repository) {
    return { number: Number(number), url: `https://github.com/${goal.repository}/issues/${number}` };
  }
  return null;
}

/**
 * The objective as prose. A goal drafted from an issue stores
 * "Resolve <url> # [Tag] Title ## Problem …": the URL and the repeated title
 * are dropped and the markdown markers removed, keeping the issue's own words.
 */
export function objectiveText(goal: Pick<PlatformGoal, "objective">): string {
  let text = (goal.objective ?? "").trim();
  text = text.replace(/^Resolve\s+https:\/\/github\.com\/\S+\s*/i, "");
  text = text.replace(/^#\s+[^\n#]*?(?=\s##\s|\n|$)/, "");
  return text
    .replace(/\s*#{2,6}\s+/g, "\n\n")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\s+-\s+(?=\S)/g, "\n· ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export type GoalStateKey = "needs_you" | "running" | "queued" | "stopped" | "cancelled" | "done";
export type GoalGroup = "needs_you" | "active" | "stopped" | "ended";
export type GoalTone = "live" | "stopped" | "done" | "waiting" | "idle";

export interface GoalState {
  key: GoalStateKey;
  group: GoalGroup;
  /** Two to four characters: the pill or badge. */
  label: string;
  /** One sentence under the title. */
  detail: string;
  tone: GoalTone;
}

const RUNNING = new Set(["RUNNING", "RUNNING_FIXTURE", "VALIDATING", "PREPARING_WORKSPACE"]);
const READY = new Set(["READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"]);
const STOPPED = new Set(["FAILED", "BLOCKED", "INTERRUPTED"]);

const BEFORE_RUN: Record<string, [string, string]> = {
  DRAFT: ["草稿", "等你生成计划"],
  PLANNED: ["待审阅", "计划已生成，等你审阅后开始"],
  APPROVED: ["待开始", "已批准，等你开启执行窗口"],
};

/** The one state every view shows for a goal. */
export function goalState(goal: Pick<PlatformGoal, "status" | "task_links">): GoalState {
  const before = BEFORE_RUN[goal.status];
  if (before) return { key: "needs_you", group: "needs_you", label: before[0], detail: before[1], tone: "waiting" };
  const links = goal.task_links ?? [];
  if (goal.status === "INVALIDATED") {
    return { key: "cancelled", group: "ended", label: "已作废", detail: "目标已被新版本取代", tone: "idle" };
  }
  const running = links.find((link) => RUNNING.has(link.status));
  // The host marks a goal BLOCKED once a step stopped; a stale RUNNING link must not hide that.
  if (running && !(goal.status === "BLOCKED" && links.some((link) => STOPPED.has(link.status)))) {
    return { key: "running", group: "active", label: "进行中", detail: humanActivity(running.activity) || "Agent 已启动", tone: "live" };
  }
  const stopped = links.find((link) => STOPPED.has(link.status));
  if (stopped) {
    const tries = (stopped.attempts?.length ?? 0) + 1;
    return {
      key: "stopped", group: "stopped", label: "已停下",
      detail: `${failureText(stopped.failure).label}${tries > 1 ? `（已试 ${tries} 次）` : ""}`, tone: "stopped",
    };
  }
  if (links.length > 0 && links.every((link) => link.status === "CANCELLED")) {
    return { key: "cancelled", group: "ended", label: "已取消", detail: "这个目标已取消，不会再执行", tone: "idle" };
  }
  const live = links.filter((link) => link.status !== "CANCELLED");
  if (live.length > 0 && live.every((link) => READY.has(link.status))) {
    const published = live.some((link) => link.publication);
    return {
      key: "needs_you", group: "needs_you", label: "待审查",
      detail: published ? "已开 Draft PR，等你审查" : "执行完成，等你审查结果", tone: "done",
    };
  }
  if (live.length > 0) {
    const ready = live.filter((link) => READY.has(link.status)).length;
    return { key: "queued", group: "active", label: "排队中", detail: `已完成 ${ready}/${live.length} 步，等待执行`, tone: "waiting" };
  }
  if (goal.status === "COMPLETED") {
    return { key: "needs_you", group: "needs_you", label: "待审查", detail: "执行完成，等你审查结果", tone: "done" };
  }
  if (goal.status === "RUNNING") {
    return { key: "queued", group: "active", label: "排队中", detail: "等待执行窗口派发", tone: "waiting" };
  }
  return { key: "done", group: "ended", label: "已结束", detail: "", tone: "idle" };
}

export const GOAL_TONE_TEXT: Record<GoalTone, string> = {
  live: "text-ra-accent",
  stopped: "text-ra-status-error",
  done: "text-ra-status-running",
  waiting: "text-ra-text-secondary",
  idle: "text-ra-text-tertiary",
};

export const GOAL_TONE_DOT: Record<GoalTone, string> = {
  live: "bg-ra-accent",
  stopped: "bg-ra-status-error",
  done: "bg-ra-status-running",
  waiting: "bg-ra-status-warning",
  idle: "bg-ra-border-strong",
};

function fileName(path: string): string {
  const clean = path.replace(/["']/g, "").trim();
  return clean.split(/[\\/]/).filter(Boolean).pop() ?? clean;
}

const SHELL_PREFIX = /^(?:bash|powershell|pwsh|cmd|sh)\s+(?:-c\s+)?/i;

/** "bash python -m pytest -q tests/…" → "正在跑测试"; the raw command stays one click away. */
export function humanCommand(raw: string): string {
  const command = raw.trim().replace(SHELL_PREFIX, "").replace(/^["']/, "");
  if (/\bpytest\b/.test(command)) return "正在跑测试";
  if (/\b(vitest|npm (run )?test|npx vitest|playwright)\b/.test(command)) return "正在跑前端测试";
  if (/\b(tsc|eslint|npm run (lint|build)|ruff|mypy)\b/.test(command)) return "正在检查代码";
  const read = /^(?:Get-Content|cat|type|head|tail|less|sed\s+-n\s+\S+)\s+(?:-\w+\s+)*(\S+)/i.exec(command);
  if (read) return `正在读 ${fileName(read[1])}`;
  if (/^(rg|grep|Select-String|findstr|git grep)\b/i.test(command)) return "正在搜索代码";
  const edit = /^(?:edit|write|apply_patch)\s+(\S+)/i.exec(command);
  if (edit) return `正在修改 ${fileName(edit[1])}`;
  if (/^git\b/.test(command)) return "正在查看 Git 记录";
  if (/^gh\b/.test(command)) return "正在读 GitHub";
  if (/^(ls|dir|Get-ChildItem|find|tree)\b/i.test(command)) return "正在查看目录";
  return "正在执行命令";
}

/** The newest activity of a running task as a short phrase. */
export function humanActivity(activity?: Pick<PlatformTaskActivity, "title" | "description" | "type"> | null): string {
  if (!activity) return "";
  const text = (activity.description || activity.title || "").trim();
  if (!text) return "";
  if (/^(bash|powershell|pwsh|cmd|sh|edit|write|apply_patch)\b/i.test(text)) return humanCommand(text);
  if (/^(read|view)\s+\S/i.test(text)) return `正在读 ${fileName(text.split(/\s+/)[1])}`;
  if (/^(Model selected|选择模型)/.test(text)) return "正在选择模型";
  // The agent's own sentence: keep it, in one line.
  const line = text.replace(/\s+/g, " ");
  return line.length > 60 ? `${line.slice(0, 59)}…` : line;
}

/**
 * A task's title as a person reads it. Goal tasks are stored as
 * "[<goal title>] implement Implement #1488\n\n<instructions>"; they read as
 * "<clean goal title> · 实现". Other tasks keep their own short title.
 */
export function taskTitle(raw: string, maxLength = 120): string {
  const source = (raw ?? "").trim();
  if (leadingBracket(source)) return `${cleanIssueTitle(displayTitle(source, maxLength))} · ${stepTitle(source)}`;
  return cleanIssueTitle(displayTitle(source, maxLength));
}

/** "Implement #1488" / "review" → "实现" / "审查"; anything else is the plan's own title. */
export function stepTitle(raw: string, role?: string): string {
  const roleName = STEP_ROLES[(role ?? "").toLowerCase()];
  const source = (raw ?? "").replace(/\r?\n[\s\S]*$/, "").trim();
  const bracket = leadingBracket(source);
  const rest = bracket ? source.slice(bracket.end).trim() : source;
  // Execution titles repeat the plan id first ("implement Implement #1488"): drop that token only.
  const words = rest.replace(/^(?:[\w-]+|T\d{2,4})\s+(?=(?:implement|review|test|verify|plan)\b)/i, "").trim();
  // Generated steps ("Implement #1488", "review") read as their role; a plan's own title stays.
  const kind = /^(implement|review|test|verify|plan)\b(?:\s*#\d+)?\s*$/i.exec(words)?.[1]?.toLowerCase();
  if (kind && STEP_ROLES[kind]) return STEP_ROLES[kind];
  return displayTitle(words || source) || roleName || "步骤";
}

const STEP_ROLES: Record<string, string> = {
  implement: "实现", coder: "实现", review: "审查", reviewer: "审查",
  test: "测试", verify: "验证", plan: "规划", planner: "规划",
};
