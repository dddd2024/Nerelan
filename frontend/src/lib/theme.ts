export const APPEARANCE_STORAGE_KEY = "reverse-agent.appearance";

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

const accentSwatches: Record<Accent, string> = {
  cyan: "#18c6cf",
  blue: "#438cf4",
  violet: "#8a6cf1",
  amber: "#d88a19",
  rose: "#e45b72",
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
    const raw = (storage ?? defaultStorage())?.getItem(APPEARANCE_STORAGE_KEY);
    return raw ? normalizeAppearance(JSON.parse(raw)) : { ...DEFAULT_APPEARANCE };
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
