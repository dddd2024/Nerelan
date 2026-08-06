import { cn } from "@/lib/cn";
import { Settings } from "lucide-react";

/**
 * OpenHands-style settings page.
 * Source: OpenHands settings-modal pattern (tag 1.8.0).
 * License: MIT.
 */
export function SettingsPage() {
  return (
    <div
      data-testid="settings-page"
      className={cn(
        "px-0 pt-4 bg-transparent h-full flex flex-col",
        "rounded-xl lg:px-[42px] lg:pt-[42px]",
      )}
    >
      <div className="flex flex-col flex-1 min-h-0">
        <div className="flex items-center gap-2 mb-4">
          <Settings className="h-5 w-5 text-ra-text-tertiary" />
          <h1 className="text-lg font-semibold text-ra-text-secondary">
            设置
          </h1>
        </div>
        <p className="text-sm text-ra-text-tertiary">
          配置页面正在开发中。
        </p>
      </div>
    </div>
  );
}
