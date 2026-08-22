export type GoalStatus =
  | "DRAFT"
  | "PLANNED"
  | "APPROVED"
  | "RUNNING"
  | "COMPLETED"
  | "BLOCKED"
  | "INVALIDATED";

export interface PlatformGoal {
  id: string;
  title: string;
  objective: string;
  repository: string;
  status: GoalStatus;
  revision: number;
  spec_markdown: string;
  plan_markdown: string;
  tasks: Array<{ id: string; title: string; dependencies: string[] }>;
  acceptance_criteria: string[];
  artifact_digest: string;
  executor_kind: "opencode" | "deterministic_fixture";
  orchestration_mode: "single" | "sequential_team";
  binding_ref: string;
  window_id: string;
  created_at: string;
  updated_at: string;
  task_links?: Array<{ task_id: string; plan_task_id: string; status: string; title: string }>;
}

export interface PlatformWindow {
  id: string;
  policy_id: string;
  status: string;
  expires_at: string;
  repositories: string[];
  capabilities: string[];
  max_tasks: number;
  tasks_started: number;
  tasks_completed: number;
  max_token_units: number;
  max_cost_micro_units: number;
  per_task_token_reservation: number;
  per_task_cost_reservation: number;
  provider_quota_state: "NOT_CONFIGURED" | "OBSERVED" | "UNKNOWN";
  enforcement_class: UsageEnforcementClass;
  observed_token_units: number;
  observed_cost_micro_units: number;
  unknown_observation_count: number;
}

export type UsageEnforcementClass =
  | "HARD_ADMISSION_ENFORCED"
  | "POST_RUN_OBSERVED"
  | "USAGE_UNKNOWN";

export interface PlatformUsageRole {
  role: string;
  input_units: number;
  output_units: number;
  reasoning_units: number;
  cache_read_units: number;
  cache_write_units: number;
  cost_micro_units: number;
  observation_count: number;
  unknown_observation_count: number;
  provenance_ids: string[];
}

export interface PlatformUsageSummary {
  status: "OBSERVED" | "USAGE_UNKNOWN";
  input_units: number;
  output_units: number;
  reasoning_units: number;
  cache_read_units: number;
  cache_write_units: number;
  cost_micro_units: number;
  total_token_units: number;
  observation_count: number;
  unknown_observation_count: number;
  provenance_ids: string[];
  per_role: PlatformUsageRole[];
}

export interface PlatformBudgetSummary {
  enforcement_class: UsageEnforcementClass;
  provider_quota_state: "NOT_CONFIGURED" | "OBSERVED" | "UNKNOWN";
  max_token_units: number | null;
  max_cost_micro_units: number | null;
  per_task_token_reservation: number | null;
  per_task_cost_reservation: number | null;
  reserved_token_units: number;
  reserved_cost_micro_units: number;
  observed_token_units: number;
  observed_cost_micro_units: number;
  remaining_token_units: number | null;
  remaining_cost_micro_units: number | null;
  unknown_observation_count: number;
  active_reservation_count: number;
  stop_reason: string;
}

export interface PlatformStatus {
  service: string;
  autonomy: {
    autonomy_enabled: boolean;
    active_window: PlatformWindow | null;
    mode: string;
  };
  coordinator: {
    enabled: boolean;
    executions?: number;
    last_error: string;
    active_window_id: string;
  };
  task_count: number;
  goal_count: number;
  capability_count: number;
  live_model_calls: boolean;
}

export interface StartGoalInput {
  objective: string;
  repository: string;
  executorKind: "opencode" | "deterministic_fixture";
  bindingRef: string;
  autonomyHours: number;
}

export interface PlatformInboxItem {
  id: string;
  title: string;
  objective: string;
  repository: string;
  status: "CAPTURED" | "PROMOTED" | "DISMISSED";
  promoted_goal_id: string;
  created_at: string;
  updated_at: string;
}

export interface PlatformRoadmapPhase {
  id: string;
  title: string;
  position: number;
  description: string;
  derived_status: "PLANNED" | "RUNNING" | "BLOCKED" | "COMPLETED";
  goals: Array<{
    id: string;
    title: string;
    status: string;
    repository: string;
    updated_at: string;
  }>;
  created_at: string;
  updated_at: string;
}

