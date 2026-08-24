import { beforeEach, describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { ThemeSelector } from "@/components/theme-selector";
import {
  ACCENTS,
  APPEARANCE_STORAGE_KEY,
  DEFAULT_APPEARANCE,
  normalizeAppearance,
  readAppearance,
  setAppearance,
} from "@/lib/theme";

describe("presentation appearance", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.removeAttribute("data-accent");
  });

  it("accepts only the fixed theme and accent values", () => {
    expect(normalizeAppearance({ mode: "light", accent: "rose" })).toEqual({ mode: "light", accent: "rose" });
    expect(normalizeAppearance({ mode: "unsafe", accent: "url(javascript:)" })).toEqual(DEFAULT_APPEARANCE);
    expect(ACCENTS).toEqual(["cyan", "blue", "violet", "amber", "rose"]);
  });

  it("applies and persists a presentation-only preference", () => {
    setAppearance({ mode: "light", accent: "violet" });
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(document.documentElement.dataset.accent).toBe("violet");
    expect(readAppearance()).toEqual({ mode: "light", accent: "violet" });
    expect(window.localStorage.getItem(APPEARANCE_STORAGE_KEY)).toContain("violet");
  });

  it("exposes keyboard-accessible theme and accent radios", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ThemeSelector />);

    const light = screen.getByTestId("theme-option-light");
    expect(light).toHaveAttribute("type", "radio");
    expect(light).not.toBeChecked();
    await user.click(light);
    expect(light).toBeChecked();

    const system = screen.getByTestId("theme-option-system");
    system.focus();
    await user.keyboard("{ArrowRight}");
    expect(light).toBeChecked();

    const rose = screen.getByTestId("accent-option-rose");
    await user.click(rose);
    expect(rose).toBeChecked();
    expect(document.documentElement.dataset.accent).toBe("rose");
  });

  it("fails safe when a supplied storage implementation throws", () => {
    const throwingStorage = {
      getItem: () => { throw new Error("storage read denied"); },
      setItem: () => { throw new Error("storage write denied"); },
    } as unknown as Storage;

    expect(readAppearance(throwingStorage)).toEqual(DEFAULT_APPEARANCE);
    expect(() => setAppearance({ mode: "dark", accent: "blue" }, document.documentElement, throwingStorage)).not.toThrow();
  });
});
