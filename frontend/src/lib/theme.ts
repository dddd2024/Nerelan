export const APPEARANCE_STORAGE_KEY = "nerelan.appearance";
export const LEGACY_APPEARANCE_STORAGE_KEY = "reverse-agent.appearance";

export const THEME_MODES = ["system", "light", "dark"] as const;
export type ThemeMode = (typeof THEME_MODES)[number];

export const ACCENTS = ["cyan", "blue", "violet", "amber", "rose"] as const;
export type Accent = (typeof ACCENTS)[number];

export interface Appearance {
  mode: ThemeMode;
  accent: Accent;
}

export const DEFAULT_APPEARANCE: Appearance = {
  mode: "system",
  accent: "cyan",
};

function defaultStorage(): Storage | undefined {
  try {
    return globalThis.localStorage;
  } catch {
    return undefined;
  }
}

const modeLabels: Record<ThemeMode, string> = {
  system: "跟随系统",
  light: "浅色",
  dark: "深色",
};

const accentLabels: Record<Accent, string> = {
  cyan: "青色",
  blue: "蓝色",
  violet: "紫色",
  amber: "琥珀",
  rose: "玫瑰",
};

/**
 * Preview swatch for the accent picker.
 *
 * These must be the colours the chosen accent will actually render, and an
 * accent resolves to a *different* value per theme (e.g. cyan is #7ea7a2 in
 * dark and #456e6a in light). The swatches therefore read the theme-scoped
 * `--ra-swatch-*` tokens from `index.css` instead of hardcoding hexes: the old
 * hardcoded set advertised #18c6cf for "青色", a colour no theme ever painted.
 */
const accentSwatches: Record<Accent, string> = {
  cyan: "var(--ra-swatch-cyan)",
  blue: "var(--ra-swatch-blue)",
  violet: "var(--ra-swatch-violet)",
  amber: "var(--ra-swatch-amber)",
  rose: "var(--ra-swatch-rose)",
};

export function themeModeLabel(mode: ThemeMode): string {
  return modeLabels[mode];
}

export function accentLabel(accent: Accent): string {
  return accentLabels[accent];
}

export function accentSwatch(accent: Accent): string {
  return accentSwatches[accent];
}

function isThemeMode(value: unknown): value is ThemeMode {
  return typeof value === "string" && THEME_MODES.includes(value as ThemeMode);
}

function isAccent(value: unknown): value is Accent {
  return typeof value === "string" && ACCENTS.includes(value as Accent);
}

export function normalizeAppearance(value: unknown): Appearance {
  if (!value || typeof value !== "object") return { ...DEFAULT_APPEARANCE };
  const candidate = value as Partial<Appearance>;
  return {
    mode: isThemeMode(candidate.mode) ? candidate.mode : DEFAULT_APPEARANCE.mode,
    accent: isAccent(candidate.accent) ? candidate.accent : DEFAULT_APPEARANCE.accent,
  };
}

export function readAppearance(storage?: Storage): Appearance {
  try {
    const activeStorage = storage ?? defaultStorage();
    const raw = activeStorage?.getItem(APPEARANCE_STORAGE_KEY);
    if (raw) return normalizeAppearance(JSON.parse(raw));

    const legacyRaw = activeStorage?.getItem(LEGACY_APPEARANCE_STORAGE_KEY);
    if (!legacyRaw) return { ...DEFAULT_APPEARANCE };

    const migrated = normalizeAppearance(JSON.parse(legacyRaw));
    try {
      activeStorage?.setItem(APPEARANCE_STORAGE_KEY, JSON.stringify(migrated));
      activeStorage?.removeItem(LEGACY_APPEARANCE_STORAGE_KEY);
    } catch {
      // Keeping the user's existing preference matters more than retiring the key.
    }
    return migrated;
  } catch {
    return { ...DEFAULT_APPEARANCE };
  }
}

export function applyAppearance(
  appearance: Appearance,
  root: HTMLElement = document.documentElement,
): void {
  root.dataset.theme = appearance.mode;
  root.dataset.accent = appearance.accent;
  root.style.colorScheme = appearance.mode === "system" ? "light dark" : appearance.mode;
}

export function persistAppearance(
  appearance: Appearance,
  storage?: Storage,
): void {
  try {
    (storage ?? defaultStorage())?.setItem(
      APPEARANCE_STORAGE_KEY,
      JSON.stringify(normalizeAppearance(appearance)),
    );
  } catch {
    // Presentation preferences are best-effort and never block the workspace.
  }
}

export function setAppearance(
  appearance: Appearance,
  root: HTMLElement = document.documentElement,
  storage?: Storage,
): Appearance {
  const normalized = normalizeAppearance(appearance);
  applyAppearance(normalized, root);
  persistAppearance(normalized, storage);
  return normalized;
}

export function initializeAppearance(
  root: HTMLElement = document.documentElement,
  storage?: Storage,
): Appearance {
  const appearance = readAppearance(storage);
  applyAppearance(appearance, root);
  return appearance;
}
