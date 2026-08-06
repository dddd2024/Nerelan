import { cn } from "@/lib/cn";
import { ShieldCheck } from "lucide-react";

/**
 * OpenHands-style awaiting-approval page.
 * Source: OpenHands approves/inbox patterns (tag 1.8.0).
 * License: MIT.
 */
export function ApprovalsPage() {
  return (
    <div
      data-testid="approvals-page"
      className={cn(
        "px-0 pt-4 bg-transparent h-full flex flex-col",
        "rounded-xl lg:px-[42px] lg:pt-[42px]",
      )}
    >
      <div className="flex flex-col flex-1 min-h-0">
        <div className="flex items-center gap-2 mb-4">
          <ShieldCheck className="h-5 w-5 text-ra-accent" />
          <h1 className="text-lg font-semibold text-ra-text-secondary">
            审批
          </h1>
        </div>
        <p className="text-sm text-ra-text-tertiary">
          无待处理审批。
        </p>
      </div>
    </div>
  );
}
