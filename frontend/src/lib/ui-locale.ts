/**
 * One locale switch for product-owned task copy (#1200).
 *
 * Only fixed strings the product writes live here. Agent prose, tool logs,
 * error codes and identifiers are rendered verbatim by their callers and are
 * never translated, so no model quota is spent on boilerplate.
 *
 * The active locale is an explicit stored preference when present, otherwise
 * the document language (`index.html` ships `zh-CN`). Unknown values fall
 * back to Chinese, the product's default.
 */
export const UI_LOCALE_STORAGE_KEY = "nerelan.locale";

export const UI_LOCALES = ["zh-CN", "en"] as const;
export type UiLocale = (typeof UI_LOCALES)[number];

function normalizeLocale(value: string | null | undefined): UiLocale | undefined {
  const tag = value?.trim().toLowerCase();
  if (!tag) return undefined;
  if (tag === "en" || tag.startsWith("en-")) return "en";
  if (tag === "zh" || tag.startsWith("zh-")) return "zh-CN";
  return undefined;
}

export function uiLocale(): UiLocale {
  let stored: string | null = null;
  try {
    stored = globalThis.localStorage?.getItem(UI_LOCALE_STORAGE_KEY) ?? null;
  } catch {
    stored = null;
  }
  return normalizeLocale(stored)
    ?? normalizeLocale(globalThis.document?.documentElement?.lang)
    ?? "zh-CN";
}

export interface TaskCopy {
  tasksTitle: string;
  noNextAction: string;
  noBlocker: string;
  investigateFailure: string;
  plannerTimeout: string;
  noProductChanges: string;
  reviewNotice: string;
  askBeforeActing: string;
  functional: {
    sectionLabel: string;
    verifiedTitle: string;
    verifiedBody: string;
    missingTitle: string;
    missingBody: string;
    failedTitle: string;
    failedBody: string;
    fixtureTitle: string;
    fixtureBody: string;
    nextLabel: string;
    nextChooseChecks: string;
    nextWait: string;
    nextFixFailure: string;
    detailsSummary: string;
    proofPolicy: string;
    inputFrom: (task: string) => string;
    exitCode: (code: string) => string;
    timedOut: string;
    unknown: string;
    reportCounts: (tests: number, passed: number, failed: number, skipped: number) => string;
    reportMissing: string;
    fields: {
      baseCommit: string; head: string; tree: string; contract: string; result: string; runId: string;
      lease: string; reason: string; inputTask: string; inputExecution: string; inputCommit: string;
      inputTree: string; inputResult: string; inputBinding: string;
    };
  };
}

const ZH: TaskCopy = {
  tasksTitle: "任务",
  noNextAction: "暂无下一步操作",
  noBlocker: "无",
  investigateFailure: "查看任务失败原因和执行记录",
  plannerTimeout: "Agent 在规划阶段超时；可以查看执行记录和阻塞原因",
  noProductChanges: "任务没有产生预期的文件修改",
  reviewNotice: "任务已进入待审查状态；可以查看变更和验证结果。",
  askBeforeActing: "操作前询问",
  functional: {
    sectionLabel: "功能验证",
    verifiedTitle: "功能已验证",
    verifiedBody: "测试结果已绑定到本次任务的代码修改。",
    missingTitle: "尚未完成测试",
    missingBody: "尚无足够的功能测试结果证明修改有效。",
    failedTitle: "测试未通过",
    failedBody: "功能测试没有通过，修改尚不能视为有效。",
    fixtureTitle: "仅测试夹具通过",
    fixtureBody: "这是演示用的测试夹具结果，不代表真实修改已验证。",
    nextLabel: "下一步：",
    nextChooseChecks: "在目标计划中选择功能检查，审阅后批准执行",
    nextWait: "等待可用的验证结果",
    nextFixFailure: "查看失败的检查并修复后重新验证",
    detailsSummary: "验证详情",
    proofPolicy: "功能通过需要当前代码产物的有效检查结果；补丁格式检查或退出码 0 不能单独证明功能通过。发布与交付仍需各自的验收。",
    inputFrom: (task) => `输入产物来自任务 ${task}，已绑定到本次验证。`,
    exitCode: (code) => `退出码：${code}`,
    timedOut: " · 已超时",
    unknown: "未知",
    reportCounts: (tests, passed, failed, skipped) => `共 ${tests} 项 · 通过 ${passed} · 失败 ${failed} · 跳过 ${skipped}`,
    reportMissing: "缺少完整测试报告",
    fields: {
      baseCommit: "基线 commit", head: "HEAD", tree: "产物 tree", contract: "检查契约 SHA256", result: "结果 SHA256",
      runId: "运行 ID", lease: "租约版本", reason: "原因", inputTask: "输入任务 ID", inputExecution: "输入执行 ID",
      inputCommit: "输入 commit", inputTree: "输入 tree", inputResult: "输入结果 SHA256", inputBinding: "输入绑定 SHA256",
    },
  },
};

const EN: TaskCopy = {
  tasksTitle: "Tasks",
  noNextAction: "No next step yet",
  noBlocker: "None",
  investigateFailure: "Review why the task failed and its run history",
  plannerTimeout: "The agent timed out while planning; open the run history and blocker for details",
  noProductChanges: "The task did not produce the expected file changes",
  reviewNotice: "The task is waiting for review; you can inspect its changes and verification results.",
  askBeforeActing: "Ask before acting",
  functional: {
    sectionLabel: "Functional verification",
    verifiedTitle: "Functionally verified",
    verifiedBody: "Test results are bound to this task's code changes.",
    missingTitle: "Testing not finished",
    missingBody: "There are not yet enough functional test results to show the change works.",
    failedTitle: "Tests failed",
    failedBody: "Functional tests did not pass, so the change cannot be treated as working yet.",
    fixtureTitle: "Fixture only",
    fixtureBody: "This is a demo fixture result and does not verify a real change.",
    nextLabel: "Next:",
    nextChooseChecks: "Choose functional checks in the goal plan, review them, then approve the run",
    nextWait: "Waiting for usable verification results",
    nextFixFailure: "Review the failing checks, fix them and verify again",
    detailsSummary: "Verification details",
    proofPolicy: "A functional pass needs valid check results for the current code artifact; a patch format check or exit code 0 alone does not prove it. Publication and delivery keep their own acceptance.",
    inputFrom: (task) => `Input artifact comes from task ${task} and is bound to this verification.`,
    exitCode: (code) => `Exit code: ${code}`,
    timedOut: " · timed out",
    unknown: "unknown",
    reportCounts: (tests, passed, failed, skipped) => `${tests} total · ${passed} passed · ${failed} failed · ${skipped} skipped`,
    reportMissing: "Complete test report missing",
    fields: {
      baseCommit: "Base commit", head: "HEAD", tree: "Artifact tree", contract: "Check contract SHA256", result: "Result SHA256",
      runId: "Run ID", lease: "Lease epoch", reason: "Reason", inputTask: "Input task ID", inputExecution: "Input execution ID",
      inputCommit: "Input commit", inputTree: "Input tree", inputResult: "Input result SHA256", inputBinding: "Input binding SHA256",
    },
  },
};

const CATALOGUE: Record<UiLocale, TaskCopy> = { "zh-CN": ZH, en: EN };

export function taskCopy(locale: UiLocale = uiLocale()): TaskCopy {
  return CATALOGUE[locale];
}