export type PlatformRunStage =
  | "PLAN"
  | "EXECUTE"
  | "VERIFY"
  | "PUBLISH"
  | "UNKNOWN";

export type PlatformRunLiveness =
  | "ACTIVE"
  | "WAITING"
  | "VALIDATING"
  | "BLOCKED"
  | "OWNER_ACTION_REQUIRED"
  | "STALE"
  | "TERMINAL"
  | "UNKNOWN";

export type PlatformRunActivityCategory =
  | "PLAN"
  | "READ"
  | "SEARCH"
  | "EDIT"
  | "COMMAND"
  | "TEST"
  | "VERIFY"
  | "AGENT_STARTED"
  | "AGENT_WAITING"
  | "AGENT_COMPLETED"
  | "CHECKPOINT"
  | "RECOVERY"
  | "BLOCKED"
  | "OWNER_ACTION_REQUIRED"
  | "PUBLICATION"
  | "UNKNOWN";

export interface PlatformRunAgent {
  agent_id: string;
  role: string;
  display_name?: string;
  status?: string;
  attempt?: number;
  last_activity_at?: string;
}

export interface PlatformRunLivenessSummary {
  state: PlatformRunLiveness;
  last_activity_at: string;
  last_activity_source?: string;
  seconds_since_activity?: number | null;
  stale_after_seconds?: number;
  stale_reason?: string;
}

export interface PlatformRunActivityEvent {
  id: string;
  task_id: string;
  timestamp: string;
  category: PlatformRunActivityCategory;
  title: string;
  description: string;
  status?: string;
  stage?: PlatformRunStage;
  agent_id?: string;
  role?: string;
  agent?: PlatformRunAgent | null;
  path?: string;
  command_summary?: string;
  file?: PlatformRunChangedFile | null;
  command?: PlatformRunActivityResult | null;
  test?: PlatformRunActivityResult | null;
  evidence_ref?: string;
}

export interface PlatformRunActivityResult {
  summary: string;
  status: string;
  exit_code?: number | null;
}

export interface PlatformRunCurrentActivity {
  category: PlatformRunActivityCategory;
  title: string;
  description: string;
  agent_id?: string;
  role?: string;
  agent?: PlatformRunAgent | null;
  timestamp?: string;
}

export interface PlatformRunChangeSummary {
  file_count: number;
  additions: number;
  deletions: number;
}

export interface PlatformRunValidation {
  command_id: string;
  status: string;
  exit_code?: number | null;
  summary?: string;
}

export interface PlatformAgentRun {
  task_id: string;
  title: string;
  repository: string;
  status: string;
  state: string;
  executor_kind: string;
  orchestration_mode: string;
  created_at: string;
  updated_at: string;
  failure_classification: string;
  goal_id: string;
  goal_title: string;
  window_id: string;
  stage?: PlatformRunStage;
  liveness?: PlatformRunLiveness | PlatformRunLivenessSummary;
  last_activity_at?: string;
  liveness_detail?: PlatformRunLivenessSummary;
  current_activity?: PlatformRunCurrentActivity | null;
  current_agent?: PlatformRunAgent | null;
  agents?: PlatformRunAgent[];
  change_summary?: PlatformRunChangeSummary | null;
  validation?: PlatformRunValidation | null;
  events?: PlatformRunActivityEvent[];
  activity?: PlatformRunActivityEvent[];
  activity_total?: number;
  event_count?: number;
  events_truncated?: boolean;
  changed_files?: PlatformRunChangedFile[];
  usage: PlatformUsageSummary;
  budget: PlatformBudgetSummary | null;
  publication: {
    status: string;
    branch: string;
    pr_number: number;
    pr_url: string;
    commit_sha: string;
  } | null;
  controls?: PlatformRunControls;
}

export type PlatformRunCancelAvailability = "AVAILABLE" | "UNAVAILABLE" | "ALREADY_APPLIED";
export type PlatformRunCancelReasonCode =
  | "QUEUED_UNCLAIMED"
  | "EXECUTION_HISTORY_PRESENT"
  | "STATUS_NOT_CANCELLABLE"
  | "ALREADY_CANCELLED";

export interface PlatformRunCancelControl {
  action: "CANCEL";
  scope: "QUEUE_ONLY";
  availability: PlatformRunCancelAvailability;
  reason_code: PlatformRunCancelReasonCode;
}

