import { test, expect, open, settle } from "./fixtures";

test.describe("home workspace", () => {
  test("opens on the composer and lists recent goals", async ({ appPage }) => {
    await open(appPage, "/");
    await settle(appPage);
    await expect(appPage.getByRole("heading", { name: "今天想完成什么？" })).toBeVisible();
    await expect(appPage.getByTestId("goal-composer-section")).toBeVisible();
    await expect(appPage.getByTestId("recent-goals-section")).toBeVisible();
    await expect(appPage.getByTestId("active-goal-header")).toHaveCount(0);
  });

  test("shows a selected Goal as a thread with a docked composer", async ({ appPage }) => {
    await open(appPage, "/?goal=goal-demo-platform");
    await settle(appPage);
    await expect(appPage.getByTestId("active-goal-header")).toBeVisible();
    await expect(
      appPage.getByRole("heading", { name: "完善无人值守多 Agent 平台" }),
    ).toBeVisible();
    await expect(appPage.getByTestId("goal-composer-section")).toBeInViewport();
    await expect(appPage.getByTestId("current-execution-section")).toBeVisible();
    await expect(appPage.getByTestId("active-goal-stream")).toBeVisible();
    await expect(appPage.getByTestId("autonomy-status")).toContainText("1/12");
    await expect(appPage.getByTestId("coordinator-status")).toContainText("协调器在线");
    await expect(appPage.getByText(/能力$/)).toHaveCount(0);
    if (await appPage.evaluate(() => window.innerWidth > 500)) {
      await expect(appPage.getByTestId("new-task-button")).toBeVisible();
      await expect(appPage.getByTestId("toggle-conversation-panel")).toBeVisible();
      await expect(appPage.getByTestId("sidebar-section-recent")).toBeVisible();
      await expect(appPage.getByTestId("sidebar-section-projects")).toBeVisible();
      await expect(appPage.getByTestId("sidebar-nav-设置")).toBeVisible();
      await expect(appPage.getByTestId("sidebar-nav-Agent 运行")).toBeVisible();
    } else {
      await expect(appPage.getByTestId("mobile-menu-button")).toBeVisible();
    }
  });

  test("opens the command palette with the keyboard", async ({ appPage }) => {
    if (await appPage.evaluate(() => window.innerWidth <= 500)) test.skip();
    await open(appPage, "/");
    await settle(appPage);
    await appPage.keyboard.press("Control+k");
    await expect(appPage.getByTestId("conversation-panel")).toBeVisible();
    await appPage.getByTestId("task-search-input").fill("运行");
    await appPage.keyboard.press("Enter");
    await expect(appPage.getByTestId("runs-page")).toBeVisible();
    await expect(appPage.getByTestId("conversation-panel")).toHaveCount(0);
  });

  test("can open the mobile navigation overflow", async ({ appPage }) => {
    if (await appPage.evaluate(() => window.innerWidth > 500)) test.skip();
    await open(appPage, "/");
    await appPage.getByTestId("mobile-menu-button").click();
    await expect(appPage.getByTestId("mobile-drawer")).toBeVisible();
    await expect(appPage.getByTestId("mobile-nav-收件箱")).toBeVisible();
    await appPage.getByTestId("mobile-drawer-close").click();
    await expect(appPage.getByTestId("mobile-drawer")).toBeHidden();
  });
});
