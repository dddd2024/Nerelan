import type { Task, ActivityEvent, ChangedFile, EvidenceItem } from "@/types";

function ev(
  id: string,
  type: ActivityEvent["type"],
  timestamp: string,
  title: string,
  description: string,
  rawLog?: string,
): ActivityEvent {
  return { id, type, timestamp, title, description, rawLog, expanded: false };
}

const sampleDiff = `--- a/src/lib/format.ts
+++ b/src/lib/format.ts
@@ -12,6 +12,10 @@ import type { RiskTier, RunState } from "@/types";
 export function formatRelativeTime(iso: string, now: Date = new Date()): string {
   const then = Date.parse(iso);
   if (Number.isNaN(then)) return iso;
+  const diffMs = now.getTime() - then;
+  const sec = Math.round(diffMs / 1000);
+  if (sec < 60) return "just now";
   return iso;
 }
`;

const authDiff = `--- a/reverse_agent/trust/authorization.py
+++ b/reverse_agent/trust/authorization.py
@@ -40,7 +40,9 @@ class AuthorizationRouter:
     def is_authorized(self, op: str) -> bool:
-        return op in self.allowed
+        if op not in self.allowed:
+            return False
+        return self.window_active()
`;

// ---------------------------------------------------------------------------
// Task 1 — PR #114 provider-free closure (READY_FOR_HUMAN)
// ---------------------------------------------------------------------------
const taskProviderFree: Task = {
  id: "task-pr114-provider-free",
  title: "PR #114 — 无 Provider 闭环路径",
  issueNumber: 114,
  state: "READY_FOR_HUMAN",
  riskTier: "R1",
  updatedAt: "2026-08-04T22:14:00Z",
  nextAction: "Owner 在精确 Head 审计通过后合并",
  permissionProfile: "OWNER_CONTROL",
  draftPr: {
    number: 114,
    title: "无 Provider 闭环路径",
    url: "https://github.com/dddd2024/reverse-agent/pull/114",
    headSha: "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
    baseSha: "0123456789abcdef0123456789abcdef01234567",
    draft: false,
    state: "open",
  },
  branch: "fix/pr114-provider-free-closure",
  activity: [
    ev("a1", "DISCOVERED", "2026-08-04T09:00:00Z", "已发现", "Issue 从 R1 模板创建并分类。"),
    ev("a2", "VALIDATED", "2026-08-04T09:20:00Z", "已验证", "快照摘要已计算并记录。"),
    ev("a3", "WORKSPACE_READY", "2026-08-04T09:30:00Z", "工作区就绪", "从已批准基线创建新分支。"),
    ev("a4", "EXECUTOR_RUNNING", "2026-08-04T10:00:00Z", "执行器运行中", "Codex ACP 执行器已启动。"),
    ev("a5", "EXECUTOR_FINISHED", "2026-08-04T14:00:00Z", "执行器完成", "实现完成。"),
    ev("a6", "LOCAL_VALIDATED", "2026-08-04T14:30:00Z", "本地验证通过", "pytest + git diff --check 通过。"),
    ev("a7", "COMMITTED", "2026-08-04T14:35:00Z", "已提交", "提交已推送到任务分支。"),
    ev("a8", "PUSHED", "2026-08-04T14:36:00Z", "已推送", "分支已推送到 origin。", "git push origin fix/pr114-provider-free-closure"),
    ev("a9", "DRAFT_PR_OPEN", "2026-08-04T14:40:00Z", "Draft PR 已开启", "PR #114 已创建，目标为 main。"),
    ev("a10", "WORKFLOWS_OBSERVED", "2026-08-04T15:30:00Z", "工作流已观察", "所有必需检查在 Head 上 SUCCESS。", "ci: success"),
    ev("a11", "READY_FOR_HUMAN", "2026-08-04T22:00:00Z", "等待人工处理", "独立精确 Head 审计已通过。"),
  ],
  changes: [
    {
      path: "reverse_agent/platform_v1/provider_free_acceptance.py",
      status: "modified",
      additions: 24,
      deletions: 6,
      diff: authDiff,
    },
    {
      path: "tests/platform_v1/test_acceptance.py",
      status: "modified",
      additions: 18,
      deletions: 2,
      diff: sampleDiff,
    },
  ],
  evidence: [
    {
      id: "e1",
      category: "Authority",
      label: "批准快照",
      value: "APPROVED",
      status: "pass",
      detail: "body_digest_sha256 已记录在 PR 正文中",
      rawJson: JSON.stringify({ body_digest_sha256: "9f8e7d6c5b4a3928170615243342516708192030405061728394051627384950" }, null, 2),
    },
    { id: "e2", category: "本地检查", label: "pytest", value: "12 通过", status: "pass" },
    { id: "e3", category: "工作流检查", label: "ci", value: "SUCCESS", status: "pass" },
    { id: "e4", category: "审计", label: "精确 Head 审计", value: "ACCEPTED a1b2c3d", status: "pass" },
  ],
  authorityStatus: "APPROVED",
  testStatus: "PASS",
  workflowStatus: "SUCCESS",
};

