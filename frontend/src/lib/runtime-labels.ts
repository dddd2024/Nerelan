export interface RuntimeMessage {
  label: string;
  nextStep: string;
}

// Status values: control_store.GOAL_STATES, run_store.TASK_STATUS_ORDER and
// run_read_model.BACKEND_STATUS_TO_FRONTEND_STATE.
const STATUSES: Record<string, [string, string]> = {
  DRAFT: ["草稿", "请完善目标并提交计划。"],
  PLANNED: ["等待启动", "请检查计划并批准执行。"],
  APPROVED: ["等待启动", "请在有效的授权窗口内启动目标。"],
  RUNNING: ["正在执行", "可查看执行记录，等待本次执行结束。"],
  COMPLETED: ["执行完成，待审查", "请查看验证证据并等待独立审查。"],
  BLOCKED: ["需要处理阻塞", "请查看阻塞原因，处理后再继续。"],
  INVALIDATED: ["已失效", "请核对目标和授权后重新制定计划。"],
  QUEUED: ["排队中", "请等待调度，或查看可用模型和授权窗口。"],
  PREPARING_WORKSPACE: ["正在准备工作区", "请等待工作区准备完成。"],
  RUNNING_FIXTURE: ["正在执行样例", "可查看样例记录；实际任务仍需真实执行和验证。"],
  VALIDATING: ["验证中", "请等待检查结果并查看验证证据。"],
  READY_FOR_REVIEW: ["等待审查", "请查看改动和验证证据并安排独立审查。"],
  READY_FOR_REVIEW_FIXTURE: ["样例执行完成", "请使用真实执行器运行任务并验证结果。"],
  INTERRUPTED: ["执行已中断", "请查看执行记录并确认是否可以恢复。"],
  QUOTA_WAIT: ["等待额度恢复", "请检查账户额度，恢复后再继续。"],
  FAILED: ["执行失败", "请查看失败原因，处理后再重试。"],
  CANCELLED: ["已取消", "如需继续，请确认范围后重新创建任务。"],
  READY_FOR_HUMAN: ["等待人工审查", "请查看改动和验证证据并安排独立审查。"],
  BLOCKED_EXTERNAL: ["外部阻塞", "请检查外部服务和阻塞原因后再继续。"],
  REWORK_REQUIRED: ["需要返工", "请根据验证或审查意见修改后重新检查。"],
  FAILED_TERMINAL: ["终态失败", "请查看失败记录，确认修复方案后再创建执行。"],
  WAITING_FOR_OWNER: ["等待 Owner", "请查看待处理事项并由负责人确认下一步。"],
  // Structured activity/validation statuses from run_read_model._status_for_event.
  ACTIVE: ["活动中", "可查看最新活动记录。"],
  WAITING: ["等待中", "请查看等待原因并确认前置条件。"],
  PASS: ["检查通过", "可查看检查证据并继续后续审查。"],
  FAIL: ["检查未通过", "请查看检查结果并修复问题后重新验证。"],
  UNKNOWN: ["状态未知", "请查看执行记录并核对实际状态。"],
};

