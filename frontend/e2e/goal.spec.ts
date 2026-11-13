import { test, expect, open, settle } from "./fixtures";

test("runs a provider-free goal with a deterministic fixture and bounded window", async ({ appPage }) => {
  await open(appPage, "/");
  await settle(appPage);
  await appPage.getByLabel("描述最终目标").fill("Playwright provider-free acceptance goal");
  await appPage.locator("[aria-controls=\"goal-composer-advanced\"]").click();
  await appPage.getByLabel("执行模式").selectOption("deterministic_fixture");
  await appPage.getByRole("button", { name: "创建并审阅目标" }).click();
  await expect(appPage.getByTestId("approval-goal-detail")).toBeVisible();
  const goalId = new URL(appPage.url()).searchParams.get("goal");
  expect(goalId).toBeTruthy();
  await expect(appPage.getByTestId("start-card")).toHaveCount(0);
  await appPage.getByTestId("approval-plan-button").click();
  await expect(appPage.getByTestId("approval-plan")).toContainText("Playwright provider-free acceptance goal");
  // Owner decision 2026-11-09: the planned goal starts from the confirmation card.
  await expect(appPage.getByTestId("approval-approve-button")).toHaveCount(0);
  await expect(appPage.getByTestId("start-preflight")).toContainText("检查通过");
  await appPage.getByTestId("start-button").click();
  await expect(appPage.getByTestId("goal-thread")).toBeVisible();
  expect(new URL(appPage.url()).searchParams.get("goal")).toBe(goalId);
  await expect(appPage.getByRole("heading", { name: "Playwright provider-free acceptance goal" })).toBeVisible();
});
