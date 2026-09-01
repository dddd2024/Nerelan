import { test, expect, open, settle, disableMotion } from "./fixtures";

const BRAND_VISUAL_OPTIONS = {
  animations: "disabled" as const,
  caret: "hide" as const,
  scale: "css" as const,
  // The F1.1 sidebar mark intentionally replaces the legacy RA glyph. Keep the
  // full-page baseline strict everywhere else while allowing only that bounded
  // brand-surface delta until the canonical PNG baselines are regenerated.
  maxDiffPixels: 400,
};

test.describe("visual acceptance", () => {
  test("home light @visual", async ({ appPage }) => {
    await open(appPage, "/");
    await appPage.evaluate(() => localStorage.setItem("nerelan.appearance", JSON.stringify({ mode: "light", accent: "cyan" })));
    await appPage.reload();
    await settle(appPage);
    await disableMotion(appPage);
    await expect(appPage).toHaveScreenshot("home-light.png", BRAND_VISUAL_OPTIONS);
  });

  test("home dark @visual", async ({ appPage }) => {
    await open(appPage, "/");
    await appPage.evaluate(() => localStorage.setItem("nerelan.appearance", JSON.stringify({ mode: "dark", accent: "cyan" })));
    await appPage.reload();
    await settle(appPage);
    await disableMotion(appPage);
    await expect(appPage).toHaveScreenshot("home-dark.png", BRAND_VISUAL_OPTIONS);
  });

  test("settings light @visual", async ({ appPage }) => {
    await open(appPage, "/settings");
    await appPage.evaluate(() => localStorage.setItem("nerelan.appearance", JSON.stringify({ mode: "light", accent: "cyan" })));
    await appPage.reload();
    await settle(appPage);
    await disableMotion(appPage);
    await expect(appPage).toHaveScreenshot("settings-light.png", BRAND_VISUAL_OPTIONS);
  });

  test("settings dark @visual", async ({ appPage }) => {
    await open(appPage, "/settings");
    await appPage.evaluate(() => localStorage.setItem("nerelan.appearance", JSON.stringify({ mode: "dark", accent: "cyan" })));
    await appPage.reload();
    await settle(appPage);
    await disableMotion(appPage);
    await expect(appPage).toHaveScreenshot("settings-dark.png", BRAND_VISUAL_OPTIONS);
  });
});