export interface PlatformRunControls {
  cancel: PlatformRunCancelControl;
}

export interface PlatformRunCancelResult {
  status: "APPLIED" | "ALREADY_APPLIED";
}

export interface PlatformRunChangedFile {
  path: string;
  status: string;
  additions: number;
  deletions: number;
}

export interface PlatformAgentRunDetail extends PlatformAgentRun {
  events: PlatformRunActivityEvent[];
  changed_files: PlatformRunChangedFile[];
}

const API_BASE = import.meta.env.VITE_TASK_API_BASE ?? "http://127.0.0.1:8766";

function isMock() {
  if (import.meta.env.MODE === "mock") return true;
  return import.meta.env.MODE === "test" && !import.meta.env.VITE_TASK_CLIENT_USE_HTTP;
}

const now = new Date();
const mockGoal: PlatformGoal = {
  id: "goal-demo-platform",
  title: "完善无人值守多 Agent 平台",
  objective: "把目标拆解为可恢复任务，按策略协调多个 Agent，并交付可审查的结果。",
  repository: "dddd2024/reverse-agent",
  status: "RUNNING",
  revision: 2,
  spec_markdown: "# Specification\n\nBuild a durable multi-agent platform.",
  plan_markdown: "# Plan\n\nAnalyze, implement, verify.",
  tasks: [
    { id: "T001", title: "分析目标与代码库", dependencies: [] },
    { id: "T002", title: "实现协调与恢复链路", dependencies: ["T001"] },
    { id: "T003", title: "验证并准备证据", dependencies: ["T002"] },
  ],
  acceptance_criteria: ["任务可恢复", "策略在服务端执行", "结果可审查"],
  artifact_digest: "b4a91c0e",
  executor_kind: "opencode",
  orchestration_mode: "sequential_team",
  binding_ref: "coding-default",
  window_id: "window-demo",
  created_at: new Date(now.getTime() - 25 * 60_000).toISOString(),
  updated_at: new Date(now.getTime() - 2 * 60_000).toISOString(),
  task_links: [
    { task_id: "task-demo-1", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "分析目标与代码库" },
    { task_id: "task-demo-2", plan_task_id: "T002", status: "RUNNING", title: "实现协调与恢复链路" },
    { task_id: "task-demo-3", plan_task_id: "T003", status: "QUEUED", title: "验证并准备证据" },
  ],
};

let mockGoals = [mockGoal];

export function __setMockGoalStatus(goalId: string, override: Partial<PlatformGoal>) {
  if (goalId === mockGoal.id) {
    Object.assign(mockGoal, { task_links: [...(mockGoal.task_links ?? [])], ...override });
  }
  const target = mockGoals.find((goal) => goal.id === goalId);
  if (target) Object.assign(target, { task_links: [...(target.task_links ?? [])], ...override });
  else if (goalId === mockGoal.id) mockGoals = [mockGoal, ...mockGoals.filter((g) => g.id !== goalId)];
}

const mockWindow: PlatformWindow = {
  id: "window-demo",
  policy_id: "owner-ui-demo",
  status: "ACTIVE",
  expires_at: new Date(now.getTime() + 95 * 60_000).toISOString(),
  repositories: ["dddd2024/reverse-agent"],
  capabilities: ["execute_task", "validate_task", "open_draft_pr"],
  max_tasks: 12,
  tasks_started: 2,
  tasks_completed: 1,
  max_token_units: 240000,
  max_cost_micro_units: 4000000,
  per_task_token_reservation: 80000,
  per_task_cost_reservation: 1200000,
  provider_quota_state: "OBSERVED",
  enforcement_class: "HARD_ADMISSION_ENFORCED",
  observed_token_units: 68420,
  observed_cost_micro_units: 812340,
  unknown_observation_count: 0,
};

let mockInboxItems: PlatformInboxItem[] = [
  {
    id: "inbox-demo-1",
    title: "支持定时触发的无人值守窗口",
    objective: "在自治窗口内按计划自动派发任务并保存检查点。",
    repository: "dddd2024/reverse-agent",
    status: "CAPTURED",
    promoted_goal_id: "",
    created_at: new Date(now.getTime() - 40 * 60_000).toISOString(),
    updated_at: new Date(now.getTime() - 40 * 60_000).toISOString(),
  },
];

