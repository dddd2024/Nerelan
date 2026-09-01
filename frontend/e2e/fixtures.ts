import { test as base, expect, type Page } from "@playwright/test";

const FIXED_NOW = "2026-08-24T12:00:00.000Z";

export const test = base.extend<{ appPage: Page }>({
  appPage: async ({ page, context }, use) => {
    await context.addInitScript(({ fixedNow }) => {
      const RealDate = Date;
      const fixedTime = RealDate.parse(fixedNow);
      class FixedDate extends RealDate {
        constructor(...args: ConstructorParameters<typeof Date>) {
          if (args.length === 0) super(fixedTime);
          else super(...args);
        }
        static now() { return fixedTime; }
      }
      globalThis.Date = FixedDate;
    }, { fixedNow: FIXED_NOW });
    await page.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.origin === "http://127.0.0.1:4173" || url.protocol === "data:" || url.protocol === "blob:") {
        await route.continue();
      } else {
        await route.abort("blockedbyclient");
      }
    });
    await use(page);
  },
});

export { expect };

export async function open(page: Page, path: string) {
  await page.goto(path);
  await expect(page.locator("#root")).toBeVisible();
}

export async function settle(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => document.fonts?.ready);
  await page.waitForTimeout(150);
}

export async function disableMotion(page: Page) {
  await page.addStyleTag({ content: "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}" });
}

export type LifecycleVisualScenario =
  | "empty"
  | "running"
  | "waiting"
  | "validating"
  | "completed"
  | "failed"
  | "blocked"
  | "owner-action"
  | "large-changes"
  | "long-stream"
  | "multi-agent";

interface RuntimeRun {
  [key: string]: unknown;
  task_id: string;
  title: string;
  repository: string;
  status: string;
  state: string;
  goal_id: string;
  goal_title: string;
  window_id: string;
}

interface BrowserPlatformClient {
  fetchRuns: () => Promise<RuntimeRun[]>;
  __setMockRuns: (runs: RuntimeRun[]) => void;
  __setMockGoalStatus: (goalId: string, override: Record<string, unknown>) => void;
}