// Failure classifications from executor/protocol, routing, review and execution
// modules; window stop reasons from control_store. Dynamic detail stays in title.
const FAILURES: Record<string, [string, string]> = {
  review_not_independent: ["审查缺少独立性", "请配置与实施者独立的审查者后再试。"],
  usage_budget_reached: ["已达到用量预算", "请核对用量并由负责人调整预算后再继续。"],
  usage_reservation_overrun: ["实际用量超出预留", "请核对本次用量并调整后续预留或预算。"],
  usage_unknown_budget_reached: ["未知用量已达预算上限", "请补齐用量证据并核对预算后再继续。"],
  usage_unknown: ["用量未知", "请检查用量记录，确认消耗后再继续派发。"],
  receipt_persistence_failed: ["执行凭据保存失败", "请检查本地存储并核对已有执行记录后再继续。"],
  window_expired: ["授权窗口已到期", "请由负责人启用新的授权窗口后再继续。"],
  renew_until_reached: ["自动续期已到期限", "请由负责人重新确认授权窗口。"],
  owner_stopped: ["负责人已停止窗口", "如需继续，请由负责人重新确认授权。"],
  owner_revoked: ["负责人已撤销授权", "请由负责人重新确认授权后再继续。"],
  executor_dispatch_failed: ["执行器派发失败", "请检查执行器配置和执行记录后重试。"],
  MODEL_UNAVAILABLE: ["模型不可用", "请检查模型权限或选择其他可用模型。"],
  MODEL_REFUSED: ["模型拒绝执行", "请检查任务范围和拒绝原因，必要时调整任务。"],
  policy_refusal: ["模型因策略拒绝执行", "请核对任务范围与拒绝原因后调整请求。"],
  api_error_429: ["请求受到限流", "请稍后重试并检查服务方的请求限制。"],
  quota_exhausted: ["账户额度已耗尽", "请检查账户额度，恢复后再继续。"],
  quota_paused: ["已因额度暂停", "请检查额度检查点并确认恢复条件。"],
  quota_checkpoint_failed: ["额度检查点失败", "请核对额度和执行记录后再恢复。"],
  provider_quota_limit: ["服务方容量受限", "请稍后重试或选择其他可用服务。"],
  provider_overloaded: ["服务方繁忙", "请稍后重试或选择其他可用服务。"],
  timeout: ["执行超时", "请查看执行记录，确认已有结果后再决定是否重试。"],
  executor_nonzero: ["执行器异常退出", "请查看执行记录中的退出原因并处理后重试。"],
  malformed_executor_output: ["执行器输出格式无效", "请检查执行记录和执行器配置后重试。"],
  deterministic_validation_failure: ["确定性检查未通过", "请查看检查结果并修复问题后重新验证。"],
  patch_hygiene_failed: ["补丁格式检查未通过", "请修复补丁格式问题后重新检查。"],
  no_runnable_model: ["没有可运行的模型", "请检查模型配置、额度和任务所需能力。"],
  no_willing_model: ["没有模型愿意执行", "请查看拒绝原因并调整任务范围。"],
  pinned_model_unavailable: ["指定模型不可用", "请检查指定模型的权限、额度和配置。"],
  cli_unavailable: ["执行工具不可用", "请检查本地执行工具是否已安装并可用。"],
  auth_provider_route_failure: ["认证或服务路由失败", "请检查连接的登录状态和服务地址。"],
  network_provider_failure: ["服务连接失败", "请检查网络和服务连接后重试。"],
  model_provider_unavailable: ["模型服务不可用", "请检查服务配置或选择其他可用模型。"],
  cleanup_unconfirmed: ["无法确认执行器已退出", "请核对本地进程和执行记录，确认结束后再重试。"],
  executor_error: ["执行器出错", "请查看执行记录并检查本地执行环境。"],
  coordinator_execution_error: ["调度执行出错", "请查看调度记录并核对任务的实际执行状态。"],
  binding_resolution_failed: ["连接配置无法解析", "请检查任务绑定的连接和模型配置。"],
  invalid_plan_handoff: ["计划交接无效", "请查看规划结果并重新生成有效的计划。"],
  missing_plan_handoff: ["缺少计划交接", "请检查规划记录并补齐计划结果。"],
  invalid_review_handoff: ["审查交接无效", "请检查审查记录并补齐有效的审查结果。"],
  planner_product_mutation: ["规划者修改了产品文件", "请核对越界改动并恢复正确的规划范围。"],
  reviewer_product_mutation: ["审查者修改了产品文件", "请核对越界改动并重新安排只读独立审查。"],
  no_coder_product_diff: ["实施者未产生改动", "请检查任务要求和执行记录后再安排实施。"],
  ambiguous_external_operation: ["外部操作结果不确定", "请核对外部实际状态，确认后再继续。"],
  head_moved: ["代码版本已变化", "请核对最新版本并重新验证和审查。"],
  coder_snapshot_missing: ["缺少实施快照", "请检查实施证据并补齐快照后再继续。"],
  coder_snapshot_mismatch: ["实施快照不一致", "请核对改动和快照后重新验证。"],
  resume_context_invalid: ["恢复上下文无效", "请核对恢复记录和任务状态后再继续。"],
  orphaned_preparation: ["工作区准备被中断", "请检查工作区和执行记录后再恢复。"],
  policy_worktree_violation: ["工作区不符合授权范围", "请检查工作区路径与任务授权范围。"],
  stream_budget_exhausted_before_dispatch: ["派发前预算已耗尽", "请核对预算后再派发任务。"],
  stream_budget_usage_unknown_before_dispatch: ["派发前用量未知", "请补齐用量记录并核对预算后再派发。"],
  stream_budget_abort_confirmed: ["已因流式预算停止", "请核对执行结果和用量后调整预算。"],
  stream_budget_abort_unknown: ["预算停止结果不确定", "请先核对进程状态和用量，确认后再继续。"],
  server_session_error: ["执行会话出错", "请检查会话记录和服务连接后再继续。"],
  server_transport_failed: ["执行会话连接失败", "请检查本地执行服务及连接状态。"],
  server_transport_internal_failure: ["执行会话传输出错", "请查看执行记录并检查本地执行服务。"],
  model_review_rejected: ["独立审查未通过", "请按审查意见修改后重新验证和审查。"],
  model_review_invalid_output: ["审查结果格式无效", "请检查审查记录并重新生成有效的审查结果。"],
  model_review_connection_unsupported: ["连接不支持审查", "请选择支持独立审查的连接。"],
  model_review_sandbox_unsupported: ["审查沙箱不受支持", "请配置支持只读审查的执行环境。"],
  model_review_evidence_required: ["缺少审查证据", "请补齐当前版本的独立审查证据。"],
  model_review_evidence_invalid: ["审查证据无效", "请核对当前版本并重新进行独立审查。"],
  model_review_workspace_unavailable: ["审查工作区不可用", "请检查保留的工作区后重新安排审查。"],
  model_review_workspace_unverifiable: ["审查工作区无法核验", "请核对工作区来源和版本后重新安排审查。"],
  model_review_diff_unavailable: ["审查改动不可用", "请检查保留的改动证据后重新安排审查。"],
  model_review_input_mutation: ["审查输入被修改", "请核对冻结的审查输入并重新安排审查。"],
  model_review_input_changed: ["审查输入已变化", "请基于当前版本重新生成审查输入。"],
  model_review_artifact_input_required: ["缺少审查产物输入", "请补齐实施产物后再安排审查。"],
  model_review_terminal_task_requires_new_execution: ["审查需要新的执行", "请为已结束的审查任务创建新执行。"],
  model_review_runtime_inside_product: ["审查运行目录不符合要求", "请将审查运行目录配置在产品目录之外。"],
  model_review_checkpoint_invalid: ["审查检查点无效", "请核对审查记录并补齐有效检查点。"],
  validation_failed: ["验证失败", "请查看验证记录并修复问题后重试。"],
  execution_failed: ["执行失败", "请查看执行记录并处理失败原因后重试。"],
  failed: ["执行失败", "请查看执行记录并处理失败原因后重试。"],
  blocked: ["执行受阻", "请查看阻塞原因并处理后继续。"],
  unapproved: ["尚未获得批准", "请由负责人核对任务范围并批准后再继续。"],
  role_failed: ["角色执行失败", "请查看对应角色的执行记录后再安排执行。"],
  opencode_nonzero: ["执行器异常退出", "请查看执行记录中的退出原因并处理后重试。"],
};