const mockRoadmapPhases: PlatformRoadmapPhase[] = [
  {
    id: "phase-demo-1",
    title: "P0 读模型",
    position: 1,
    description: "Inbox、Roadmap、Agent Runs 派生视图",
    derived_status: "RUNNING",
    goals: [
      { id: "goal-demo-platform", title: "完善无人值守多 Agent 平台", status: "RUNNING", repository: "dddd2024/reverse-agent", updated_at: new Date(now.getTime() - 2 * 60_000).toISOString() },
      { id: "goal-demo-budget", title: "预算与成本硬上限", status: "PLANNED", repository: "dddd2024/reverse-agent", updated_at: new Date(now.getTime() - 20 * 60_000).toISOString() },
    ],
    created_at: new Date(now.getTime() - 3 * 3600_000).toISOString(),
    updated_at: new Date(now.getTime() - 2 * 60_000).toISOString(),
  },
  {
    id: "phase-demo-2",
    title: "P1 无人值守",
    position: 2,
    description: "定时触发与停止条件",
    derived_status: "PLANNED",
    goals: [],
    created_at: new Date(now.getTime() - 3 * 3600_000).toISOString(),
    updated_at: new Date(now.getTime() - 3 * 3600_000).toISOString(),
  },
];

const mockHardBudget: PlatformBudgetSummary = {
  enforcement_class: "HARD_ADMISSION_ENFORCED",
  provider_quota_state: "OBSERVED",
  max_token_units: 240000,
  max_cost_micro_units: 4000000,
  per_task_token_reservation: 80000,
  per_task_cost_reservation: 1200000,
  reserved_token_units: 80000,
  reserved_cost_micro_units: 1200000,
  observed_token_units: 68420,
  observed_cost_micro_units: 812340,
  remaining_token_units: 91580,
  remaining_cost_micro_units: 1987660,
  unknown_observation_count: 0,
  active_reservation_count: 1,
  stop_reason: "usage_reservation_overrun",
};

const mockUnknownBudget: PlatformBudgetSummary = {
  ...mockHardBudget,
  enforcement_class: "USAGE_UNKNOWN",
  reserved_token_units: 0,
  reserved_cost_micro_units: 0,
  remaining_token_units: 171580,
  remaining_cost_micro_units: 3187660,
  unknown_observation_count: 1,
  active_reservation_count: 0,
  stop_reason: "usage_unknown",
};