// ---------------------------------------------------------------------------
// Task 2 — Codex quota/protocol blocker (BLOCKED_EXTERNAL)
// ---------------------------------------------------------------------------
const taskCodexBlocked: Task = {
  id: "task-codex-quota-blocked",
  title: "R2 过渡 — Codex ACP 执行",
  issueNumber: 121,
  state: "BLOCKED_EXTERNAL",
  riskTier: "R2",
  updatedAt: "2026-08-04T18:02:00Z",
  blocker: "Codex ACP 配额耗尽 (rate_limit_exceeded)",
  nextAction: "等待配额重置后恢复执行器",
  permissionProfile: "CONTROLLER_REVIEW",
  branch: "transition/r2-codex-acp",
  activity: [
    ev("b1", "DISCOVERED", "2026-08-04T08:00:00Z", "已发现", "过渡 Decision 已批准。"),
    ev("b2", "VALIDATED", "2026-08-04T08:10:00Z", "已验证", "命令计划已生成。"),
    ev("b3", "EXECUTOR_RUNNING", "2026-08-04T09:00:00Z", "执行器运行中", "Codex ACP 已启动。"),
    ev("b4", "EXECUTOR_FINISHED", "2026-08-04T18:00:00Z", "执行器中止", "上游协议错误。", "ERROR: rate_limit_exceeded"),
  ],
  changes: [],
  evidence: [
    { id: "e1", category: "Decision", label: "Decision Preflight", value: "PRE_EXECUTION_AUTHORIZED", status: "pass" },
    { id: "e2", category: "执行器", label: "Codex ACP", value: "rate_limit_exceeded", status: "fail", detail: "上游配额耗尽" },
  ],
  authorityStatus: "APPROVED",
  testStatus: "PENDING",
  workflowStatus: "PENDING",
};

// ---------------------------------------------------------------------------
// Task 3 — Frontend implementation task (RUNNING)
// ---------------------------------------------------------------------------
const taskFrontend: Task = {
  id: "task-frontend-v1",
  title: "前端 V1 — OpenHands 适配 UI",
  issueNumber: 125,
  state: "RUNNING",
  riskTier: "R1",
  updatedAt: "2026-08-05T07:48:00Z",
  nextAction: "继续组件实现",
  permissionProfile: "CONTROLLER_REVIEW",
  branch: "feat/frontend-v1-openhands-ui",
  activity: [
    ev("c1", "DISCOVERED", "2026-08-05T01:00:00Z", "已发现", "前端 V1 工作项已批准。"),
    ev("c2", "WORKSPACE_READY", "2026-08-05T02:00:00Z", "工作区就绪", "Vite + React 19 脚手架就绪。"),
    ev("c3", "EXECUTOR_RUNNING", "2026-08-05T03:00:00Z", "执行器运行中", "正在实现类型、Schema 和组件。"),
  ],
  changes: [
    {
      path: "frontend/src/types/index.ts",
      status: "added",
      additions: 180,
      deletions: 0,
      diff: sampleDiff,
    },
    {
      path: "frontend/src/lib/format.ts",
      status: "modified",
      additions: 12,
      deletions: 4,
      diff: sampleDiff,
    },
  ],
  evidence: [
    { id: "e1", category: "Authority", label: "批准快照", value: "APPROVED", status: "pass" },
    { id: "e2", category: "本地检查", label: "vitest", value: "运行中", status: "pending" },
  ],
  authorityStatus: "APPROVED",
  testStatus: "PENDING",
  workflowStatus: "PENDING",
};

