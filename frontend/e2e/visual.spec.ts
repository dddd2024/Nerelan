import { test, expect, open, settle, disableMotion } from "./fixtures";

test.describe("visual acceptance", () => {
  test("home light @visual", async ({ appPage }) => {
    await open(appPage, "/");
    await appPage.evaluate(() => localStorage.setItem("reverse-agent.appearance", JSON.stringify({ mode: "light", accent: "cyan" })));
    await appPage.reload();
    await settle(appPage);
    await disableMotion(appPage);
    await expect(appPage).toHaveScreenshot("home-light.png", { animations: "disabled", caret: "hide", scale: "css" });
  });

  test("home dark @visual", async ({ appPage }) => {
    await open(appPage, "/");
    await appPage.evaluate(() => localStorage.setItem("reverse-agent.appearance", JSON.stringify({ mode: "dark", accent: "cyan" })));
    await appPage.reload();
    await settle(appPage);
    await disableMotion(appPage);
    await expect(appPage).toHaveScreenshot("home-dark.png", { animations: "disabled", caret: "hide", scale: "css" });
  });

  test("settings light @visual", async ({ appPage }) => {
    await open(appPage, "/settings");
    await appPage.evaluate(() => localStorage.setItem("reverse-agent.appearance", JSON.stringify({ mode: "light", accent: "cyan" })));
    await appPage.reload();
    await settle(appPage);
    await disableMotion(appPage);
    await expect(appPage).toHaveScreenshot("settings-light.png", { animations: "disabled", caret: "hide", scale: "css" });
  });

  test("settings dark @visual", async ({ appPage }) => {
    await open(appPage, "/settings");
    await appPage.evaluate(() => localStorage.setItem("reverse-agent.appearance", JSON.stringify({ mode: "dark", accent: "cyan" })));
    await appPage.reload();
    await settle(appPage);
    await disableMotion(appPage);
    await expect(appPage).toHaveScreenshot("settings-dark.png", { animations: "disabled", caret: "hide", scale: "css" });
  });
});
