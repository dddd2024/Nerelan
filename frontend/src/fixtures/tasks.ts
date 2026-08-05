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
  title: "PR #114 — provider-free closure path",
  issueNumber: 114,
  state: "READY_FOR_HUMAN",
  riskTier: "R1",
  updatedAt: "2026-08-04T22:14:00Z",
  nextAction: "Owner to merge after exact-head audit accepts",
  permissionProfile: "OWNER_CONTROL",
  draftPr: {
    number: 114,
    title: "provider-free closure path",
    url: "https://github.com/dddd2024/reverse-agent/pull/114",
    headSha: "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
    baseSha: "0123456789abcdef0123456789abcdef01234567",
    draft: false,
    state: "open",
  },
  branch: "fix/pr114-provider-free-closure",
  activity: [
    ev("a1", "DISCOVERED", "2026-08-04T09:00:00Z", "Discovered", "Issue triaged from R1 template."),
    ev("a2", "VALIDATED", "2026-08-04T09:20:00Z", "Validated", "Snapshot digest computed and recorded."),
    ev("a3", "WORKSPACE_READY", "2026-08-04T09:30:00Z", "Workspace ready", "Fresh branch from approved base."),
    ev("a4", "EXECUTOR_RUNNING", "2026-08-04T10:00:00Z", "Executor running", "Codex ACP executor started."),
    ev("a5", "EXECUTOR_FINISHED", "2026-08-04T14:00:00Z", "Executor finished", "Implementation complete."),
    ev("a6", "LOCAL_VALIDATED", "2026-08-04T14:30:00Z", "Local validated", "pytest + git diff --check clean."),
    ev("a7", "COMMITTED", "2026-08-04T14:35:00Z", "Committed", "Commit pushed to task branch."),
    ev("a8", "PUSHED", "2026-08-04T14:36:00Z", "Pushed", "Branch pushed to origin.", "git push origin fix/pr114-provider-free-closure"),
    ev("a9", "DRAFT_PR_OPEN", "2026-08-04T14:40:00Z", "Draft PR opened", "PR #114 created against main."),
    ev("a10", "WORKFLOWS_OBSERVED", "2026-08-04T15:30:00Z", "Workflows observed", "All required checks SUCCESS on head.", "ci: success"),
    ev("a11", "READY_FOR_HUMAN", "2026-08-04T22:00:00Z", "Ready for human", "Independent exact-head audit accepted."),
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
      label: "Approval snapshot",
      value: "APPROVED",
      status: "pass",
      detail: "body_digest_sha256 recorded in PR body",
      rawJson: JSON.stringify({ body_digest_sha256: "9f8e7d6c5b4a3928170615243342516708192030405061728394051627384950" }, null, 2),
    },
    { id: "e2", category: "Tests", label: "pytest", value: "12 passed", status: "pass" },
    { id: "e3", category: "Workflows", label: "ci", value: "SUCCESS", status: "pass" },
    { id: "e4", category: "Audit", label: "Exact-head audit", value: "ACCEPTED a1b2c3d", status: "pass" },
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
  title: "R2 transition — Codex ACP execution",
  issueNumber: 121,
  state: "BLOCKED_EXTERNAL",
  riskTier: "R2",
  updatedAt: "2026-08-04T18:02:00Z",
  blocker: "Codex ACP quota exhausted (rate_limit_exceeded)",
  nextAction: "Wait for quota reset, then resume executor",
  permissionProfile: "CONTROLLER_REVIEW",
  branch: "transition/r2-codex-acp",
  activity: [
    ev("b1", "DISCOVERED", "2026-08-04T08:00:00Z", "Discovered", "Transition Decision approved."),
    ev("b2", "VALIDATED", "2026-08-04T08:10:00Z", "Validated", "Command plan generated."),
    ev("b3", "EXECUTOR_RUNNING", "2026-08-04T09:00:00Z", "Executor running", "Codex ACP started."),
    ev("b4", "EXECUTOR_FINISHED", "2026-08-04T18:00:00Z", "Executor halted", "Protocol error from upstream.", "ERROR: rate_limit_exceeded"),
  ],
  changes: [],
  evidence: [
    { id: "e1", category: "Decision", label: "Decision Preflight", value: "PRE_EXECUTION_AUTHORIZED", status: "pass" },
    { id: "e2", category: "Executor", label: "Codex ACP", value: "rate_limit_exceeded", status: "fail", detail: "Upstream quota exhausted" },
  ],
  authorityStatus: "APPROVED",
  testStatus: "PENDING",
  workflowStatus: "UNKNOWN",
};

