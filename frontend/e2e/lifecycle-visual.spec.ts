import type { Page } from "@playwright/test";
import {
  applyLifecycleVisualState,
  disableMotion,
  expect,
  open,
  settle,
  test,
  type LifecycleVisualScenario,
} from "./fixtures";

const CASES: Array<{
  scenario: LifecycleVisualScenario;
  mobile: boolean;
  assertion: { testId?: string; text?: string; absentTestId?: string };
}> = [
  {
    scenario: "empty",
    mobile: true,
    assertion: { testId: "goal-state-label", text: "草稿", absentTestId: "goal-current-activity" },
  },
  {
    scenario: "running",
    mobile: true,
    assertion: { testId: "goal-current-activity-now", text: "正在实现任务执行链路" },
  },
  {
    scenario: "waiting",
    mobile: false,
    assertion: { testId: "goal-activity-liveness", text: "等待中" },
  },
  {
    scenario: "validating",
    mobile: false,
    assertion: { testId: "goal-activity-liveness", text: "验证中" },
  },
  {
    scenario: "completed",
    mobile: false,
    assertion: { testId: "goal-state-label", text: "已完成" },
  },
  {
    scenario: "failed",
    mobile: false,
    assertion: { testId: "goal-current-activity-now", text: "验证失败，Run 已终止" },
  },
  {
    scenario: "blocked",
    mobile: true,
    assertion: { testId: "goal-activity-liveness", text: "已阻塞" },
  },
  {
    scenario: "owner-action",
    mobile: true,
    assertion: { testId: "goal-activity-liveness", text: "需要 Owner 处理" },
  },
  {
    scenario: "large-changes",
    mobile: false,
    assertion: { testId: "goal-activity-change-summary", text: "149 个文件变更 · +6000 -4500" },
  },
  {
    scenario: "long-stream",
    mobile: true,
    assertion: { testId: "goal-activity-event-long-29", text: "语义事件 29" },
  },
  {
    scenario: "multi-agent",
    mobile: false,
    assertion: { testId: "goal-activity-agents", text: "2 个 Agent 并行" },
  },
];

async function prepareLightMode(page: Page) {
  await open(page, "/");
  await page.evaluate(() =>
    localStorage.setItem(
      "reverse-agent.appearance",
      JSON.stringify({ mode: "light", accent: "cyan" }),
    ),
  );
  await page.reload();
  await settle(page);
}

test.describe("task-first lifecycle visual matrix @visual", () => {
  for (const entry of CASES) {
    test(`${entry.scenario} lifecycle state @visual`, async ({ appPage }, testInfo) => {
      const isMobile = testInfo.project.name === "mobile-chromium";
      test.skip(isMobile && !entry.mobile, "desktop-only stress/lifecycle acceptance state");

      await prepareLightMode(appPage);
      await applyLifecycleVisualState(appPage, entry.scenario);

      if (entry.assertion.testId && entry.assertion.text) {
        await expect(appPage.getByTestId(entry.assertion.testId)).toContainText(
          entry.assertion.text,
        );
      }
      if (entry.assertion.absentTestId) {
        await expect(appPage.getByTestId(entry.assertion.absentTestId)).toHaveCount(0);
      }

      await settle(appPage);
      await disableMotion(appPage);
      await expect(appPage).toHaveScreenshot(`home-${entry.scenario}-light.png`, {
        animations: "disabled",
        caret: "hide",
        scale: "css",
      });
    });
  }
});