// ---------------------------------------------------------------------------
// Task 4 — Green Authority and Preflight (READY_FOR_HUMAN)
// ---------------------------------------------------------------------------
const taskGreenAuth: Task = {
  id: "task-green-authority-preflight",
  title: "绿色 Authority + Preflight 对账",
  issueNumber: 118,
  state: "READY_FOR_HUMAN",
  riskTier: "R1",
  updatedAt: "2026-08-04T20:30:00Z",
  nextAction: "Owner 审查证据摘要",
  permissionProfile: "OWNER_CONTROL",
  draftPr: {
    number: 118,
    title: "绿色 Authority + Preflight",
    url: "https://github.com/dddd2024/reverse-agent/pull/118",
    headSha: "abcdef0123456789abcdef0123456789abcdef01",
    baseSha: "0123456789abcdef0123456789abcdef01234567",
    draft: false,
    state: "open",
  },
  branch: "fix/green-authority-preflight",
  activity: [
    ev("d1", "DISCOVERED", "2026-08-04T07:00:00Z", "已发现", "对账工作项。"),
    ev("d2", "EXECUTOR_FINISHED", "2026-08-04T12:00:00Z", "执行器完成", "已对账。"),
    ev("d3", "LOCAL_VALIDATED", "2026-08-04T12:30:00Z", "本地验证通过", "所有检查绿色通过。"),
    ev("d4", "WORKFLOWS_OBSERVED", "2026-08-04T13:00:00Z", "工作流已观察", "ci + state-gate SUCCESS。"),
    ev("d5", "READY_FOR_HUMAN", "2026-08-04T20:00:00Z", "等待人工处理", "等待 Owner 审查。"),
  ],
  changes: [
    {
      path: "reverse_agent/architecture/authority.py",
      status: "modified",
      additions: 8,
      deletions: 1,
      diff: authDiff,
    },
  ],
  evidence: [
    { id: "e1", category: "Authority", label: "Decision Preflight", value: "PRE_EXECUTION_AUTHORIZED", status: "pass" },
    { id: "e2", category: "State Gate", label: "State Gate", value: "PASS", status: "pass" },
    { id: "e3", category: "工作流检查", label: "ci", value: "SUCCESS", status: "pass" },
  ],
  authorityStatus: "APPROVED",
  testStatus: "PASS",
  workflowStatus: "SUCCESS",
};

// ---------------------------------------------------------------------------
// Task 5 — Owner review pending (WAITING_FOR_OWNER)
// ---------------------------------------------------------------------------
const taskOwnerReview: Task = {
  id: "task-owner-review-pending",
  title: "R1 验收 — 等待 Owner 审查",
  issueNumber: 130,
  state: "WAITING_FOR_OWNER",
  riskTier: "R1",
  updatedAt: "2026-08-05T06:10:00Z",
  blocker: "等待 Owner/维护者批准标签",
  nextAction: "Owner 应用 r1-approved 标签",
  permissionProfile: "ASK_FOR_APPROVAL",
  branch: "feat/owner-review-pending",
  activity: [
    ev("f1", "DISCOVERED", "2026-08-05T05:00:00Z", "已发现", "CANDIDATE 工作项已从模板创建。"),
    ev("f2", "VALIDATED", "2026-08-05T05:30:00Z", "已验证", "等待批准标签。"),
  ],
  changes: [],
  evidence: [
    { id: "e1", category: "Authority", label: "批准标签", value: "CANDIDATE", status: "pending", detail: "r1-approved 尚未应用" },
  ],
  authorityStatus: "CANDIDATE",
  testStatus: "PENDING",
  workflowStatus: "PENDING",
};

// ---------------------------------------------------------------------------
// Task 6 — Expired unattended window (FAILED_TERMINAL)
// ---------------------------------------------------------------------------
const taskExpiredWindow: Task = {
  id: "task-expired-unattended-window",
  title: "R2 无人值守窗口 — 已过期",
  issueNumber: 122,
  state: "FAILED_TERMINAL",
  riskTier: "R2",
  updatedAt: "2026-08-04T03:00:00Z",
  blocker: "autonomousWindow.expiresAt 已过 (window_expired)",
  nextAction: "请求新的有界 Decision 以继续",
  permissionProfile: "OWNER_CONTROL",
  branch: "transition/r2-window-expired",
  activity: [
    ev("g1", "DISCOVERED", "2026-08-03T20:00:00Z", "已发现", "窗口开启至 03:00。"),
    ev("g2", "EXECUTOR_RUNNING", "2026-08-03T20:30:00Z", "执行器运行中", "在窗口内工作。"),
    ev("g3", "EXECUTOR_FINISHED", "2026-08-04T03:00:00Z", "窗口过期", "停止条件 window_expired 触发。", "STOP: window_expired"),
  ],
  changes: [],
  evidence: [
    { id: "e1", category: "停止", label: "window_expired", value: "TRIGGERED", status: "fail" },
    { id: "e2", category: "Authority", label: "窗口", value: "EXPIRED", status: "fail" },
  ],
  authorityStatus: "EXPIRED",
  testStatus: "PENDING",
  workflowStatus: "PENDING",
};