const mockRuns: PlatformAgentRun[] = [
  {
    task_id: "task-demo-1",
    title: "[完善无人值守多 Agent 平台] T001 分析目标与代码库",
    repository: "dddd2024/reverse-agent",
    status: "READY_FOR_REVIEW",
    state: "READY_FOR_HUMAN",
    executor_kind: "opencode",
    orchestration_mode: "sequential_team",
    created_at: new Date(now.getTime() - 30 * 60_000).toISOString(),
    updated_at: new Date(now.getTime() - 5 * 60_000).toISOString(),
    failure_classification: "",
    goal_id: "goal-demo-platform",
    goal_title: "完善无人值守多 Agent 平台",
    window_id: "window-demo",
    stage: "VERIFY",
    liveness: { state: "OWNER_ACTION_REQUIRED", last_activity_at: new Date(now.getTime() - 5 * 60_000).toISOString() },
    last_activity_at: new Date(now.getTime() - 5 * 60_000).toISOString(),
    current_agent: { agent_id: "reviewer", role: "reviewer", display_name: "Reviewer" },
    agents: [
      { agent_id: "planner", role: "planner", display_name: "Planner" },
      { agent_id: "coder", role: "coder", display_name: "Coder" },
      { agent_id: "reviewer", role: "reviewer", display_name: "Reviewer" },
    ],
    current_activity: {
      category: "OWNER_ACTION_REQUIRED",
      title: "等待 Owner 审查",
      description: "验证完成，等待人工审查结果。",
      agent: { agent_id: "reviewer", role: "reviewer", display_name: "Reviewer" },
      timestamp: new Date(now.getTime() - 5 * 60_000).toISOString(),
    },
    change_summary: { file_count: 2, additions: 42, deletions: 11 },
    validation: {
      command_id: "pytest tests/platform_v1 -q",
      status: "SUCCESS",
      exit_code: 0,
      summary: "1785 passed",
    },
    events: [
      {
        id: "activity-demo-1",
        task_id: "task-demo-1",
        timestamp: new Date(now.getTime() - 16 * 60_000).toISOString(),
        category: "AGENT_STARTED",
        title: "Coder 开始执行",
        description: "已从已批准计划开始执行。",
        agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
        stage: "EXECUTE",
      },
      {
        id: "activity-demo-2",
        task_id: "task-demo-1",
        timestamp: new Date(now.getTime() - 10 * 60_000).toISOString(),
        category: "EDIT",
        title: "修改任务实现",
        description: "更新了执行与恢复链路。",
        agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
        stage: "EXECUTE",
        path: "reverse_agent/platform_v1/task_execution.py",
      },
      {
        id: "activity-demo-3",
        task_id: "task-demo-1",
        timestamp: new Date(now.getTime() - 5 * 60_000).toISOString(),
        category: "VERIFY",
        title: "验证通过",
        description: "确定性验证已通过，结果已留给 Owner 审查。",
        agent: { agent_id: "reviewer", role: "reviewer", display_name: "Reviewer" },
        stage: "VERIFY",
        test: { summary: "pytest tests/platform_v1 -q", status: "PASS", exit_code: 0 },
      },
    ],
    changed_files: [
      { path: "reverse_agent/platform_v1/task_execution.py", status: "modified", additions: 24, deletions: 6 },
      { path: "tests/platform_v1/test_task_execution.py", status: "modified", additions: 18, deletions: 5 },
    ],
    usage: {
      status: "OBSERVED",
      input_units: 42000,
      output_units: 5420,
      reasoning_units: 3000,
      cache_read_units: 18000,
      cache_write_units: 0,
      cost_micro_units: 812340,
      total_token_units: 68420,
      observation_count: 3,
      unknown_observation_count: 0,
      provenance_ids: ["usage-planner", "usage-coder", "usage-reviewer"],
      per_role: [
        {
          role: "planner", input_units: 12000, output_units: 1020,
          reasoning_units: 800, cache_read_units: 4000, cache_write_units: 0,
          cost_micro_units: 182340, observation_count: 1,
          unknown_observation_count: 0, provenance_ids: ["usage-planner"],
        },
        {
          role: "coder", input_units: 30000, output_units: 4400,
          reasoning_units: 2200, cache_read_units: 14000, cache_write_units: 0,
          cost_micro_units: 630000, observation_count: 2,
          unknown_observation_count: 0,
          provenance_ids: ["usage-coder", "usage-reviewer"],
        },
      ],
    },
    budget: mockHardBudget,
    publication: {
      status: "COMPLETE",
      branch: "codex/goal-demo-platform",
      pr_number: 97,
      pr_url: "https://github.com/dddd2024/reverse-agent/pull/97",
      commit_sha: "2e6dd422188c3c77928c4496049f763f81048ba7",
    },
    controls: {
      cancel: {
        action: "CANCEL",
        scope: "QUEUE_ONLY",
        availability: "UNAVAILABLE",
        reason_code: "STATUS_NOT_CANCELLABLE",
      },
    },
  },
  {
    task_id: "task-demo-2",
    title: "[完善无人值守多 Agent 平台] T002 实现协调与恢复链路",
    repository: "dddd2024/reverse-agent",
    status: "RUNNING",
    state: "RUNNING",
    executor_kind: "opencode",
    orchestration_mode: "sequential_team",
    created_at: new Date(now.getTime() - 25 * 60_000).toISOString(),
    updated_at: new Date(now.getTime() - 60_000).toISOString(),
    failure_classification: "",
    goal_id: "goal-demo-platform",
    goal_title: "完善无人值守多 Agent 平台",
    window_id: "window-demo",
    stage: "EXECUTE",
    activity_total: 8,
    liveness: { state: "ACTIVE", last_activity_at: new Date(now.getTime() - 60_000).toISOString() },
    last_activity_at: new Date(now.getTime() - 60_000).toISOString(),
    current_agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
    agents: [
      { agent_id: "coder", role: "coder", display_name: "Coder" },
      { agent_id: "test", role: "test", display_name: "Test Agent" },
    ],
    current_activity: {
      category: "COMMAND",
      title: "运行集成测试",
      description: "正在执行确定性测试。",
      agent: { agent_id: "test", role: "test", display_name: "Test Agent" },
      timestamp: new Date(now.getTime() - 60_000).toISOString(),
    },
    change_summary: { file_count: 1, additions: 8, deletions: 2 },
    validation: {
      command_id: "git_diff_check",
      status: "RUNNING",
      summary: "正在运行",
    },
    events: [
      {
        id: "activity-demo-4",
        task_id: "task-demo-2",
        timestamp: new Date(now.getTime() - 4 * 60_000).toISOString(),
        category: "AGENT_STARTED",
        title: "Coder 正在执行",
        description: "执行器已启动。",
        agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
        stage: "EXECUTE",
      },
      {
        id: "activity-demo-5",
        task_id: "task-demo-2",
        timestamp: new Date(now.getTime() - 2 * 60_000).toISOString(),
        category: "COMMAND",
        title: "Test Agent 运行测试",
        description: "正在执行测试命令。",
        agent: { agent_id: "test", role: "test", display_name: "Test Agent" },
        stage: "VERIFY",
        command: {
          summary: "git_diff_check",
          status: "RUNNING",
        },
      },
      {
        id: "activity-demo-6",
        task_id: "task-demo-2",
        timestamp: new Date(now.getTime() - 60_000).toISOString(),
        category: "UNKNOWN",
        title: "新的持久化活动",
        description: "使用通用活动展示。",
        agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
        stage: "EXECUTE",
      },
    ],
    changed_files: [
      { path: "reverse_agent/platform_v1/task_service.py", status: "modified", additions: 8, deletions: 2 },
    ],
    usage: {
      status: "USAGE_UNKNOWN",
      input_units: 0,
      output_units: 0,
      reasoning_units: 0,
      cache_read_units: 0,
      cache_write_units: 0,
      cost_micro_units: 0,
      total_token_units: 0,
      observation_count: 1,
      unknown_observation_count: 1,
      provenance_ids: ["usage-unknown"],
      per_role: [{
        role: "coder", input_units: 0, output_units: 0, reasoning_units: 0,
        cache_read_units: 0, cache_write_units: 0, cost_micro_units: 0,
        observation_count: 1, unknown_observation_count: 1,
        provenance_ids: ["usage-unknown"],
      }],
    },
    budget: mockUnknownBudget,
    publication: null,
    controls: {
      cancel: {
        action: "CANCEL",
        scope: "QUEUE_ONLY",
        availability: "UNAVAILABLE",
        reason_code: "STATUS_NOT_CANCELLABLE",
      },
    },
  },
];

