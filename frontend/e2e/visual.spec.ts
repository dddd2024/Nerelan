import type { Page } from "@playwright/test";
import { test, expect, open, settle, disableMotion } from "./fixtures";
import {
  APPEARANCE_STORAGE_KEY,
  LEGACY_APPEARANCE_STORAGE_KEY,
  type Appearance,
} from "../src/lib/theme";

/**
 * Seeds a stored appearance through the canonical storage key, then reloads so
 * the screenshot captures what a returning user actually sees.
 *
 * The baselines used to seed `reverse-agent.appearance`, which is now only a
 * migration input. Seeding the retired key would mean the visual contract no
 * longer exercises the key the product writes, so the canonical key is used
 * here and the legacy key gets its own explicit case below.
 */
async function seedAppearance(appPage: Page, appearance: Appearance) {
  await appPage.evaluate(
    ({ key, value }) => localStorage.setItem(key, JSON.stringify(value)),
    { key: APPEARANCE_STORAGE_KEY, value: appearance },
  );
  await appPage.reload();
  await settle(appPage);
  await disableMotion(appPage);
}

test.describe("visual acceptance", () => {
  test("home light @visual", async ({ appPage }) => {
    await open(appPage, "/");
    await seedAppearance(appPage, { mode: "light", accent: "cyan" });
    await expect(appPage).toHaveScreenshot("home-light.png", { animations: "disabled", caret: "hide", scale: "css" });
  });

  test("home dark @visual", async ({ appPage }) => {
    await open(appPage, "/");
    await seedAppearance(appPage, { mode: "dark", accent: "cyan" });
    await expect(appPage).toHaveScreenshot("home-dark.png", { animations: "disabled", caret: "hide", scale: "css" });
  });

  test("settings light @visual", async ({ appPage }) => {
    await open(appPage, "/settings");
    await seedAppearance(appPage, { mode: "light", accent: "cyan" });
    await expect(appPage).toHaveScreenshot("settings-light.png", { animations: "disabled", caret: "hide", scale: "css" });
  });

  test("settings dark @visual", async ({ appPage }) => {
    await open(appPage, "/settings");
    await seedAppearance(appPage, { mode: "dark", accent: "cyan" });
    await expect(appPage).toHaveScreenshot("settings-dark.png", { animations: "disabled", caret: "hide", scale: "css" });
  });
});

test.describe("appearance storage migration", () => {
  /**
   * The pre-paint migration lives in an inline script in `index.html`, so no
   * unit test can cover it: jsdom never executes that script. This case is the
   * only check that a user who still has `reverse-agent.appearance` keeps both
   * the preference and a first paint with no flash of the default theme.
   */
  test("retires the legacy key in the browser without losing the preference", async ({ appPage }) => {
    const legacyAppearance: Appearance = { mode: "dark", accent: "violet" };

    await appPage.goto("/");
    await appPage.evaluate(
      ({ canonical, legacy, value }) => {
        localStorage.removeItem(canonical);
        localStorage.setItem(legacy, JSON.stringify(value));
      },
      {
        canonical: APPEARANCE_STORAGE_KEY,
        legacy: LEGACY_APPEARANCE_STORAGE_KEY,
        value: legacyAppearance,
      },
    );

    await appPage.reload();

    await expect(appPage.locator("html")).toHaveAttribute("data-theme", "dark");
    await expect(appPage.locator("html")).toHaveAttribute("data-accent", "violet");

    const stored = await appPage.evaluate(
      ({ canonical, legacy }) => ({
        canonical: localStorage.getItem(canonical),
        legacy: localStorage.getItem(legacy),
      }),
      { canonical: APPEARANCE_STORAGE_KEY, legacy: LEGACY_APPEARANCE_STORAGE_KEY },
    );

    expect(stored.canonical).toBe(JSON.stringify(legacyAppearance));
    expect(stored.legacy).toBeNull();
  });
});
