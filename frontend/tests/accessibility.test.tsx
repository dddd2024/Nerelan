import { readFileSync } from "node:fs";
import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { PermissionSelector } from "@/components/permission-selector";
import { CustomPolicyEditor } from "@/components/custom-policy-editor";
import { Sidebar } from "@/components/sidebar";
import { profileToPolicy } from "@/lib/profile-mapper";

function read(relative: string) {
  return readFileSync(relative, "utf8");
}

function srgbChannel(value: number) {
  const channel = value / 255;
  return channel <= 0.04045
    ? channel / 12.92
    : ((channel + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(hex: string) {
  const value = Number.parseInt(hex.slice(1), 16);
  const red = (value >> 16) & 0xff;
  const green = (value >> 8) & 0xff;
  const blue = value & 0xff;
  return (
    0.2126 * srgbChannel(red) +
    0.7152 * srgbChannel(green) +
    0.0722 * srgbChannel(blue)
  );
}

function contrastRatio(a: string, b: string) {
  const first = relativeLuminance(a);
  const second = relativeLuminance(b);
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Every hex declared by an `--ra-accent-tone-*` rule, across all three theme
 * scopes, lowercased and without the leading `#`.
 *
 * Asserting on declarations rather than on the raw file text matters because
 * the tone lists carry comments that intentionally quote the previous hexes to
 * record why they were replaced.
 */
function declaredAccentTones(css: string): string[] {
  return [...css.matchAll(/--ra-accent-tone-[a-z]+(?:-hover)?\s*:\s*#([0-9a-f]{6})\s*;/gi)]
    .map((match) => match[1].toLowerCase());
}

describe("accessibility", () => {
  it("permission selector opens via keyboard and is aria-labelled", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <PermissionSelector value="CONTROLLER_REVIEW" onChange={() => {}} />,
    );
    const trigger = screen.getByLabelText("权限配置");
    expect(trigger).toHaveAttribute("aria-haspopup", "listbox");
    trigger.focus();
    await user.keyboard("{Enter}");
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(
      screen.getByRole("listbox", { name: "权限配置" }),
    ).toBeInTheDocument();
  });

  it("sidebar nav items are keyboard reachable and labelled", () => {
    renderWithProviders(
      <div>
        <Sidebar
          onNewTask={() => {}}
          onOpenConversationPanel={() => {}}
          onConversationPanelClose={() => {}}
          conversationPanelOpen={false}
        />
      </div>,
    );
    const tasksLink = screen.getByTestId("sidebar-nav-任务");
    expect(tasksLink).toHaveAttribute("href", "/tasks");
    const homeLink = screen.getByTestId("sidebar-nav-首页");
    expect(homeLink).toHaveAttribute("href", "/");
    expect(screen.getByTestId("sidebar-nav-收件箱")).toHaveAttribute("href", "/inbox");
    expect(screen.getByTestId("sidebar-nav-路线图")).toHaveAttribute("href", "/roadmap");
    expect(screen.getByTestId("sidebar-nav-Agent 运行")).toHaveAttribute("href", "/runs");
    expect(screen.getByTestId("sidebar-nav-设置")).toHaveAttribute("href", "/settings");
  });

  it("custom policy editor traps focus (Tab cycles within dialog)", async () => {
    const user = userEvent.setup();
    const policy = profileToPolicy("CUSTOM");
    renderWithProviders(
      <CustomPolicyEditor
        open={true}
        policy={policy}
        onChange={() => {}}
        onClose={() => {}}
      />,
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    // Many focusable elements exist inside.
    const focusables = dialog.querySelectorAll(
      "button, input, select, textarea, [href], [tabindex]:not([tabindex='-1'])",
    );
    expect(focusables.length).toBeGreaterThan(2);
    // The first focusable should receive focus shortly after open.
    // Move focus explicitly and ensure Tab stays within the dialog.
    (focusables[0] as HTMLElement).focus();
    await user.tab();
    const activeAfterTab = document.activeElement as HTMLElement;
    expect(dialog.contains(activeAfterTab)).toBe(true);
  });

  it("collapsible section exposes aria-expanded", async () => {
    const user = userEvent.setup();
    const { CollapsibleSection } = await import("@/components/collapsible-section");
    renderWithProviders(
      <CollapsibleSection title="区块">
        <p data-testid="body">内容</p>
      </CollapsibleSection>,
    );
    const btn = screen.getByRole("button", { name: "区块" });
    expect(btn).toHaveAttribute("aria-expanded", "false");
    await user.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("body")).toBeInTheDocument();
  });

  it("keeps tertiary text at WCAG AA contrast on every surface it renders on", () => {
    const css = read("src/index.css");

    expect(css).not.toContain("--ra-text-tertiary: #77786f;");
    expect(css).toContain("--ra-text-tertiary: #66675f;");
    // #8f8e88 only reached 4.34:1 on the dark tertiary surface and 4.16:1 on
    // the dark input surface, where the task-detail tabs and the settings hint
    // text actually sit.
    expect(css).not.toContain("--ra-text-tertiary: #8f8e88;");
    expect(css).toContain("--ra-text-tertiary: #979690;");

    for (const surface of ["#fffefa", "#f1eee6", "#ece8de", "#ebe7dd", "#f7f4ed"]) {
      expect(contrastRatio("#66675f", surface)).toBeGreaterThanOrEqual(4.5);
    }
    for (const surface of ["#171816", "#232421", "#1d1e1c", "#1a1b19", "#2a2b27", "#2d2e2a"]) {
      expect(contrastRatio("#979690", surface)).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("keeps the light accent and status hues at WCAG AA contrast on every light surface", () => {
    const css = read("src/index.css");

    // The light accents were previously tuned against `--ra-base` only, so
    // #507f7a measured 3.65:1 and #2f7d50 4.08:1 on `--ra-tertiary`.
    // Compare against the *declared* tone values, not the raw file text: the
    // comments above each list deliberately quote the old hexes to explain why
    // they were replaced.
    expect(declaredAccentTones(css)).not.toContain("507f7a");
    // The light accent lives in the theme's tone list; `html[data-accent="…"]`
    // only points at it, so the literal must be asserted there.
    expect(css).toContain("--ra-accent-tone-cyan: #456e6a;");

    const lightSurfaces = ["#f1eee6", "#fffefa", "#ece8de", "#ebe7dd", "#f7f4ed"];
    for (const value of ["#456e6a", "#2b734a", "#8c5d12", "#a83c35", "#65665f"]) {
      for (const surface of lightSurfaces) {
        expect(contrastRatio(value, surface)).toBeGreaterThanOrEqual(4.5);
      }
    }
  });

  it("keeps every dark accent tone at WCAG AA contrast on every dark surface", () => {
    const css = read("src/index.css");

    // `text-ra-accent` is used for run state, activity verbs and inline links,
    // so each accent has to hold up as *text* on all six dark surfaces, not
    // just as a fill on the workspace. The original seeds were tuned against
    // the workspace alone: blue measured 4.10:1, violet 3.58:1 and rose
    // 3.93:1 on `--ra-input`.
    for (const stale of ["438cf4", "8a6cf1", "e45b72"]) {
      expect(declaredAccentTones(css), `${stale} must not survive as a dark accent`).not.toContain(stale);
    }

    const darkSurfaces = ["#171816", "#232421", "#1d1e1c", "#1a1b19", "#2a2b27", "#2d2e2a"];
    for (const value of ["#7ea7a2", "#5597f5", "#9e85f3", "#d88a19", "#e87185"]) {
      expect(css, `${value} must be declared as a dark accent tone`).toContain(value);
      for (const surface of darkSurfaces) {
        expect(
          contrastRatio(value, surface),
          `${value} on ${surface}`,
        ).toBeGreaterThanOrEqual(4.6);
      }
    }
  });

  it("does not ship an unlayered global reset that would defeat padding utilities", () => {
    const css = read("src/index.css");

    // An unlayered `* { margin: 0; padding: 0 }` outranks @layer utilities and
    // silently zeroed every px-*/py-* in the product. Tailwind's preflight
    // already provides the same reset inside @layer base.
    const normalized = css.replace(/\s+/g, " ");
    expect(normalized).not.toContain(
      "*::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }",
    );
    expect(css).toContain('@import "tailwindcss"');
  });

  it("keeps light error text at WCAG AA contrast on both light surfaces", () => {
    const css = read("src/index.css");

    expect(css).not.toContain("--ra-status-error: #b9473f;");
    expect(css).toContain("--ra-status-error: #a83c35;");
    expect(contrastRatio("#a83c35", "#fffefa")).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio("#a83c35", "#f1eee6")).toBeGreaterThanOrEqual(4.5);
  });
});
