import type { PlatformGoal } from "@/lib/platform-client";
import { quotaFitText, type QuotaFit } from "@/lib/goal-labels";

type PlanTask = PlatformGoal["tasks"][number];

function checksText(task: PlanTask): string {
  const checks = task.validation_checks ?? [];
  if (checks.length === 0) return "没有选择功能检查：只检查补丁格式，不能证明功能正确。";
  return `功能检查：${checks.map((check) => {
    const targets = check.targets?.length ? `，针对 ${check.targets.join("、")}` : "";
    return `${check.profile_id}（在 ${check.working_directory || "仓库根目录"}${targets}）`;
  }).join("；")}`;
}

/**
 * The plan as numbered steps in the Owner's language, built from the goal's
 * structured tasks. The stored Markdown stays the approved artifact; it is
 * shown folded underneath for anyone who wants the exact text.
 */
export function PlanSteps({ goal }: { goal: PlatformGoal & { quota_fit?: QuotaFit | null } }) {
  const order = new Map(goal.tasks.map((task, index) => [task.id, index + 1]));
  const quota = quotaFitText(goal.quota_fit);
  return (
    <div data-testid="approval-plan" className="ra-measure mt-2 space-y-3">
      {goal.tasks.length === 0 ? (
        <p className="text-sm text-ra-text-secondary">当前目标还没有可显示的计划步骤。</p>
      ) : (
        <ol className="space-y-3">
          {goal.tasks.map((task, index) => {
            const after = task.dependencies.map((id) => (order.has(id) ? `第 ${order.get(id)} 步` : id));
            return (
              <li key={task.id} data-testid={`plan-step-${task.id}`} className="rounded-xl border border-ra-border bg-ra-light/30 p-4">
                <p className="text-sm font-medium text-ra-text">
                  <span className="mr-2 text-ra-text-tertiary">第 {index + 1} 步</span>{task.title}
                </p>
                {task.instruction ? (
                  <p className="mt-2 whitespace-pre-line text-sm leading-6 text-ra-text-secondary">{task.instruction}</p>
                ) : null}
                <ul className="mt-2 space-y-1 text-xs leading-5 text-ra-text-tertiary">
                  <li>{after.length ? `在${after.join("、")}之后进行` : "可以最先开始"}</li>
                  <li>{checksText(task)}</li>
                </ul>
              </li>
            );
          })}
        </ol>
      )}
      {quota ? <p data-testid="approval-quota-fit" className="text-xs text-ra-text-secondary">{quota} 这只是预测，不会预留额度。</p> : null}
      {goal.plan_markdown ? (
        <details className="text-xs text-ra-text-tertiary">
          <summary className="cursor-pointer select-none hover:text-ra-text-secondary">查看原始计划文本</summary>
          <pre data-testid="approval-plan-markdown" className="mt-2 whitespace-pre-wrap rounded-lg border border-ra-border p-3 font-mono text-xs leading-5">
            {goal.plan_markdown}
          </pre>
        </details>
      ) : null}
    </div>
  );
}