// Both native executors use codex_executor._e for these classifications.
for (const executor of ["codex", "claude_code"]) {
  for (const [suffix, message] of Object.entries({
    timeout: FAILURES.timeout,
    usage_limit: FAILURES.quota_exhausted,
    turn_failed: FAILURES.executor_error,
    process_failed: FAILURES.executor_nonzero,
    process_start_failed: ["执行器启动失败", "请检查本地执行环境后重试。"],
    tool_launch_failed: ["执行工具启动失败", "请检查本地工具和沙箱环境后重试。"],
    no_product_changes: ["没有产生预期的文件修改", "请检查任务要求和执行记录后再安排实施。"],
    stream_read_failed: FAILURES.network_provider_failure,
    stdin_write_failed: FAILURES.executor_error,
    stderr_limit_exceeded: ["执行器错误输出过多", "请查看执行记录中的首个错误并修复。"],
  } satisfies Record<string, [string, string]>)) {
    FAILURES[`${executor}_${suffix}`] = message;
  }
}

export function runtimeMessage(code: string): RuntimeMessage {
  const lookup = (key: string) => Object.hasOwn(STATUSES, key) ? STATUSES[key]
    : Object.hasOwn(FAILURES, key) ? FAILURES[key] : undefined;
  const entry = lookup(code) ?? lookup(code.split(":", 1)[0]);
  return entry ? { label: entry[0], nextStep: entry[1] } : { label: code, nextStep: "" };
}

export function runtimeExplanation(code: string): string {
  const { label, nextStep } = runtimeMessage(code);
  return nextStep ? `${label}：${nextStep}` : code;
}

export function runtimeTitle(code: string): string {
  const { nextStep } = runtimeMessage(code);
  return nextStep ? `${code}\n${nextStep}` : code;
}
