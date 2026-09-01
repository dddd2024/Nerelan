import { Check, Laptop, Moon, Sun } from "lucide-react";
import { useState } from "react";
import {
  ACCENTS,
  type Accent,
  type Appearance,
  setAppearance,
  themeModeLabel,
  accentLabel,
  accentSwatch,
  readAppearance,
  type ThemeMode,
} from "@/lib/theme";
import { cn } from "@/lib/cn";

const modeIcons: Record<ThemeMode, typeof Laptop> = {
  system: Laptop,
  light: Sun,
  dark: Moon,
};

const modeDescriptions: Record<ThemeMode, string> = {
  system: "根据设备的外观自动切换",
  light: "适合明亮环境的清晰表面",
  dark: "适合长时间工作的低噪声表面",
};

export function ThemeSelector() {
  const [appearance, setAppearanceState] = useState<Appearance>(() => readAppearance());

  function update(next: Partial<Appearance>) {
    setAppearanceState((current) => setAppearance({ ...current, ...next }));
  }

  return (
    <section
      aria-labelledby="appearance-heading"
      data-testid="theme-selector"
      className="border-t border-ra-border/60 py-4"
    >
      <div>
        <h2 id="appearance-heading" className="text-sm font-semibold text-ra-text">
          外观
        </h2>
        <p className="mt-1 max-w-xl text-xs leading-5 text-ra-text-tertiary">
          仅保存本设备的显示偏好，不会影响任务、权限或执行状态。
        </p>
      </div>

      <fieldset className="mt-3">
        <legend className="text-xs font-medium text-ra-text-secondary">主题模式</legend>
        <div role="radiogroup" aria-label="主题模式" className="mt-1.5 grid gap-1 sm:grid-cols-3">
          {(["system", "light", "dark"] as ThemeMode[]).map((mode) => {
            const Icon = modeIcons[mode];
            const selected = appearance.mode === mode;
            return (
              <label
                key={mode}
                htmlFor={`theme-option-${mode}`}
                className={cn(
                  "flex min-h-11 items-center gap-2 rounded-md px-2.5 py-2 text-left transition-colors",
                  "focus-within:ring-2 focus-within:ring-ra-accent focus-within:ring-offset-2 focus-within:ring-offset-ra-light",
                  selected
                    ? "bg-ra-tertiary text-ra-text"
                    : "text-ra-text-secondary hover:bg-ra-tertiary/70",
                )}
              >
                <input
                  id={`theme-option-${mode}`}
                  type="radio"
                  name="theme-mode"
                  value={mode}
                  checked={selected}
                  onChange={() => update({ mode })}
                  data-testid={`theme-option-${mode}`}
                  className="sr-only"
                />
                <Icon className="h-4 w-4 shrink-0 text-ra-text-tertiary" aria-hidden="true" />
                <span className="min-w-0 flex-1">
                  <span className="block text-xs font-medium">{themeModeLabel(mode)}</span>
                  <span className="mt-0.5 block text-[11px] leading-4 text-ra-text-tertiary">
                    {modeDescriptions[mode]}
                  </span>
                </span>
                {selected && <Check className="h-4 w-4 shrink-0 text-ra-accent" aria-hidden="true" />}
              </label>
            );
          })}
        </div>
      </fieldset>

      <fieldset className="mt-3 border-t border-ra-border/50 pt-3">
        <legend className="text-xs font-medium text-ra-text-secondary">强调色</legend>
        <div role="radiogroup" aria-label="强调色" className="mt-1.5 flex flex-wrap gap-1">
          {ACCENTS.map((accent: Accent) => {
            const selected = appearance.accent === accent;
            return (
              <label
                key={accent}
                htmlFor={`accent-option-${accent}`}
                className={cn(
                  "group inline-flex items-center gap-2 rounded-md px-2 py-1.5 text-xs transition-colors",
                  "focus-within:ring-2 focus-within:ring-ra-accent focus-within:ring-offset-2 focus-within:ring-offset-ra-light",
                  selected
                    ? "bg-ra-tertiary text-ra-text"
                    : "text-ra-text-secondary hover:bg-ra-tertiary/70",
                )}
              >
                <input
                  id={`accent-option-${accent}`}
                  type="radio"
                  name="accent"
                  value={accent}
                  checked={selected}
                  onChange={() => update({ accent })}
                  data-testid={`accent-option-${accent}`}
                  className="sr-only"
                />
                <span
                  className="h-3 w-3 rounded-full ring-1 ring-inset ring-black/20"
                  style={{ backgroundColor: accentSwatch(accent) }}
                  aria-hidden="true"
                />
                {accentLabel(accent)}
                {selected && <Check className="h-3.5 w-3.5 text-ra-accent" aria-hidden="true" />}
              </label>
            );
          })}
        </div>
      </fieldset>
    </section>
  );
}
