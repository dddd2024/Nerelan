import { test, expect, open, settle } from "./fixtures";

const routes = [
  ["/", "platform-home"],
  ["/tasks", "tasks-page"],
  ["/inbox", "inbox-page"],
  ["/roadmap", "roadmap-page"],
  ["/runs", "runs-page"],
  ["/settings", "settings-page"],
] as const;

function routeLabel(path: string) {
  return path === "/tasks"
    ? "任务"
    : path === "/inbox"
      ? "收件箱"
      : path === "/roadmap"
        ? "路线图"
        : path === "/runs"
          ? "Agent 运行"
          : "设置";
}

test("keeps all six product routes reachable through task-first desktop IA", async ({ appPage }) => {
  await open(appPage, "/");
  await settle(appPage);
  if (await appPage.evaluate(() => window.innerWidth <= 500)) {
    for (const [path, testId] of routes.slice(1)) {
      await appPage.getByTestId("mobile-menu-button").click();
      const link = appPage.getByTestId("mobile-nav-" + routeLabel(path));
      await expect(link).toBeVisible();
      await link.focus();
      await expect(link).toBeFocused();
      await link.click();
      await settle(appPage);
      await expect(appPage.getByTestId(testId)).toBeVisible();
      await expect(appPage.getByTestId("mobile-drawer")).toBeHidden();
    }
  } else {
    for (const [path, testId] of routes.slice(1, -1)) {
      await appPage.getByTestId("sidebar-more-toggle").click();
      const link = appPage.getByTestId("sidebar-nav-" + routeLabel(path));
      await expect(link).toBeVisible();
      await link.focus();
      await expect(link).toBeFocused();
      await link.click();
      await settle(appPage);
      await expect(appPage.getByTestId(testId)).toBeVisible();
    }

    const settings = appPage.getByTestId("sidebar-nav-设置");
    await expect(settings).toBeVisible();
    await settings.click();
    await settle(appPage);
    await expect(appPage.getByTestId("settings-page")).toBeVisible();
    await expect(settings).toHaveClass(/bg-ra-tertiary/);
  }
});