mockRuns.push({
  ...mockRuns[0],
  task_id: "task-demo-queued",
  title: "[完善无人值守多 Agent 平台] T003 等待派发",
  status: "QUEUED",
  state: "QUEUED",
  created_at: new Date(now.getTime() - 2 * 60_000).toISOString(),
  updated_at: new Date(now.getTime() - 60_000).toISOString(),
  stage: "PLAN",
  liveness: "WAITING",
  last_activity_at: undefined,
  current_activity: null,
  current_agent: null,
  agents: [],
  events: [],
  activity: [],
  activity_total: 0,
  changed_files: [],
  change_summary: null,
  validation: null,
  publication: null,
  controls: {
    cancel: {
      action: "CANCEL",
      scope: "QUEUE_ONLY",
      availability: "AVAILABLE",
      reason_code: "QUEUED_UNCLAIMED",
    },
  },
});

export class PlatformClientError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string) {
    super("平台请求未完成");
    this.name = "PlatformClientError";
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { Accept: "application/json", "Content-Type": "application/json", ...init?.headers },
  });
  const text = await response.text();
  const payload = text ? (JSON.parse(text) as T & { error?: string }) : ({} as T & { error?: string });
  if (!response.ok) {
    const code = typeof payload.error === "string" ? payload.error : "platform_request_failed";
    throw new PlatformClientError(response.status, code);
  }
  return payload;
}

export async function fetchPlatformStatus(): Promise<PlatformStatus> {
  if (isMock()) return {
    service: "reverse-agent-platform-v2",
    autonomy: { autonomy_enabled: true, active_window: mockWindow, mode: "owner_activated_bounded_window" },
    coordinator: { enabled: true, executions: 7, last_error: "", active_window_id: mockWindow.id },
    task_count: 18, goal_count: mockGoals.length, capability_count: 6, live_model_calls: false,
  };
  return request<PlatformStatus>("/api/platform/status");
}

