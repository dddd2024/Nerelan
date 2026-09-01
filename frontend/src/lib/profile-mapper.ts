import type { PermissionMode, PolicyContract } from "@/types";

/**
 * Map each PermissionMode to a default PolicyContract.
 *
 * These are fixture-driven UI defaults. Real authorization is enforced
 * server-side; these profiles are delegation requests only.
 *
 * Note: all budgets/window caps are positive integers (>=1) per the policy
 * validation rule. A capability that is not granted (e.g. merge_pr absent)
 * means the operation cannot happen regardless of its budget cap.
 */

const BASE_REPO = "dddd2024/Nerelan";
const FUTURE_EXPIRY = "2030-12-31T08:00:00Z";

function baseWindow(expiresAt: string): PolicyContract["autonomousWindow"] {
  return {
    enabled: false,
    startsAt: "2026-08-05T00:00:00Z",
    expiresAt,
    maxPrsOpened: 1,
    maxMergesToMain: 1,
    maxReleasesCreated: 1,
    maxDeploysToEnvironment: 1,
    stopConditions: [
      { type: "manual_stop", scope: "window" },
      { type: "authority_revoked", scope: "task" },
    ],
  };
}

function emptyResource(): PolicyContract["resourceAccess"] {
  return {
    filesystem: { allowedPaths: [], writablePaths: [] },
    network: { allowedDomains: [], allowWrite: false },
    shell: { allowedCommands: [], deniedCommands: [] },
    secrets: { access: "none", allowedKeys: [] },
    workerApproval: { required: false, approvers: [] },
  };
}

const ASK_FOR_APPROVAL: PolicyContract = {
  mode: "ASK_FOR_APPROVAL",
  repository: BASE_REPO,
  resourceAccess: {
    ...emptyResource(),
    filesystem: {
      allowedPaths: ["src/**", "tests/**"],
      writablePaths: ["src/**", "tests/**"],
    },
  },
  githubCapabilities: ["read_repository", "create_branch"],
  publicationCapabilities: [],
  publicationPolicy: {
    allowedArtifactOrPackage: [],
    allowedRegistry: [],
    allowedRepository: [],
    allowedEnvironment: [],
  },
  mergePolicy: {
    allowedRepositories: [],
    allowedBaseBranches: [],
    requiredChecks: [],
    allowedMergeMethods: [],
    requireExactHead: true,
  },
  autonomousWindow: baseWindow("2026-08-05T01:00:00Z"),
  budgets: {
    maxPrsOpened: 1,
    maxMergesToMain: 1,
    maxReleasesCreated: 1,
    maxDeploysToEnvironment: 1,
  },
};

const CONTROLLER_REVIEW: PolicyContract = {
  mode: "CONTROLLER_REVIEW",
  repository: BASE_REPO,
  resourceAccess: {
    filesystem: {
      allowedPaths: ["src/**", "tests/**", "docs/**"],
      writablePaths: ["src/**", "tests/**"],
    },
    network: { allowedDomains: ["github.com"], allowWrite: false },
    shell: { allowedCommands: ["pytest", "tsc", "eslint"], deniedCommands: [] },
    secrets: { access: "none", allowedKeys: [] },
    workerApproval: { required: true, approvers: ["@controller"] },
  },
  githubCapabilities: [
    "read_repository",
    "create_branch",
    "push_task_branch",
    "open_draft_pr",
  ],
  publicationCapabilities: [],
  publicationPolicy: {
    allowedArtifactOrPackage: [],
    allowedRegistry: [],
    allowedRepository: [],
    allowedEnvironment: [],
  },
  mergePolicy: {
    allowedRepositories: [],
    allowedBaseBranches: [],
    requiredChecks: [],
    allowedMergeMethods: [],
    requireExactHead: true,
  },
  autonomousWindow: baseWindow("2026-08-05T04:00:00Z"),
  budgets: {
    maxPrsOpened: 3,
    maxMergesToMain: 1,
    maxReleasesCreated: 1,
    maxDeploysToEnvironment: 1,
  },
};

