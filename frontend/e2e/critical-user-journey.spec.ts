import { type Page } from "@playwright/test";
import { test, expect, open, settle } from "./fixtures";

const GOAL_TITLE = "Playwright provider-free critical journey";
// Cancellation uses the fixture's separate queued Run. The new default Goal
// intentionally has one bounded Task, matching the actual Goal planner.
const QUEUED_TASK_ID = "task-demo-queued";

async function navigateFromShell(page: Page, destination: "首页" | "设置") {
  const mobile = await page.evaluate(() => window.innerWidth <= 500);
  if (mobile) {
    await page.getByTestId("mobile-menu-button").click();
    const link = page.getByTestId(`mobile-nav-${destination}`);
    await expect(link).toBeVisible();
    await link.click();
  } else if (destination === "设置") {
    await page.getByTestId("sidebar-nav-设置").click();
  } else {
    await page.getByTestId("sidebar-logo").click();
  }
  await settle(page);
}

test("completes one provider-free critical user journey end to end", async ({ appPage }) => {
  await open(appPage, "/");
  await settle(appPage);

  await navigateFromShell(appPage, "设置");
  await expect(appPage.getByTestId("settings-page")).toBeVisible();

  await navigateFromShell(appPage, "首页");
  await expect(appPage.getByTestId("platform-home")).toBeVisible();

  await appPage.getByLabel("描述最终目标").fill(GOAL_TITLE);
  await appPage.getByLabel("执行模式").selectOption("deterministic_fixture");
  await appPage.getByRole("button", { name: "创建并审阅目标" }).click();
  await expect(appPage.getByTestId("approval-goal-detail")).toBeVisible();
  const goalId = new URL(appPage.url()).searchParams.get("goal");
  await expect(appPage.getByTestId("approval-launch-button")).toHaveCount(0);
  await appPage.getByTestId("approval-plan-button").click();
  await expect(appPage.getByTestId("approval-plan")).toContainText(GOAL_TITLE);
  await appPage.getByTestId("approval-approve-button").click();
  await expect(appPage.getByTestId("approval-launch-button")).toBeDisabled();
  await appPage.getByLabel("确认启动当前计划").check();
  await appPage.getByTestId("approval-launch-button").click();

  await expect(appPage.getByTestId("goal-progress-bar")).toBeVisible();
  await expect(appPage.getByRole("heading", { name: GOAL_TITLE })).toBeVisible();
  expect(new URL(appPage.url()).searchParams.get("goal")).toBe(goalId);
  const currentExecution = appPage.getByTestId("current-execution-section");
  await expect(currentExecution.getByTestId("goal-current-activity")).toBeVisible({ timeout: 12_000 });

  await currentExecution.getByTestId("goal-activity-full-run-link").click();
  await settle(appPage);
  await expect(appPage.getByTestId("runs-page")).toBeVisible();
  const PRIMARY_TASK_ID = new URL(appPage.url()).searchParams.get("task");
  expect(PRIMARY_TASK_ID).toBeTruthy();

  const primary = appPage.getByTestId(`run-${PRIMARY_TASK_ID}`);
  await expect(primary).toBeVisible();
  await primary.getByTestId(`run-toggle-${PRIMARY_TASK_ID}`).click();
  await expect(primary.getByTestId(`run-agents-${PRIMARY_TASK_ID}`)).toBeVisible();
  await expect(primary.getByTestId(`run-activity-section-${PRIMARY_TASK_ID}`)).toBeVisible();
  await expect(primary.getByTestId(`run-files-${PRIMARY_TASK_ID}`)).toBeVisible();
  await expect(primary.getByTestId(`run-validation-${PRIMARY_TASK_ID}`)).toBeVisible();

  const queued = appPage.getByTestId(`run-${QUEUED_TASK_ID}`);
  await expect(queued).toBeVisible();
  await queued.getByTestId(`run-toggle-${QUEUED_TASK_ID}`).click();
  await queued.getByTestId(`run-cancel-${QUEUED_TASK_ID}`).click();
  await expect(queued.getByTestId(`run-cancel-confirm-${QUEUED_TASK_ID}`)).toBeVisible();
  await queued.getByRole("button", { name: "确认取消" }).click();
  await expect(queued.getByTestId(`run-state-${QUEUED_TASK_ID}`)).toContainText("CANCELLED");

  await navigateFromShell(appPage, "首页");
  await expect(appPage.getByTestId("platform-home")).toBeVisible();
  await expect(appPage.getByRole("heading", { name: GOAL_TITLE })).toBeVisible();
});