export async function fetchGoals(): Promise<PlatformGoal[]> {
  if (isMock()) return mockGoals;
  const result = await request<{ goals: PlatformGoal[] }>("/api/goals");
  return result.goals;
}

export async function fetchGoal(goalId: string): Promise<PlatformGoal> {
  if (isMock()) return mockGoals.find((goal) => goal.id === goalId) ?? mockGoal;
  return request<PlatformGoal>(`/api/goals/${encodeURIComponent(goalId)}`);
}

export async function startGoal(input: StartGoalInput): Promise<PlatformGoal> {
  if (isMock()) {
    const timestamp = new Date().toISOString();
    const goal: PlatformGoal = {
      ...mockGoal,
      id: `goal-${Date.now()}`,
      title: input.objective.slice(0, 48),
      objective: input.objective,
      repository: input.repository,
      status: "RUNNING",
      revision: 1,
      executor_kind: input.executorKind,
      orchestration_mode: input.executorKind === "opencode" ? "sequential_team" : "single",
      binding_ref: input.bindingRef,
      created_at: timestamp,
      updated_at: timestamp,
      task_links: mockGoal.task_links?.map((item, index) => ({
        ...item,
        task_id: `mock-task-${Date.now()}-${index}`,
        status: index === 0 ? "RUNNING" : "QUEUED",
      })),
    };
    mockGoals = [goal, ...mockGoals];
    return goal;
  }

  const idempotencyKey = `ui-goal-${Date.now()}-${crypto.randomUUID()}`;
  const created = await request<PlatformGoal>("/api/goals", {
    method: "POST",
    body: JSON.stringify({
      objective: input.objective,
      repository: input.repository,
      idempotency_key: idempotencyKey,
      executor_kind: input.executorKind,
      orchestration_mode: input.executorKind === "opencode" ? "sequential_team" : "single",
      binding_ref: input.executorKind === "opencode" ? input.bindingRef : "",
    }),
  });
  await request<PlatformGoal>(`/api/goals/${created.id}/plan`, {
    method: "POST", body: JSON.stringify({ expected_revision: created.revision }),
  });
  await request<PlatformGoal>(`/api/goals/${created.id}/approve`, {
    method: "POST", body: JSON.stringify({ expected_revision: created.revision }),
  });
  const status = await fetchPlatformStatus();
  let window = status.autonomy.active_window;
  if (!window || !window.repositories.includes(input.repository)) {
    const starts = new Date();
    const expires = new Date(starts.getTime() + input.autonomyHours * 60 * 60 * 1000);
    window = await request<PlatformWindow>("/api/windows/activate", {
      method: "POST",
      body: JSON.stringify({
        policy_id: `owner-ui-${Date.now()}`,
        policy_revision: 1,
        owner_identity: "local-owner",
        starts_at: starts.toISOString(),
        expires_at: expires.toISOString(),
        repositories: [input.repository],
        capabilities: ["execute_task", "resume_task", "reconcile_task", "validate_task", "open_draft_pr"],
        max_concurrent_tasks: 2,
        max_tasks: 20,
        max_retries: 1,
        confirmation: "ACTIVATE",
      }),
    });
  }
  await request<PlatformGoal>(`/api/goals/${created.id}/launch`, {
    method: "POST", body: JSON.stringify({ expected_revision: created.revision, window_id: window.id }),
  });
  return fetchGoal(created.id);
}

export async function fetchInbox(): Promise<PlatformInboxItem[]> {
  if (isMock()) return mockInboxItems;
  const result = await request<{ items: PlatformInboxItem[] }>("/api/inbox");
  return result.items;
}