// ---------------------------------------------------------------------------
// Task 7 — Rework required (REWORK_REQUIRED)
// ---------------------------------------------------------------------------
const taskRework: Task = {
  id: "task-rework-required",
  title: "R1 — 独立审计发现问题",
  issueNumber: 133,
  state: "REWORK_REQUIRED",
  riskTier: "R1",
  updatedAt: "2026-08-05T05:00:00Z",
  blocker: "审计拒绝了 Head: 缺少证据来源",
  nextAction: "重新记录证据来源并重跑本地检查",
  permissionProfile: "CONTROLLER_REVIEW",
  draftPr: {
    number: 133,
    title: "需要返工",
    url: "https://github.com/dddd2024/reverse-agent/pull/133",
    headSha: "f00dface0123456789abcdef0123456789abcdef",
    baseSha: "0123456789abcdef0123456789abcdef01234567",
    draft: true,
    state: "open",
  },
  branch: "feat/rework-required",
  activity: [
    ev("h1", "DISCOVERED", "2026-08-04T22:00:00Z", "已发现", "实现已起草。"),
    ev("h2", "EXECUTOR_FINISHED", "2026-08-04T23:00:00Z", "执行器完成", "已提交审计。"),
    ev("h3", "READY_FOR_HUMAN", "2026-08-05T04:00:00Z", "审计拒绝", "证据来源缺失。", "AUDIT: REJECT"),
  ],
  changes: [
    { path: "reverse_agent/evidence.py", status: "modified", additions: 4, deletions: 2, diff: authDiff },
  ],
  evidence: [
    { id: "e1", category: "审计", label: "精确 Head 审计", value: "REJECTED", status: "fail", detail: "缺少来源" },
  ],
  authorityStatus: "APPROVED",
  testStatus: "FAIL",
  workflowStatus: "FAILURE",
};

// ---------------------------------------------------------------------------
// Task 8 — Operation budget exhausted (FAILED_TERMINAL)
// ---------------------------------------------------------------------------
const taskBudgetExhausted: Task = {
  id: "task-budget-exhausted",
  title: "R2 — 操作预算耗尽",
  issueNumber: 140,
  state: "FAILED_TERMINAL",
  riskTier: "R2",
  updatedAt: "2026-08-04T16:00:00Z",
  blocker: "max_merges_to_main 预算耗尽",
  nextAction: "请求修订 Decision 提高预算或停止",
  permissionProfile: "OWNER_CONTROL",
  branch: "transition/r2-budget-exhausted",
  activity: [
    ev("i1", "DISCOVERED", "2026-08-04T08:00:00Z", "已发现", "设置 2 次合并预算。"),
    ev("i2", "EXECUTOR_RUNNING", "2026-08-04T09:00:00Z", "执行器运行中", "在预算内合并。"),
    ev("i3", "EXECUTOR_FINISHED", "2026-08-04T16:00:00Z", "预算耗尽", "停止条件 budget_exhausted 触发。", "STOP: budget_exhausted"),
  ],
  changes: [],
  evidence: [
    { id: "e1", category: "预算", label: "max_merges_to_main", value: "2/2", status: "fail" },
    { id: "e2", category: "停止", label: "budget_exhausted", value: "TRIGGERED", status: "fail" },
  ],
  authorityStatus: "APPROVED",
  testStatus: "PENDING",
  workflowStatus: "PENDING",
};

export const FIXTURE_TASKS: Task[] = [
  taskProviderFree,
  taskCodexBlocked,
  taskFrontend,
  taskGreenAuth,
  taskOwnerReview,
  taskExpiredWindow,
  taskRework,
  taskBudgetExhausted,
];

export function findFixtureTask(id: string): Task | undefined {
  return FIXTURE_TASKS.find((t) => t.id === id);
}

export type { Task, ActivityEvent, ChangedFile, EvidenceItem };
