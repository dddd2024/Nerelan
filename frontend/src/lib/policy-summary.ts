import type { PolicyContract } from "@/types";
import { formatClock } from "@/lib/format";

/**
 * Generate a plain-language authorization summary from a PolicyContract.
 *
 * Example target output:
 *   "截至 08:00，主控仅在 dddd2024/reverse-agent 中工作，创建最多 3 个
 *    PR，merge 最多 2 个 PR 到 main 在 pytest, ci 通过后、Decision
 *    Preflight 和 State Gate 在精确 Head 上通过，创建 一 个 GitHub
 *    Release。不允许生产部署。"
 */
export function summarizePolicy(policy: PolicyContract): string {
  const window = policy.autonomousWindow;
  const until = window.enabled ? `截至 ${formatClock(window.expiresAt)}` : "未启用无人值守窗口时";
  const repo = `仅在 ${policy.repository} 中工作`;

  const mergeRepos = policy.mergePolicy.allowedRepositories.length
    ? `，merge 仓库：${policy.mergePolicy.allowedRepositories.join("，")}`
    : "";

  const grants: string[] = [];

  if (policy.githubCapabilities.includes("open_draft_pr")) {
    grants.push(
      `创建最多 ${policy.budgets.maxPrsOpened} 个 PR${plural(policy.budgets.maxPrsOpened)}`,
    );
  }

  if (policy.githubCapabilities.includes("merge_pr")) {
    const methods = policy.mergePolicy.allowedMergeMethods.length;
    const methodWord = methods > 1 ? "merge" : (policy.mergePolicy.allowedMergeMethods[0] ?? "merge");
    const after = policy.mergePolicy.requiredChecks.length
      ? ` 在 ${policy.mergePolicy.requiredChecks.join("，")} 通过后`
      : "";
    const exact = policy.mergePolicy.requireExactHead
      ? "、Decision Preflight 和 State Gate 在精确 Head 上通过"
      : "";
    grants.push(
      `${methodWord} 最多 ${policy.budgets.maxMergesToMain} 个 PR${plural(policy.budgets.maxMergesToMain)} 到 main${after}${exact}`,
    );
  }

  const releaseCapable = policy.publicationCapabilities.includes(
    "create_github_release",
  );
  if (releaseCapable) {
    const n = policy.budgets.maxReleasesCreated;
    grants.push(`创建 ${countWord(n)} 个 GitHub Release${plural(n)}`);
  }

  const deployProd = policy.publicationCapabilities.includes(
    "deploy_production",
  );
  const deployStaging = policy.publicationCapabilities.includes(
    "deploy_staging",
  );
  const deployPreview = policy.publicationCapabilities.includes(
    "deploy_preview",
  );

  const deployment = deployProd
    ? "允许生产部署"
    : "不允许生产部署";

  const grantClause = grants.length ? grants.join("，") + "，并" : "";
  const releaseClause = releaseCapable ? "" : "";
  void releaseClause;

  const parts = [until, "主控可", repo];
  if (grantClause) parts.push(grantClause.replace(/，并$/, ""));
  parts.push(`。${deployment}。`);

  // Compose final sentence, ensuring the example shape.
  const intro = `${until}，主控${repo}`;
  const mergeClause = mergeRepos ? `${mergeRepos}` : "";
  const tail = grants.length ? `，${grants.join("，")}` : "";
  const closing = `。${deployment}。`;
  const extras =
    deployStaging || deployPreview
      ? ` 非生产部署目标：${[deployPreview ? "预览" : null, deployStaging ? "预发" : null].filter(Boolean).join("，")}。`
      : "";

  void parts;
  return `${intro}${mergeClause}${tail}${closing}${extras}`.replace(/\s+。/g, "。").replace(/， 。/g, "。");
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function plural(n: number): string {
  return n === 1 ? "" : "s";
}

function countWord(n: number): string {
  if (n === 1) return "一";
  if (n === 2) return "二";
  if (n === 3) return "三";
  return String(n);
}