export async function captureInboxItem(input: { title?: string; objective: string; repository?: string }): Promise<PlatformInboxItem> {
  if (isMock()) {
    const timestamp = new Date().toISOString();
    const item: PlatformInboxItem = {
      id: `inbox-${Date.now()}`,
      title: (input.title || input.objective).slice(0, 77),
      objective: input.objective,
      repository: input.repository || "dddd2024/reverse-agent",
      status: "CAPTURED",
      promoted_goal_id: "",
      created_at: timestamp,
      updated_at: timestamp,
    };
    mockInboxItems = [item, ...mockInboxItems];
    return item;
  }
  return request<PlatformInboxItem>("/api/inbox", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function promoteInboxItem(itemId: string): Promise<{ item: PlatformInboxItem; goal: PlatformGoal }> {
  if (isMock()) {
    const item = mockInboxItems.find((entry) => entry.id === itemId);
    if (!item) throw new Error("inbox item not found");
    if (item.status === "PROMOTED" && item.promoted_goal_id) {
      const goal = mockGoals.find((entry) => entry.id === item.promoted_goal_id) ?? mockGoal;
      return { item, goal };
    }
    if (item.status !== "CAPTURED") throw new Error("inbox item not promotable");
    const timestamp = new Date().toISOString();
    const goal: PlatformGoal = {
      ...mockGoal,
      id: `goal-inbox-${Date.now()}`,
      title: item.title,
      objective: item.objective,
      repository: item.repository,
      status: "DRAFT",
      revision: 1,
      task_links: [],
      created_at: timestamp,
      updated_at: timestamp,
    };
    mockGoals = [goal, ...mockGoals];
    item.status = "PROMOTED";
    item.promoted_goal_id = goal.id;
    item.updated_at = timestamp;
    return { item, goal };
  }
  return request<{ item: PlatformInboxItem; goal: PlatformGoal }>(
    `/api/inbox/${encodeURIComponent(itemId)}/promote`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export async function dismissInboxItem(itemId: string): Promise<PlatformInboxItem> {
  if (isMock()) {
    const item = mockInboxItems.find((entry) => entry.id === itemId);
    if (!item) throw new Error("inbox item not found");
    if (item.status !== "CAPTURED") throw new Error("inbox item not dismissable");
    item.status = "DISMISSED";
    item.updated_at = new Date().toISOString();
    return item;
  }
  return request<PlatformInboxItem>(`/api/inbox/${encodeURIComponent(itemId)}/dismiss`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function fetchRoadmap(): Promise<PlatformRoadmapPhase[]> {
  if (isMock()) return mockRoadmapPhases;
  const result = await request<{ phases: PlatformRoadmapPhase[] }>("/api/roadmap");
  return result.phases;
}

export async function fetchRuns(): Promise<PlatformAgentRun[]> {
  if (isMock()) return mockRuns.map((run) => ({ ...run }));
  const result = await request<{ runs: PlatformAgentRun[] }>("/api/runs");
  return result.runs;
}

export async function fetchRun(taskId: string): Promise<PlatformAgentRunDetail> {
  if (isMock()) {
    const run = mockRuns.find((entry) => entry.task_id === taskId) ?? mockRuns[0];
    return {
      ...run,
      events: run.events ?? [],
      changed_files: run.changed_files ?? [],
    };
  }
  return request<PlatformAgentRunDetail>(`/api/runs/${encodeURIComponent(taskId)}`);
}

export async function cancelRun(taskId: string): Promise<PlatformRunCancelResult> {
  if (isMock()) {
    const run = mockRuns.find((entry) => entry.task_id === taskId);
    if (!run) throw new PlatformClientError(404, "run_not_found");
    const cancel = run.controls?.cancel;
    if (cancel?.availability === "ALREADY_APPLIED") return { status: "ALREADY_APPLIED" };
    if (cancel?.availability !== "AVAILABLE") {
      throw new PlatformClientError(409, "queue_cancel_unavailable");
    }
    run.status = "CANCELLED";
    run.state = "CANCELLED";
    run.updated_at = new Date().toISOString();
    run.liveness = "TERMINAL";
    run.controls = {
      cancel: {
        action: "CANCEL",
        scope: "QUEUE_ONLY",
        availability: "ALREADY_APPLIED",
        reason_code: "ALREADY_CANCELLED",
      },
    };
    const event: PlatformRunActivityEvent = {
      id: `${taskId}-queue-cancelled`,
      task_id: taskId,
      timestamp: run.updated_at,
      category: "CHECKPOINT",
      title: "排队任务已取消",
      description: "尚未获取执行权的排队任务已取消。",
      status: "COMPLETED",
      stage: "PLAN",
    };
    run.events = [event];
    run.activity = [event];
    run.activity_total = 1;
    return { status: "APPLIED" };
  }
  return request<PlatformRunCancelResult>(`/api/runs/${encodeURIComponent(taskId)}/cancel`, {
    method: "POST",
    body: "{}",
  });
}