// ---------------------------------------------------------------------------
// Task 3 — Frontend implementation task (RUNNING)
// ---------------------------------------------------------------------------
const taskFrontend: Task = {
  id: "task-frontend-v1",
  title: "Frontend V1 — OpenHands-adapted UI",
  issueNumber: 125,
  state: "RUNNING",
  riskTier: "R1",
  updatedAt: "2026-08-05T07:48:00Z",
  nextAction: "Continue component implementation",
  permissionProfile: "CONTROLLER_REVIEW",
  branch: "feat/frontend-v1-openhands-ui",
  activity: [
    ev("c1", "DISCOVERED", "2026-08-05T01:00:00Z", "Discovered", "Frontend V1 work item approved."),
    ev("c2", "WORKSPACE_READY", "2026-08-05T02:00:00Z", "Workspace ready", "Vite + React 19 scaffold ready."),
    ev("c3", "EXECUTOR_RUNNING", "2026-08-05T03:00:00Z", "Executor running", "Implementing types, schemas, components."),
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
    { id: "e1", category: "Authority", label: "Approval snapshot", value: "APPROVED", status: "pass" },
    { id: "e2", category: "Tests", label: "vitest", value: "RUNNING", status: "pending" },
  ],
  authorityStatus: "APPROVED",
  testStatus: "RUNNING",
  workflowStatus: "PENDING",
};