const OWNER_CONTROL: PolicyContract = {
  mode: "OWNER_CONTROL",
  repository: BASE_REPO,
  resourceAccess: {
    filesystem: {
      allowedPaths: ["src/**", "tests/**", "docs/**"],
      writablePaths: ["src/**", "tests/**"],
    },
    network: { allowedDomains: ["github.com"], allowWrite: false },
    shell: { allowedCommands: ["pytest", "tsc", "eslint"], deniedCommands: [] },
    secrets: { access: "masked", allowedKeys: [] },
    workerApproval: { required: true, approvers: ["@owner"] },
  },
  githubCapabilities: [
    "read_repository",
    "create_branch",
    "push_task_branch",
    "open_draft_pr",
    "request_review",
    "merge_pr",
  ],
  publicationCapabilities: ["create_github_release"],
  publicationPolicy: {
    allowedArtifactOrPackage: ["reverse-agent-frontend"],
    allowedRegistry: [],
    allowedRepository: [BASE_REPO],
    allowedEnvironment: [],
  },
  mergePolicy: {
    allowedRepositories: [BASE_REPO],
    allowedBaseBranches: ["main"],
    requiredChecks: ["pytest", "ci"],
    allowedMergeMethods: ["merge"],
    requireExactHead: true,
  },
  autonomousWindow: {
    ...baseWindow(FUTURE_EXPIRY),
    enabled: true,
    maxPrsOpened: 3,
    maxMergesToMain: 2,
    maxReleasesCreated: 1,
    maxDeploysToEnvironment: 1,
    stopConditions: [
      { type: "max_merges_to_main", scope: "window", limit: 2 },
      { type: "window_expired", scope: "window" },
      { type: "manual_stop", scope: "window" },
      { type: "ci_failure_on_head", scope: "task" },
      { type: "main_drift_detected", scope: "task" },
      { type: "blocking_review_thread", scope: "task" },
      { type: "authority_revoked", scope: "task" },
    ],
  },
  budgets: {
    maxPrsOpened: 3,
    maxMergesToMain: 2,
    maxReleasesCreated: 1,
    maxDeploysToEnvironment: 1,
  },
};

const CUSTOM: PolicyContract = {
  mode: "CUSTOM",
  repository: BASE_REPO,
  resourceAccess: {
    filesystem: {
      allowedPaths: ["src/**", "tests/**", "docs/**"],
      writablePaths: ["src/**", "tests/**"],
    },
    network: { allowedDomains: ["github.com", "registry.npmjs.org"], allowWrite: true },
    shell: { allowedCommands: ["pytest", "tsc", "eslint", "npm"], deniedCommands: ["rm -rf"] },
    secrets: { access: "masked", allowedKeys: ["NPM_TOKEN"] },
    workerApproval: { required: true, approvers: ["@owner", "@controller"] },
  },
  githubCapabilities: [
    "read_repository",
    "create_branch",
    "push_task_branch",
    "open_draft_pr",
    "request_review",
    "merge_pr",
    "delete_merged_branch",
    "push_main",
  ],
  publicationCapabilities: [
    "create_tag",
    "create_github_release",
    "publish_package",
    "publish_container",
    "deploy_preview",
    "deploy_staging",
    "deploy_production",
    "rollback_deployment",
  ],
  publicationPolicy: {
    allowedArtifactOrPackage: ["reverse-agent-frontend"],
    allowedRegistry: ["registry.npmjs.org"],
    allowedRepository: [BASE_REPO],
    allowedEnvironment: ["preview", "staging", "production"],
    rollbackStrategy: "redeploy-previous-tag",
  },
  mergePolicy: {
    allowedRepositories: [BASE_REPO],
    allowedBaseBranches: ["main"],
    requiredChecks: ["pytest", "ci"],
    allowedMergeMethods: ["merge", "squash"],
    requireExactHead: true,
  },
  autonomousWindow: {
    enabled: true,
    startsAt: "2026-08-05T00:00:00Z",
    expiresAt: FUTURE_EXPIRY,
    maxPrsOpened: 3,
    maxMergesToMain: 2,
    maxReleasesCreated: 1,
    maxDeploysToEnvironment: 1,
    stopConditions: [
      { type: "max_merges_to_main", scope: "window", limit: 2 },
      { type: "max_releases_created", scope: "window", limit: 1 },
      { type: "max_deploys_to_environment", scope: "window", limit: 1 },
      { type: "window_expired", scope: "window" },
      { type: "manual_stop", scope: "window" },
      { type: "ci_failure_on_head", scope: "task" },
      { type: "main_drift_detected", scope: "task" },
      { type: "blocking_review_thread", scope: "task" },
      { type: "authority_revoked", scope: "task" },
    ],
  },
  budgets: {
    maxPrsOpened: 3,
    maxMergesToMain: 2,
    maxReleasesCreated: 1,
    maxDeploysToEnvironment: 1,
  },
};

const PROFILES: Record<PermissionMode, PolicyContract> = {
  ASK_FOR_APPROVAL,
  CONTROLLER_REVIEW,
  OWNER_CONTROL,
  CUSTOM,
};

export function profileToPolicy(mode: PermissionMode): PolicyContract {
  // Deep clone so callers can mutate without affecting the defaults.
  return JSON.parse(JSON.stringify(PROFILES[mode])) as PolicyContract;
}

export function allProfiles(): Record<PermissionMode, PolicyContract> {
  return JSON.parse(JSON.stringify(PROFILES)) as Record<PermissionMode, PolicyContract>;
}

export const CUSTOM_EXAMPLE_POLICY: PolicyContract = CUSTOM;