import type { PolicyContract } from "@/types";
import { formatClock } from "@/lib/format";

/**
 * Generate a plain-language authorization summary from a PolicyContract.
 *
 * Example target output:
 *   "Until 08:00, the controller may work only in dddd2024/reverse-agent,
 *    create up to 3 PRs, merge up to 2 PRs into main after CI, Decision
 *    Preflight and State Gate pass on the exact head, and create one GitHub
 *    Release. Production deployment is not allowed."
 */
export function summarizePolicy(policy: PolicyContract): string {
  const window = policy.autonomousWindow;
  const until = window.enabled ? `Until ${formatClock(window.expiresAt)}` : "Without an unattended window";
  const repo = `work only in ${policy.repository}`;

  const grants: string[] = [];

  if (policy.githubCapabilities.includes("open_draft_pr")) {
    grants.push(
      `create up to ${policy.budgets.maxPrsOpened} PR${plural(policy.budgets.maxPrsOpened)}`,
    );
  }

  if (policy.githubCapabilities.includes("merge_pr")) {
    const methods = policy.mergePolicy.allowedMergeMethods.length;
    const methodWord = methods > 1 ? "merge" : (policy.mergePolicy.allowedMergeMethods[0] ?? "merge");
    const after = policy.mergePolicy.requiredChecks.length
      ? ` after ${policy.mergePolicy.requiredChecks.join(", ")}`
      : "";
    const exact = policy.mergePolicy.requireExactHead
      ? ", Decision Preflight and State Gate pass on the exact head"
      : "";
    grants.push(
      `${methodWord} up to ${policy.budgets.maxMergesToMain} PR${plural(policy.budgets.maxMergesToMain)} into main${after}${exact}`,
    );
  }

  const releaseCapable = policy.publicationCapabilities.includes(
    "create_github_release",
  );
  if (releaseCapable) {
    const n = policy.budgets.maxReleasesCreated;
    grants.push(`create ${countWord(n)} GitHub Release${plural(n)}`);
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
    ? "Production deployment is allowed"
    : "Production deployment is not allowed";

  const grantClause = grants.length ? grants.join(", ") + ", and " : "";
  const releaseClause = releaseCapable ? "" : "";
  void releaseClause;

  const parts = [until, "the controller may", repo];
  if (grantClause) parts.push(grantClause.replace(/, and $/, ""));
  parts.push(`. ${deployment}.`);

  if (deployStaging || deployPreview) {
    const envs: string[] = [];
    if (deployPreview) envs.push("preview");
    if (deployStaging) envs.push("staging");
    parts.push(` Non-production deploy targets: ${envs.join(", ")}.`);
  }

  // Compose final sentence, ensuring the example shape.
  const intro = `${until}, the controller may ${repo}`;
  const tail = grants.length ? `, ${grants.join(", ")}` : "";
  const closing = `. ${deployment}.`;
  const extras =
    deployStaging || deployPreview
      ? ` Non-production deploy targets: ${[deployPreview ? "preview" : null, deployStaging ? "staging" : null].filter(Boolean).join(", ")}.`
      : "";

  void parts;
  return `${intro}${tail}${closing}${extras}`.replace(/\s+\./g, ".").replace(/, \./g, ".");
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function plural(n: number): string {
  return n === 1 ? "" : "s";
}

function countWord(n: number): string {
  if (n === 1) return "one";
  if (n === 2) return "two";
  if (n === 3) return "three";
  return String(n);
}