// ---------------------------------------------------------------------------
// Task 4 — Green Authority and Preflight (READY_FOR_HUMAN)
// ---------------------------------------------------------------------------
const taskGreenAuth: Task = {
  id: "task-green-authority-preflight",
  title: "Green Authority + Preflight reconciliation",
  issueNumber: 118,
  state: "READY_FOR_HUMAN",
  riskTier: "R1",
  updatedAt: "2026-08-04T20:30:00Z",
  nextAction: "Owner review of evidence summary",
  permissionProfile: "OWNER_CONTROL",
  draftPr: {
    number: 118,
    title: "green authority + preflight",
    url: "https://github.com/dddd2024/reverse-agent/pull/118",
    headSha: "abcdef0123456789abcdef0123456789abcdef01",
    baseSha: "0123456789abcdef0123456789abcdef01234567",
    draft: false,
    state: "open",
  },
  branch: "fix/green-authority-preflight",
  activity: [
    ev("d1", "DISCOVERED", "2026-08-04T07:00:00Z", "Discovered", "Reconciliation work item."),
    ev("d2", "EXECUTOR_FINISHED", "2026-08-04T12:00:00Z", "Executor finished", "Reconciled."),
    ev("d3", "LOCAL_VALIDATED", "2026-08-04T12:30:00Z", "Local validated", "All checks green."),
    ev("d4", "WORKFLOWS_OBSERVED", "2026-08-04T13:00:00Z", "Workflows observed", "ci + state-gate SUCCESS."),
    ev("d5", "READY_FOR_HUMAN", "2026-08-04T20:00:00Z", "Ready for human", "Awaiting owner review."),
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
    { id: "e3", category: "Workflows", label: "ci", value: "SUCCESS", status: "pass" },
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
  title: "R1 acceptance — owner review pending",
  issueNumber: 130,
  state: "WAITING_FOR_OWNER",
  riskTier: "R1",
  updatedAt: "2026-08-05T06:10:00Z",
  blocker: "Awaiting owner/maintainer approval label",
  nextAction: "Owner applies r1-approved label",
  permissionProfile: "ASK_FOR_APPROVAL",
  branch: "feat/owner-review-pending",
  activity: [
    ev("f1", "DISCOVERED", "2026-08-05T05:00:00Z", "Discovered", "CANDIDATE work item created from template."),
    ev("f2", "VALIDATED", "2026-08-05T05:30:00Z", "Validated", "Awaiting approval label."),
  ],
  changes: [],
  evidence: [
    { id: "e1", category: "Authority", label: "Approval label", value: "CANDIDATE", status: "pending", detail: "r1-approved not yet applied" },
  ],
  authorityStatus: "CANDIDATE",
  testStatus: "PENDING",
  workflowStatus: "UNKNOWN",
};

// ---------------------------------------------------------------------------
// Task 6 — Expired unattended window (FAILED_TERMINAL)
// ---------------------------------------------------------------------------
const taskExpiredWindow: Task = {
  id: "task-expired-unattended-window",
  title: "R2 unattended window — expired",
  issueNumber: 122,
  state: "FAILED_TERMINAL",
  riskTier: "R2",
  updatedAt: "2026-08-04T03:00:00Z",
  blocker: "autonomousWindow.expiresAt passed (window_expired)",
  nextAction: "Request a new bounded Decision to continue",
  permissionProfile: "OWNER_CONTROL",
  branch: "transition/r2-window-expired",
  activity: [
    ev("g1", "DISCOVERED", "2026-08-03T20:00:00Z", "Discovered", "Window opened until 03:00."),
    ev("g2", "EXECUTOR_RUNNING", "2026-08-03T20:30:00Z", "Executor running", "Working within window."),
    ev("g3", "EXECUTOR_FINISHED", "2026-08-04T03:00:00Z", "Window expired", "Stop condition window_expired triggered.", "STOP: window_expired"),
  ],
  changes: [],
  evidence: [
    { id: "e1", category: "Stop", label: "window_expired", value: "TRIGGERED", status: "fail" },
    { id: "e2", category: "Authority", label: "Window", value: "EXPIRED", status: "fail" },
  ],
  authorityStatus: "EXPIRED",
  testStatus: "PENDING",
  workflowStatus: "UNKNOWN",
};

// ---------------------------------------------------------------------------
// Task 7 — Rework required (REWORK_REQUIRED)
// ---------------------------------------------------------------------------
const taskRework: Task = {
  id: "task-rework-required",
  title: "R1 — independent audit found issue",
  issueNumber: 133,
  state: "REWORK_REQUIRED",
  riskTier: "R1",
  updatedAt: "2026-08-05T05:00:00Z",
  blocker: "Audit rejected head: missing evidence provenance",
  nextAction: "Re-record evidence provenance and re-run local checks",
  permissionProfile: "CONTROLLER_REVIEW",
  draftPr: {
    number: 133,
    title: "rework needed",
    url: "https://github.com/dddd2024/reverse-agent/pull/133",
    headSha: "f00dface0123456789abcdef0123456789abcdef",
    baseSha: "0123456789abcdef0123456789abcdef01234567",
    draft: true,
    state: "open",
  },
  branch: "feat/rework-required",
  activity: [
    ev("h1", "DISCOVERED", "2026-08-04T22:00:00Z", "Discovered", "Implementation drafted."),
    ev("h2", "EXECUTOR_FINISHED", "2026-08-04T23:00:00Z", "Executor finished", "Submitted for audit."),
    ev("h3", "READY_FOR_HUMAN", "2026-08-05T04:00:00Z", "Audit rejected", "Evidence provenance missing.", "AUDIT: REJECT"),
  ],
  changes: [
    { path: "reverse_agent/evidence.py", status: "modified", additions: 4, deletions: 2, diff: authDiff },
  ],
  evidence: [
    { id: "e1", category: "Audit", label: "Exact-head audit", value: "REJECTED", status: "fail", detail: "missing provenance" },
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
  title: "R2 — operation budget exhausted",
  issueNumber: 140,
  state: "FAILED_TERMINAL",
  riskTier: "R2",
  updatedAt: "2026-08-04T16:00:00Z",
  blocker: "max_merges_to_main budget exhausted",
  nextAction: "Request revised Decision with higher budget or stop",
  permissionProfile: "OWNER_CONTROL",
  branch: "transition/r2-budget-exhausted",
  activity: [
    ev("i1", "DISCOVERED", "2026-08-04T08:00:00Z", "Discovered", "Budget of 2 merges set."),
    ev("i2", "EXECUTOR_RUNNING", "2026-08-04T09:00:00Z", "Executor running", "Merging within budget."),
    ev("i3", "EXECUTOR_FINISHED", "2026-08-04T16:00:00Z", "Budget exhausted", "Stop condition budget_exhausted triggered.", "STOP: budget_exhausted"),
  ],
  changes: [],
  evidence: [
    { id: "e1", category: "Budget", label: "max_merges_to_main", value: "2/2", status: "fail" },
    { id: "e2", category: "Stop", label: "budget_exhausted", value: "TRIGGERED", status: "fail" },
  ],
  authorityStatus: "APPROVED",
  testStatus: "PENDING",
  workflowStatus: "UNKNOWN",
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
