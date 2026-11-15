export interface StartErrorExplanation {
  readonly code: string;
  readonly params: readonly string[];
  readonly zh: string;
  readonly advice: string;
  readonly known: boolean;
}

interface Entry {
  readonly zh: string;
  readonly advice: string;
}

const ENTRIES: Record<string, Entry> = {
  owner_selection_confirmation_unavailable: {
    zh: "当前浏览器无法打开终端确认窗口。",
    advice: "请在已连接终端的环境中操作，或刷新页面后重试。",
  },
  owner_window_preflight_unavailable: {
    zh: "启动前预检暂不可用。",
    advice: "请稍后重试；若持续出现，请检查服务端日志。",
  },

  owner_window_old_active_claims_hold: {
    zh: "已有未完成的旧窗口声明占用资源。",
    advice: "请先完成或结束旧窗口，再创建新窗口。",
  },
  owner_window_requires_one_repository: {
    zh: "自治窗口必须绑定且仅绑定一个仓库。",
    advice: "在目标设定中指定唯一仓库后重试。",
  },
  owner_window_goal_not_admissible: {
    zh: "目标不在当前窗口的可接受范围内。",
    advice: "请检查目标所属仓库与窗口设定是否一致。",
  },
  owner_window_capability_missing: {
    zh: "目标所需的执行能力在当前窗口中不可用。",
    advice: "请在窗口配置中启用所需能力，或更换执行绑定。",
  },
  owner_window_max_tasks_below_planned_tasks: {
    zh: "窗口最大任务数低于目标计划的任务数。",
    advice: "请提高窗口任务上限，或拆分目标为多个窗口。",
  },
  owner_window_repository_changed: {
    zh: "窗口绑定的仓库已变更。",
    advice: "请重新确认窗口仓库与目标是否仍匹配。",
  },
  owner_window_pinned_binding_outside_pool: {
    zh: "窗口固定的执行绑定不在当前可用池中。",
    advice: "请检查账户绑定是否仍有效，或重新选择绑定。",
  },
  owner_window_scope_too_large: {
    zh: "窗口范围过大，无法一次性覆盖。",
    advice: "请缩小目标范围，拆分为多个窗口逐步执行。",
  },
  owner_window_task_unroutable: {
    zh: "窗口无法将任务路由到可用的执行器。",
    advice: "请检查执行绑定是否在线、能力是否匹配。",
  },
  owner_window_goals_invalid: {
    zh: "窗口目标列表无效。",
    advice: "请重新选择目标后重试。",
  },
  owner_window_duration_invalid: {
    zh: "窗口时长设定无效。",
    advice: "请设定合理的窗口时长（不超过策略上限）。",
  },
  owner_window_limits_invalid: {
    zh: "窗口资源限制无效。",
    advice: "请检查并修正 Token、成本或任务数上限。",
  },
  owner_window_budget_invalid: {
    zh: "窗口预算设定无效。",
    advice: "请调整预算至策略允许范围内。",
  },
  owner_window_capabilities_invalid: {
    zh: "窗口能力列表无效。",
    advice: "请重新勾选需要的执行能力。",
  },
  owner_window_settings_invalid: {
    zh: "窗口配置无效。",
    advice: "请检查窗口参数是否完整且合法。",
  },
  owner_window_card_digest_invalid: {
    zh: "激活卡片摘要校验失败。",
    advice: "请重新生成或确认激活卡片。",
  },
  owner_window_scope_changed: {
    zh: "窗口范围在激活过程中已发生变化。",
    advice: "请重新执行预检并确认最新范围。",
  },
  owner_window_preset_invalid: {
    zh: "窗口预设不存在或已失效。",
    advice: "请选择其他预设，或手动配置窗口参数。",
  },
  owner_window_request_invalid: {
    zh: "窗口请求无效。",
    advice: "请刷新页面后重新发起窗口创建。",
  },
  owner_window_supervisor_activation_disabled: {
    zh: "当前环境已禁用监督激活模式。",
    advice: "请使用其他激活方式，或联系管理员开启。",
  },
  owner_window_terminal_confirmation_required: {
    zh: "需要在终端完成激活确认。",
    advice: "请切换到终端环境执行确认，或改用其他激活模式。",
  },
  owner_window_surface_invalid: {
    zh: "激活媒介（浏览器/终端）无效或不匹配。",
    advice: "请在正确的激活媒介中重新发起。",
  },
  owner_window_admission_in_progress: {
    zh: "窗口正在处理准入流程，请稍候。",
    advice: "等待准入完成后自动继续；若长时间无响应请刷新。",
  },
  owner_window_confirmation_refused: {
    zh: "激活确认已被拒绝。",
    advice: "请确认风险后重新发起窗口创建。",
  },
  owner_window_confirmation_expired: {
    zh: "激活确认已过期。",
    advice: "请重新发起窗口创建并及时完成确认。",
  },
  owner_window_missing: {
    zh: "窗口记录不存在。",
    advice: "请确认窗口 ID 是否正确，或重新创建窗口。",
  },
  owner_window_receipt_missing: {
    zh: "窗口缺少有效的激活收据。",
    advice: "请重新完成激活流程以获取收据。",
  },
  owner_window_task_unbound: {
    zh: "目标中的任务未绑定到任何执行实例。",
    advice: "请检查任务状态并重新触发绑定。",
  },

  quick_start_text_invalid: {
    zh: "一句话启动的文本无效。",
    advice: "请用简短的 Issue 引用或任务描述重试。",
  },
  quick_start_repository_invalid: {
    zh: "指定的仓库无效或不可访问。",
    advice: "请确认仓库名拼写正确且你有权限访问。",
  },
  quick_start_preset_invalid: {
    zh: "启动预设不存在或已失效。",
    advice: "请选择其他预设，或手动配置。",
  },
  quick_start_issue_outside_repository: {
    zh: "引用的 Issue 不在指定仓库中。",
    advice: "请确认 Issue 所属仓库，或更换目标仓库。",
  },
  quick_start_too_many_issues: {
    zh: "单次启动引用了过多 Issue。",
    advice: "请将 Issue 拆分到多个启动批次中。",
  },
  quick_start_issue_unreadable: {
    zh: "无法读取指定 Issue 的内容。",
    advice: "请确认 Issue 编号正确且你有读取权限。",
  },
  quick_start_issue_not_open: {
    zh: "指定 Issue 已关闭或不存在。",
    advice: "请重新打开该 Issue 或选择其他仍在进行的 Issue。",
  },
  quick_start_presets_invalid: {
    zh: "窗口预设列表无效。",
    advice: "请刷新页面后重试，或手动配置窗口参数。",
  },
  quick_start_too_many_attempts: {
    zh: "连续启动尝试次数过多，已暂时限制。",
    advice: "请稍后再试，或检查是否存在循环重试的问题。",
  },

  native_owner_identity_unavailable: {
    zh: "当前原生执行器身份不可用。",
    advice: "请确认执行器已正确安装并完成身份初始化。",
  },
  native_owner_identity_unavailable_or_changed: {
    zh: "原生执行器身份不可用或已变更。",
    advice: "请重新完成身份确认，或使用非原生激活方式。",
  },
  native_owner_impersonation: {
    zh: "检测到身份伪装，激活已中止。",
    advice: "请使用正确的所有者身份重新激活。",
  },
  native_admission_old_active_claims_hold: {
    zh: "已有旧的原生准入声明在进行中。",
    advice: "请等待旧声明完成或清理后再试。",
  },
  native_admission_goal_changed: {
    zh: "目标内容在原生准入过程中已变更。",
    advice: "请刷新并确认最新目标状态后重试。",
  },
  native_admission_requires_planned_single_codex_goal: {
    zh: "原生准入仅支持已规划的单一 Codex 目标。",
    advice: "请将目标规划后再进行原生准入。",
  },
  native_admission_goal_already_materialized: {
    zh: "目标已进入实体执行阶段，无法再走原生准入。",
    advice: "请使用窗口激活方式继续。",
  },
  native_admission_requires_pinned_native_codex_binding: {
    zh: "原生准入需要固定的原生 Codex 执行绑定。",
    advice: "请在账户设置中绑定原生 Codex，或切换到其他执行器。",
  },
  native_admission_repository_changed: {
    zh: "原生准入期间目标仓库已变更。",
    advice: "请重新选择目标仓库后重试。",
  },
  native_admission_task_changed: {
    zh: "原生准入期间任务内容已变更。",
    advice: "请刷新任务状态后重新准入。",
  },
  native_admission_in_progress: {
    zh: "原生准入正在进行中，请稍候。",
    advice: "等待准入完成；若长时间无响应请刷新页面。",
  },
  native_owner_scope_changed: {
    zh: "原生执行范围在激活过程中已变更。",
    advice: "请重新确认范围并重新激活。",
  },
  native_owner_consent_refused: {
    zh: "原生所有者同意已被拒绝。",
    advice: "请重新确认同意并再次激活。",
  },
  native_owner_consent_consumed: {
    zh: "原生所有者同意已被使用过。",
    advice: "请重新发起同意流程。",
  },
  native_owner_consent_expired: {
    zh: "原生所有者同意已过期。",
    advice: "请重新完成同意流程后重试。",
  },
  native_admission_receipt_missing: {
    zh: "原生准入缺少收据记录。",
    advice: "请重新完成准入流程以生成收据。",
  },
  native_admission_window_missing: {
    zh: "原生准入对应的窗口不存在。",
    advice: "请确认窗口已创建，或重新发起窗口创建。",
  },

  active_window_repository_conflict: {
    zh: "当前已激活的自治窗口属于其他仓库。",
    advice: "请先完成或结束现有窗口，再启动新仓库的目标。",
  },
  active_window_policy_conflict: {
    zh: "当前自治窗口与请求的策略不兼容。",
    advice: "请检查窗口策略是否允许当前操作。",
  },
  active_window_exists: {
    zh: "已存在活跃的自治窗口，无法同时启动新窗口。",
    advice: "请先结束现有窗口或等待其完成。",
  },
  active_window_not_available: {
    zh: "当前无可激活的自治窗口。",
    advice: "请先创建窗口，或检查窗口状态。",
  },
  delegated_policy_authority_unavailable: {
    zh: "委托策略的授权当前不可用。",
    advice: "请确认策略授权状态，或稍后重试。",
  },
  trusted_policy_unavailable: {
    zh: "受信任的策略当前不可用。",
    advice: "请检查账户策略配置，或稍后重试。",
  },
  delegated_policy_template_invalid: {
    zh: "委托策略模板无效。",
    advice: "请检查策略模板是否完整且已保存。",
  },

  invalid_autonomy_policy_identity: {
    zh: "自治策略身份无效。",
    advice: "请确认策略身份是否已正确配置。",
  },
  repository_workspace_unconfigured: {
    zh: "该仓库尚未配置工作区。",
    advice: "请先在仓库设置中完成工作区初始化。",
  },
};

function splitCode(raw: string): { base: string; params: string[] } {
  if (!raw) return { base: "", params: [] };
  const [base, ...rest] = raw.split(":");
  return { base, params: rest };
}

export function explainStartError(rawCode: string): StartErrorExplanation {
  const { base, params } = splitCode(rawCode);
  const entry = ENTRIES[base];
  if (entry) {
    const zh = params.length
      ? `${entry.zh}（${params.join(" · ")}）`
      : entry.zh;
    return { code: base, params, zh, advice: entry.advice, known: true };
  }
  return {
    code: base,
    params,
    zh: rawCode,
    advice: "请将此错误码反馈给管理员或查阅文档。",
    known: false,
  };
}