export async function applyLifecycleVisualState(
  page: Page,
  scenario: LifecycleVisualScenario,
) {
  await page.evaluate(async (scenarioName) => {
    const loadClient = new Function(
      "return import('/src/lib/platform-client.ts')",
    ) as () => Promise<BrowserPlatformClient>;
    const client = await loadClient();
    const sourceRuns = await client.fetchRuns();
    const source =
      sourceRuns.find((run) => run.task_id === "task-demo-2") ?? sourceRuns[0];
    if (!source) throw new Error("deterministic mock run fixture is unavailable");

    const now = Date.now();
    const iso = (minutesAgo: number) =>
      new Date(now - minutesAgo * 60_000).toISOString();
    const coder = { agent_id: "coder", role: "coder", display_name: "Coder" };
    const reviewer = {
      agent_id: "reviewer",
      role: "reviewer",
      display_name: "Reviewer",
    };
    const planner = {
      agent_id: "planner",
      role: "planner",
      display_name: "Planner",
    };

    const link = (taskId: string, status: string, title: string, index = 1) => ({
      task_id: taskId,
      plan_task_id: `T${String(index).padStart(3, "0")}`,
      status,
      title,
    });

    const activityEvent = (
      id: string,
      taskId: string,
      category: string,
      title: string,
      minutesAgo: number,
      agent = coder,
    ) => ({
      id,
      task_id: taskId,
      timestamp: iso(minutesAgo),
      category,
      title,
      description: "",
      stage: category === "VERIFY" || category === "TEST" ? "VERIFY" : "EXECUTE",
      agent,
    });

    const makeRun = (
      taskId: string,
      overrides: Record<string, unknown> = {},
    ): RuntimeRun => ({
      ...structuredClone(source),
      task_id: taskId,
      title: `[Visual acceptance] ${taskId}`,
      repository: "dddd2024/reverse-agent",
      status: "RUNNING",
      state: "RUNNING",
      goal_id: "goal-demo-platform",
      goal_title: "完善无人值守多 Agent 平台",
      window_id: "window-demo",
      stage: "EXECUTE",
      liveness: "ACTIVE",
      created_at: iso(18),
      updated_at: iso(1),
      last_activity_at: iso(1),
      current_agent: coder,
      agents: [coder],
      current_activity: {
        category: "EDIT",
        title: "正在修改实现",
        description: "根据已批准计划更新任务实现。",
        agent: coder,
        timestamp: iso(1),
      },
      change_summary: null,
      validation: null,
      events: [],
      activity: [],
      changed_files: [],
      publication: null,
      ...overrides,
    });

    let goalStatus = "RUNNING";
    let taskLinks: Array<Record<string, unknown>> = [];
    let runs: RuntimeRun[] = [];

    if (scenarioName === "empty") {
      goalStatus = "DRAFT";
      taskLinks = [];
      runs = [];
    } else if (scenarioName === "running") {
      const taskId = "visual-running";
      taskLinks = [link(taskId, "RUNNING", "实现任务执行链路")];
      runs = [
        makeRun(taskId, {
          liveness: "ACTIVE",
          current_activity: {
            category: "EDIT",
            title: "正在实现任务执行链路",
            description: "Coder 正在写入已批准的最小修改。",
            agent: coder,
            timestamp: iso(1),
          },
          activity: [
            activityEvent("running-read", taskId, "READ", "读取执行入口", 6),
            activityEvent("running-edit", taskId, "EDIT", "修改任务执行链路", 3),
            activityEvent("running-checkpoint", taskId, "CHECKPOINT", "保存执行检查点", 1),
          ],
          change_summary: { file_count: 3, additions: 72, deletions: 18 },
        }),
      ];
    } else if (scenarioName === "waiting") {
      const taskId = "visual-waiting";
      taskLinks = [link(taskId, "RUNNING", "等待依赖完成")];
      runs = [
        makeRun(taskId, {
          liveness: "WAITING",
          current_activity: {
            category: "AGENT_WAITING",
            title: "等待上游任务完成",
            description: "当前任务保持可恢复，等待依赖结果。",
            agent: coder,
            timestamp: iso(2),
          },
          activity: [
            activityEvent("waiting-start", taskId, "AGENT_STARTED", "Coder 开始执行", 8),
            activityEvent("waiting-state", taskId, "AGENT_WAITING", "进入依赖等待", 2),
          ],
        }),
      ];
    } else if (scenarioName === "validating") {
      const taskId = "visual-validating";
      taskLinks = [link(taskId, "VALIDATING", "验证候选结果")];
      runs = [
        makeRun(taskId, {
          stage: "VERIFY",
          liveness: "VALIDATING",
          current_agent: reviewer,
          agents: [coder, reviewer],
          current_activity: {
            category: "VERIFY",
            title: "正在运行独立验证",
            description: "Reviewer 正在核验候选结果与测试证据。",
            agent: reviewer,
            timestamp: iso(1),
          },
          activity: [
            activityEvent("validating-edit", taskId, "EDIT", "候选修改完成", 7),
            activityEvent("validating-test", taskId, "TEST", "执行确定性测试", 3, reviewer),
            activityEvent("validating-now", taskId, "VERIFY", "独立验证进行中", 1, reviewer),
          ],
          validation: {
            command_id: "npm test",
            status: "RUNNING",
            summary: "deterministic frontend suite",
          },
        }),
      ];
    } else if (scenarioName === "completed") {
      const taskId = "visual-completed";
      goalStatus = "COMPLETED";
      taskLinks = [link(taskId, "READY_FOR_REVIEW", "交付验证结果")];
      runs = [
        makeRun(taskId, {
          status: "READY_FOR_REVIEW",
          state: "READY_FOR_HUMAN",
          stage: "VERIFY",
          liveness: "TERMINAL",
          current_agent: reviewer,
          agents: [coder, reviewer],
          current_activity: {
            category: "AGENT_COMPLETED",
            title: "任务已完成并通过验证",
            description: "结果与证据已准备完成。",
            agent: reviewer,
            timestamp: iso(1),
          },
          activity: [
            activityEvent("completed-edit", taskId, "EDIT", "实现修改完成", 8),
            activityEvent("completed-test", taskId, "TEST", "测试通过", 4, reviewer),
            activityEvent("completed-done", taskId, "AGENT_COMPLETED", "Agent 执行完成", 1, reviewer),
          ],
          change_summary: { file_count: 4, additions: 91, deletions: 24 },
          validation: {
            command_id: "npm test",
            status: "SUCCESS",
            exit_code: 0,
            summary: "all deterministic checks passed",
          },
        }),
      ];
    } else if (scenarioName === "failed") {
      const taskId = "visual-failed";
      goalStatus = "INVALIDATED";
      taskLinks = [link(taskId, "FAILED", "修复验证失败")];
      runs = [
        makeRun(taskId, {
          status: "FAILED",
          state: "FAILED_TERMINAL",
          liveness: "TERMINAL",
          failure_classification: "validation_failed",
          current_agent: reviewer,
          current_activity: {
            category: "BLOCKED",
            title: "验证失败，Run 已终止",
            description: "确定性检查失败，需要重新规划后再执行。",
            agent: reviewer,
            timestamp: iso(1),
          },
          activity: [
            activityEvent("failed-test", taskId, "TEST", "运行确定性测试", 3, reviewer),
            activityEvent("failed-stop", taskId, "BLOCKED", "验证失败并终止", 1, reviewer),
          ],
          validation: {
            command_id: "npm test",
            status: "FAILED",
            exit_code: 1,
            summary: "1 deterministic check failed",
          },
        }),
      ];
    } else if (scenarioName === "blocked") {
      const taskId = "visual-blocked";
      goalStatus = "BLOCKED";
      taskLinks = [link(taskId, "BLOCKED", "处理执行阻塞")];
      runs = [
        makeRun(taskId, {
          status: "BLOCKED",
          state: "BLOCKED_EXTERNAL",
          liveness: "BLOCKED",
          current_activity: {
            category: "BLOCKED",
            title: "上游执行器不可用",
            description: "当前任务无法继续，等待外部阻塞解除。",
            timestamp: iso(2),
          },
          activity: [
            activityEvent("blocked-read", taskId, "READ", "检查执行环境", 7),
            activityEvent("blocked-stop", taskId, "BLOCKED", "执行被阻塞", 2),
          ],
        }),
      ];
    } else if (scenarioName === "owner-action") {
      const taskId = "visual-owner-action";
      taskLinks = [link(taskId, "READY_FOR_REVIEW", "等待 Owner 审查")];
      runs = [
        makeRun(taskId, {
          status: "READY_FOR_REVIEW",
          state: "READY_FOR_HUMAN",
          stage: "VERIFY",
          liveness: "OWNER_ACTION_REQUIRED",
          current_agent: reviewer,
          agents: [coder, reviewer],
          current_activity: {
            category: "OWNER_ACTION_REQUIRED",
            title: "等待 Owner 审查",
            description: "自动验证已完成，需要 Owner 决定是否继续。",
            agent: reviewer,
            timestamp: iso(1),
          },
          activity: [
            activityEvent("owner-test", taskId, "TEST", "自动验证通过", 5, reviewer),
            activityEvent("owner-wait", taskId, "OWNER_ACTION_REQUIRED", "转交 Owner 审查", 1, reviewer),
          ],
          validation: {
            command_id: "npm test",
            status: "SUCCESS",
            exit_code: 0,
            summary: "all checks passed",
          },
        }),
      ];
    } else if (scenarioName === "large-changes") {
      const first = "visual-large-a";
      const second = "visual-large-b";
      taskLinks = [
        link(first, "RUNNING", "重构执行链路 A", 1),
        link(second, "RUNNING", "重构执行链路 B", 2),
      ];
      runs = [
        makeRun(first, {
          change_summary: { file_count: 85, additions: 4000, deletions: 3500 },
          current_activity: {
            category: "EDIT",
            title: "正在整理大规模修改",
            description: "界面仅展示聚合变更统计，不展开原始文件墙。",
            agent: coder,
            timestamp: iso(1),
          },
        }),
        makeRun(second, {
          current_agent: reviewer,
          agents: [reviewer],
          change_summary: { file_count: 64, additions: 2000, deletions: 1000 },
          current_activity: {
            category: "VERIFY",
            title: "并行核验变更范围",
            description: "Reviewer 正在检查另一组修改。",
            agent: reviewer,
            timestamp: iso(2),
          },
        }),
      ];
    } else if (scenarioName === "long-stream") {
      const taskId = "visual-long-stream";
      taskLinks = [link(taskId, "RUNNING", "处理长时间执行流")];
      runs = [
        makeRun(taskId, {
          current_activity: {
            category: "EDIT",
            title: "继续处理长时间执行流",
            description: "仅保留最近的高价值语义事件。",
            agent: coder,
            timestamp: iso(0),
          },
          activity: Array.from({ length: 30 }, (_, index) =>
            activityEvent(
              `long-${index}`,
              taskId,
              index % 3 === 0 ? "READ" : index % 3 === 1 ? "EDIT" : "VERIFY",
              `语义事件 ${index}`,
              30 - index,
              index % 3 === 2 ? reviewer : coder,
            ),
          ),
          change_summary: { file_count: 12, additions: 420, deletions: 133 },
        }),
      ];
    } else if (scenarioName === "multi-agent") {
      const first = "visual-agent-a";
      const second = "visual-agent-b";
      taskLinks = [
        link(first, "RUNNING", "实现执行路径", 1),
        link(second, "VALIDATING", "并行验证路径", 2),
      ];
      runs = [
        makeRun(first, {
          current_agent: coder,
          agents: [planner, coder],
          current_activity: {
            category: "EDIT",
            title: "Coder 正在实现执行路径",
            description: "主实现任务持续推进。",
            agent: coder,
            timestamp: iso(1),
          },
          activity: [
            activityEvent("multi-plan", first, "PLAN", "Planner 完成计划", 7, planner),
            activityEvent("multi-edit", first, "EDIT", "Coder 修改实现", 1, coder),
          ],
        }),
        makeRun(second, {
          stage: "VERIFY",
          liveness: "VALIDATING",
          current_agent: reviewer,
          agents: [reviewer],
          current_activity: {
            category: "VERIFY",
            title: "Reviewer 并行验证",
            description: "验证任务与实现任务同时推进。",
            agent: reviewer,
            timestamp: iso(1),
          },
          activity: [
            activityEvent("multi-verify", second, "VERIFY", "Reviewer 核验候选结果", 1, reviewer),
          ],
        }),
      ];
    }

    client.__setMockGoalStatus("goal-demo-platform", {
      status: goalStatus,
      updated_at: iso(1),
      task_links: taskLinks,
    });
    client.__setMockRuns(runs);
  }, scenario);

  await page.evaluate(() => {
    window.dispatchEvent(new Event("online"));
    window.dispatchEvent(new Event("focus"));
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await page.waitForTimeout(200);
}
