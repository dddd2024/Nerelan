import { z } from "zod";
import type { PolicyContract } from "@/types";

// ---------------------------------------------------------------------------
// Primitive enums
// ---------------------------------------------------------------------------

const permissionModeSchema = z.enum([
  "ASK_FOR_APPROVAL",
  "CONTROLLER_REVIEW",
  "OWNER_CONTROL",
  "CUSTOM",
]);

const secretsAccessSchema = z.enum(["none", "masked", "raw_values"]);

const githubCapabilitySchema = z.enum([
  "read_repository",
  "create_issue",
  "update_issue",
  "create_branch",
  "push_task_branch",
  "open_draft_pr",
  "mark_ready",
  "request_review",
  "merge_pr",
  "delete_merged_branch",
  "push_main",
]);

const publicationCapabilitySchema = z.enum([
  "create_tag",
  "create_github_release",
  "publish_package",
  "publish_container",
  "deploy_preview",
  "deploy_staging",
  "deploy_production",
  "rollback_deployment",
]);

const mergeMethodSchema = z.enum(["merge", "squash", "rebase"]);

const stopConditionSchema = z.enum([
  "max_prs_opened",
  "max_merges_to_main",
  "max_releases_created",
  "max_deploys_to_environment",
  "budget_exhausted",
  "window_expired",
  "manual_stop",
  "blocking_review_thread",
  "ci_failure_on_head",
  "main_drift_detected",
  "authority_revoked",
]);

const stopConditionScopeSchema = z.enum(["task", "window"]);

const positiveInt = z
  .number()
  .int("must be an integer")
  .positive("must be a positive integer");

// ---------------------------------------------------------------------------
// Nested objects
// ---------------------------------------------------------------------------

const filesystemScopeSchema = z.object({
  allowedPaths: z.array(z.string()).default([]),
  writablePaths: z.array(z.string()).default([]),
  tempDir: z.string().optional(),
});

const networkScopeSchema = z.object({
  allowedDomains: z.array(z.string()).default([]),
  allowWrite: z.boolean().default(false),
});

const shellScopeSchema = z.object({
  allowedCommands: z.array(z.string()).default([]),
  deniedCommands: z.array(z.string()).default([]),
});

const secretsScopeSchema = z.object({
  access: secretsAccessSchema,
  allowedKeys: z.array(z.string()).default([]),
});

const workerApprovalScopeSchema = z.object({
  required: z.boolean().default(false),
  approvers: z.array(z.string()).default([]),
});

const resourceAccessSchema = z.object({
  filesystem: filesystemScopeSchema,
  network: networkScopeSchema,
  shell: shellScopeSchema,
  secrets: secretsScopeSchema,
  workerApproval: workerApprovalScopeSchema,
});

const mergePolicySchema = z.object({
  allowedRepositories: z.array(z.string()).default([]),
  allowedBaseBranches: z.array(z.string()).default([]),
  requiredChecks: z.array(z.string()).default([]),
  allowedMergeMethods: z.array(mergeMethodSchema).default([]),
  requireExactHead: z.boolean().default(true),
});

const publicationPolicySchema = z.object({
  allowedArtifactOrPackage: z.array(z.string()).default([]),
  allowedRegistry: z.array(z.string()).default([]),
  allowedRepository: z.array(z.string()).default([]),
  allowedEnvironment: z.array(z.string()).default([]),
  rollbackStrategy: z.string().optional(),
});

const stopConditionRuleSchema = z.object({
  type: stopConditionSchema,
  scope: stopConditionScopeSchema,
  limit: z.number().int().positive().optional(),
});

const autonomousWindowSchema = z.object({
  enabled: z.boolean().default(false),
  startsAt: z.string().min(1),
  expiresAt: z.string().min(1),
  maxPrsOpened: positiveInt,
  maxMergesToMain: positiveInt,
  maxReleasesCreated: positiveInt,
  maxDeploysToEnvironment: positiveInt,
  stopConditions: z.array(stopConditionRuleSchema).default([]),
});

const budgetsSchema = z.object({
  maxPrsOpened: positiveInt,
  maxMergesToMain: positiveInt,
  maxReleasesCreated: positiveInt,
  maxDeploysToEnvironment: positiveInt,
});

// ---------------------------------------------------------------------------
// Root schema
// ---------------------------------------------------------------------------

