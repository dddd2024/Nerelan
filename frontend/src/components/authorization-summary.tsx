import type { PolicyContract } from "@/types";
import { summarizePolicy } from "@/lib/policy-summary";

interface AuthorizationSummaryProps {
  policy: PolicyContract;
}

/**
 * Plain-language summary that updates as the form changes. Includes the
 * required disclaimer that real authorization is enforced server-side.
 */
export function AuthorizationSummary({ policy }: AuthorizationSummaryProps) {
  const summary = summarizePolicy(policy);
  return (
    <div
      data-testid="authorization-summary"
      className="rounded-lg border border-amber-200 bg-amber-50/60 p-4"
    >
      <h3 className="text-sm font-medium text-amber-800">
        授权摘要
      </h3>
      <p className="mt-2 text-sm text-slate-700" data-testid="authorization-summary-text">
        {summary}
      </p>
      <p className="mt-3 text-xs text-amber-700">
        此前端策略为委托请求。实际授权由服务端 Authority 系统执行。
      </p>
    </div>
  );
}
