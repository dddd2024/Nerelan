import { readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { ACCENTS, accentSwatch } from "@/lib/theme";

/**
 * The accent picker must preview the accent the product will actually render.
 *
 * This broke once already: `accentSwatch()` returned hardcoded saturated hexes
 * (#18c6cf for "青色") while `--ra-accent` resolved to #7ea7a2 in dark and
 * #456e6a in light, so the picker advertised a colour the UI then contradicted.
 *
 * The fix made the class of defect structurally impossible instead of
 * test-enforced: every accent now has exactly one `--ra-accent-tone-*` per
 * theme, `html[data-accent="…"]` only *points* at it, and `--ra-swatch-*`
 * aliases the same name. These tests assert that structure, so a future edit
 * that reintroduces a second hardcoded list fails here.
 */

const CSS = readFileSync(resolve(__dirname, "../src/index.css"), "utf8");

/** Body of a block whose selector matches, stopping at the first column-0 `}`.
 *  Safe here because none of the targeted blocks nest a rule. */
function blockBody(re: RegExp, label: string): string {
  const m = CSS.match(re);
  if (!m) throw new Error(`could not locate the ${label} block in index.css`);
  return m[1];
}

const ROOT = blockBody(/:root\s*\{([\s\S]*?)\n\}/, ":root");
const LIGHT = blockBody(
  /html\[data-theme="light"\],\s*\n?\s*html\[data-theme="system"\]\s*\{([\s\S]*?)\n\}/,
  "light palette",
);
const SYSTEM_DARK = blockBody(
  /@media \(prefers-color-scheme: dark\)\s*\{\s*html\[data-theme="system"\]\s*\{([\s\S]*?)\n {2}\}/,
  "system dark palette",
);

const value = (body: string, name: string): string | undefined =>
  body.match(new RegExp(`${name}\\s*:\\s*([^;]+);`))?.[1].trim();

describe("accent tokens own the picker swatch", () => {
  it("gives every accent one tone per theme and no literal --ra-accent hexes", () => {
    for (const accent of ACCENTS) {
      const tone = `--ra-accent-tone-${accent}`;
      for (const [label, body] of [
        [":root", ROOT],
        ["light palette", LIGHT],
        ["system dark palette", SYSTEM_DARK],
      ] as const) {
        expect(
          value(body, tone),
          `${label} must define ${tone} as a hex value`,
        ).toMatch(/^#[0-9a-f]{6}$/i);
      }
    }

    // The whole point: a literal accent hex outside the three tone lists would
    // mean two sources of truth again.
    for (const body of [ROOT, LIGHT, SYSTEM_DARK]) {
      const literal = value(body, `--ra-accent`) ?? "";
      expect(literal).not.toMatch(/^#[0-9a-f]{6}$/i);
    }
  });

  it("points the accent and its hover state at the matching tone", () => {
    for (const accent of ACCENTS) {
      const m = CSS.match(
        new RegExp(
          `html\\[data-accent="${accent}"\\]\\s*\\{([\\s\\S]*?)\\n\\}`,
        ),
      );
      expect(m, `html[data-accent="${accent}"] must exist`).not.toBeNull();
      const body = m![1].trim();
      expect(value(body, "--ra-accent")).toBe(`var(--ra-accent-tone-${accent})`);
      expect(value(body, "--ra-accent-hover")).toBe(
        `var(--ra-accent-tone-${accent}-hover)`,
      );
    }
  });

  it("aliases every picker swatch to the accent tone rather than a hex", () => {
    for (const accent of ACCENTS) {
      expect(
        value(ROOT, `--ra-swatch-${accent}`),
        `:root must alias --ra-swatch-${accent} to the tone`,
      ).toBe(`var(--ra-accent-tone-${accent})`);
      expect(accentSwatch(accent)).toBe(`var(--ra-swatch-${accent})`);
    }
  });
});

/**
 * Every saturated colour on screen must come from `index.css`.
 *
 * `index.css` already documents why this matters: a hardcoded
 * `rgba(0,0,0,.16)` panel shadow "disappeared entirely in dark mode", so the
 * shadow family moved to `--ra-shadow-*`. A literal survived in the sidebar's
 * "更多" popover (`rgba(0,0,0,.12)`), which both contradicted its sibling
 * popovers that use `--ra-shadow-2` and painted a neutral-black shadow in a
 * light theme whose shadows are warm (`rgb(31 30 26 / 0.10)`).
 *
 * The scan is deliberately zero-allowlist: the design tokens live in
 * `index.css` (CSS, not scanned) and `--ra-*` is the only way a component may
 * name a colour. Comments are stripped first so an upstream-port note that
 * *quotes* a retired literal does not read as a live one, and issue references
 * such as `#448` are not matched because the pattern requires six digits.
 */
function sourceFiles(dir: string, found: string[] = []): string[] {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    // Vendored upstream code is not ours to re-tokenise.
    if (entry.isDirectory()) {
      if (entry.name !== "vendor") sourceFiles(full, found);
    } else if (/\.tsx?$/.test(entry.name)) {
      found.push(full);
    }
  }
  return found;
}

const LITERAL_COLOUR = /#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?\b|\brgba?\(|\bhsla?\(/g;

describe("component surfaces name colours only through tokens", () => {
  it("keeps every literal colour out of src/", () => {
    const strip = (source: string) =>
      source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^[ \t]*\/\/.*$/gm, "");

    const offenders: string[] = [];
    for (const file of sourceFiles(resolve(__dirname, "../src"))) {
      const lines = strip(readFileSync(file, "utf8")).split("\n");
      lines.forEach((line, index) => {
        const hits = line.match(LITERAL_COLOUR);
        if (hits) {
          offenders.push(
            `${file
              .slice(file.indexOf("src"))
              .replace(/\\/g, "/")}:${index + 1} -> ${hits.join(", ")}`,
          );
        }
      });
    }

    expect(
      offenders,
      "use a --ra-* token (or a var(--ra-shadow-*) composite) instead of a literal colour",
    ).toEqual([]);
  });
});