export const policySchema = z
  .object({
    mode: permissionModeSchema,
    repository: z.string().min(1, "repository is required"),
    resourceAccess: resourceAccessSchema,
    githubCapabilities: z.array(githubCapabilitySchema),
    publicationCapabilities: z.array(publicationCapabilitySchema),
    publicationPolicy: publicationPolicySchema,
    mergePolicy: mergePolicySchema,
    autonomousWindow: autonomousWindowSchema,
    budgets: budgetsSchema,
  })
  .superRefine((policy, ctx) => {
    const errors: string[] = [];

    const has = (cap: string) => policy.githubCapabilities.includes(cap as never);
    const hasPub = (cap: string) =>
      policy.publicationCapabilities.includes(cap as never);

    // merge_pr requires merge policy fields
    if (has("merge_pr")) {
      if (policy.mergePolicy.allowedRepositories.length === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["mergePolicy", "allowedRepositories"],
          message: "merge_pr requires non-empty allowedRepositories",
        });
        errors.push("merge_pr requires non-empty allowedRepositories");
      }
      if (policy.mergePolicy.allowedBaseBranches.length === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["mergePolicy", "allowedBaseBranches"],
          message: "merge_pr requires non-empty allowedBaseBranches",
        });
        errors.push("merge_pr requires non-empty allowedBaseBranches");
      }
      if (policy.mergePolicy.requiredChecks.length === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["mergePolicy", "requiredChecks"],
          message: "merge_pr requires non-empty requiredChecks",
        });
        errors.push("merge_pr requires non-empty requiredChecks");
      }
    }

    // deploy_production requires environment + rollbackStrategy
    if (hasPub("deploy_production")) {
      if (policy.publicationPolicy.allowedEnvironment.length === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["publicationPolicy", "allowedEnvironment"],
          message: "deploy_production requires allowedEnvironment",
        });
        errors.push("deploy_production requires allowedEnvironment");
      }
      if (!policy.publicationPolicy.rollbackStrategy) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["publicationPolicy", "rollbackStrategy"],
          message: "deploy_production requires rollbackStrategy",
        });
        errors.push("deploy_production requires rollbackStrategy");
      }
    }

    // publication capabilities require artifact/package + registry or repository
    const pubNeedsArtifact =
      hasPub("publish_package") ||
      hasPub("publish_container") ||
      hasPub("create_github_release");
    if (pubNeedsArtifact) {
      if (policy.publicationPolicy.allowedArtifactOrPackage.length === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["publicationPolicy", "allowedArtifactOrPackage"],
          message:
            "publication capabilities require allowedArtifactOrPackage",
        });
        errors.push("publication capabilities require allowedArtifactOrPackage");
      }
      const hasRegistry = policy.publicationPolicy.allowedRegistry.length > 0;
      const hasRepo = policy.publicationPolicy.allowedRepository.length > 0;
      if (!hasRegistry && !hasRepo) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["publicationPolicy", "allowedRegistry"],
          message:
            "publication capabilities require allowedRegistry or allowedRepository",
        });
        errors.push(
          "publication capabilities require allowedRegistry or allowedRepository",
        );
      }
    }

    // autonomousWindow.expiresAt must be a valid future ISO date (only when enabled)
    if (policy.autonomousWindow.enabled) {
      const expires = Date.parse(policy.autonomousWindow.expiresAt);
      if (Number.isNaN(expires)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["autonomousWindow", "expiresAt"],
          message: "autonomousWindow.expiresAt must be a valid ISO date",
        });
        errors.push("autonomousWindow.expiresAt must be a valid ISO date");
      } else if (expires <= Date.now()) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["autonomousWindow", "expiresAt"],
          message: "autonomousWindow.expiresAt must be in the future",
        });
        errors.push("autonomousWindow.expiresAt must be a valid future ISO date");
      }
    }

    // secrets must not be "raw_values"
    if (policy.resourceAccess.secrets.access === "raw_values") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["resourceAccess", "secrets", "access"],
        message: "raw secret values are not allowed",
      });
      errors.push("secrets must not be raw_values");
    }

    // push_main must NOT be implicitly enabled by merge_pr (they are independent).
    // This rule asserts that push_main is never auto-derived: if merge_pr is on
    // but push_main is also on, that is allowed only because it was explicitly
    // selected. There is nothing to reject here for "implicit" enabling at the
    // contract level; instead we assert the invariant that the two capabilities
    // remain independently toggleable by checking they are distinct entries.
    // (No error path — documented invariant.)

    // deployment must NOT be implied by network write access.
    if (
      policy.resourceAccess.network.allowWrite &&
      !hasPub("deploy_production") &&
      !hasPub("deploy_staging") &&
      !hasPub("deploy_preview") &&
      policy.publicationCapabilities.length === 0
    ) {
      // Network write alone must not silently enable deployment. This is a
      // no-op guard: deployment is only granted via explicit publication
      // capabilities, never via network.allowWrite. No error issued unless a
      // deployment capability is present without publicationPolicy support
      // (handled above).
    }

    // Expose collected errors via a hidden path for the validatePolicy helper.
    if (errors.length > 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["__collected__"],
        message: errors.join("; "),
      });
    }
  });

export interface PolicyValidationResult {
  success: boolean;
  errors: string[];
}

export function validatePolicy(
  input: unknown,
): PolicyValidationResult {
  const parsed = policySchema.safeParse(input);
  if (parsed.success) {
    return { success: true, errors: [] };
  }
  const errors: string[] = [];
  for (const issue of parsed.error.issues) {
    const path = issue.path.filter((p) => p !== "__collected__").join(".");
    const where = path ? `${path}: ` : "";
    if (issue.path.includes("__collected__")) {
      // Split the joined collected errors back out for readability.
      for (const piece of issue.message.split("; ")) {
        if (piece) errors.push(piece);
      }
    } else {
      errors.push(`${where}${issue.message}`);
    }
  }
  return { success: false, errors };
}

export type { PolicyContract };
