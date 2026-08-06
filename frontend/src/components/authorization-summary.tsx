import type { PolicyContract } from "@/types";
import { summarizePolicy } from "@/lib/policy-summary";
import { AlertTriangle } from "lucide-react";

interface AuthorizationSummaryProps {
  policy: PolicyContract;
}

/**
 * OpenHands-style authorization summary.
 * Styled as an alert banner using OpenHands amber/alert color scheme
 * (amber-200/amber-50 from OpenHands index.css alert patterns).
 */
export function AuthorizationSummary({ policy }: AuthorizationSummaryProps) {
  const summary = summarizePolicy(policy);
  return (
    <div
      data-testid="authorization-summary"
      className="rounded-lg border border-[#FFD43B]/30 bg-[#FFD43B]/10 p-4"
    >
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-[#FFD43B]" />
        <h3 className="text-sm font-medium text-[#FFD43B]">授权摘要</h3>
      </div>
      <p
        className="mt-2 text-sm text-ra-text-secondary"
        data-testid="authorization-summary-text"
      >
        {summary}
      </p>
      <p className="mt-3 text-xs text-ra-text-tertiary">
        此前端策略为委托请求。实际授权由服务端 Authority 系统执行。
      </p>
    </div>
  );
}
