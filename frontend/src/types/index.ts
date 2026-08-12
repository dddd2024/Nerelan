/**
 * reverse-agent Frontend V1 — Domain Types
 *
 * Adapted from OpenHands 1.8.0 permission/policy concepts. These types are
 * fixture-driven UI types only. They do NOT call any real API and do NOT
 * authorize any operation. Real authorization is enforced server-side.
 */

// ---------------------------------------------------------------------------
// Risk & Run state
// ---------------------------------------------------------------------------

export type RiskTier = "R0" | "R1" | "R2" | "R3";

export type RunState =
  | "READY_FOR_HUMAN"
  | "RUNNING"
  | "BLOCKED_EXTERNAL"
  | "REWORK_REQUIRED"
  | "FAILED_TERMINAL"
  | "WAITING_FOR_OWNER";

// ---------------------------------------------------------------------------
// Activity stream
// ---------------------------------------------------------------------------

export type ActivityEventType =
  | "DISCOVERED"
  | "VALIDATED"
  | "WORKSPACE_READY"
  | "EXECUTOR_RUNNING"
  | "EXECUTOR_FINISHED"
  | "LOCAL_VALIDATED"
  | "COMMITTED"
  | "PUSHED"
  | "DRAFT_PR_OPEN"
  | "WORKFLOWS_OBSERVED"
  | "READY_FOR_HUMAN";

export interface ActivityEvent {
  id: string;
  type: ActivityEventType;
  timestamp: string;
  title: string;
  description: string;
  rawLog?: string;
  expanded: boolean;
}

// ---------------------------------------------------------------------------
// Changes
// ---------------------------------------------------------------------------

export type FileStatus = "added" | "modified" | "deleted" | "renamed";

export interface ChangedFile {
  path: string;
  status: FileStatus;
  additions: number;
  deletions: number;
  diff: string;
}

// ---------------------------------------------------------------------------
// Evidence
// ---------------------------------------------------------------------------

export type EvidenceStatus = "pass" | "fail" | "pending" | "info";

export interface EvidenceItem {
  id: string;
  category: string;
  label: string;
  value: string;
  status: EvidenceStatus;
  detail?: string;
  rawJson?: string;
}

// ---------------------------------------------------------------------------
// Task
// ---------------------------------------------------------------------------

export type AuthorityStatus =
  | "APPROVED"
  | "CANDIDATE"
  | "EXPIRED"
  | "MISSING"
  | "REVOKED";

export type TestStatus = "PASS" | "FAIL" | "PENDING" | "RUNNING";

export type WorkflowStatus =
  | "SUCCESS"
  | "FAILURE"
  | "PENDING"
  | "RUNNING"
  | "NEUTRALIZED"
  | "UNKNOWN";

export interface DraftPr {
  number: number;
  title: string;
  url: string;
  headSha: string;
  baseSha: string;
  draft: boolean;
  state: "open" | "closed" | "merged";
}

export interface Task {
  id: string;
  title: string;
  issueNumber: number;
  state: RunState;
  riskTier: RiskTier;
  updatedAt: string;
  blocker?: string;
  nextAction?: string;
  permissionProfile: PermissionMode;
  modelProfileId?: string;
  bindingRef?: string;
  draftPr?: DraftPr;
  branch: string;
  activity: ActivityEvent[];
  changes: ChangedFile[];
  evidence: EvidenceItem[];
  authorityStatus: AuthorityStatus;
  testStatus: TestStatus;
  workflowStatus: WorkflowStatus;
  executor?: string;
  repository?: string;
  executionId?: string;
  failureClassification?: string;
  validationCommandId?: string;
  validationExitCode?: number;
}

// ---------------------------------------------------------------------------
// Permission policy contract
// ---------------------------------------------------------------------------

export type PermissionMode =
  | "ASK_FOR_APPROVAL"
  | "CONTROLLER_REVIEW"
  | "OWNER_CONTROL"
  | "CUSTOM";

export interface FilesystemScope {
  allowedPaths: string[];
  writablePaths: string[];
  tempDir?: string;
}

export interface NetworkScope {
  allowedDomains: string[];
  allowWrite: boolean;
}

export interface ShellScope {
  allowedCommands: string[];
  deniedCommands: string[];
}

export type SecretsAccess = "none" | "masked" | "raw_values";

export interface SecretsScope {
  access: SecretsAccess;
  allowedKeys: string[];
}

export interface WorkerApprovalScope {
  required: boolean;
  approvers: string[];
}

export interface ResourceAccess {
  filesystem: FilesystemScope;
  network: NetworkScope;
  shell: ShellScope;
  secrets: SecretsScope;
  workerApproval: WorkerApprovalScope;
}

export type GithubCapability =
  | "read_repository"
  | "create_issue"
  | "update_issue"
  | "create_branch"
  | "push_task_branch"
  | "open_draft_pr"
  | "mark_ready"
  | "request_review"
  | "merge_pr"
  | "delete_merged_branch"
  | "push_main";

export type PublicationCapability =
  | "create_tag"
  | "create_github_release"
  | "publish_package"
  | "publish_container"
  | "deploy_preview"
  | "deploy_staging"
  | "deploy_production"
  | "rollback_deployment";

export type MergeMethod = "merge" | "squash" | "rebase";

export interface MergePolicy {
  allowedRepositories: string[];
  allowedBaseBranches: string[];
  requiredChecks: string[];
  allowedMergeMethods: MergeMethod[];
  requireExactHead: boolean;
}

export interface PublicationPolicy {
  allowedArtifactOrPackage: string[];
  allowedRegistry: string[];
  allowedRepository: string[];
  allowedEnvironment: string[];
  rollbackStrategy?: string;
}

export type StopConditionScope = "task" | "window";

export type StopCondition =
  | "max_prs_opened"
  | "max_merges_to_main"
  | "max_releases_created"
  | "max_deploys_to_environment"
  | "budget_exhausted"
  | "window_expired"
  | "manual_stop"
  | "blocking_review_thread"
  | "ci_failure_on_head"
  | "main_drift_detected"
  | "authority_revoked";

export interface StopConditionRule {
  type: StopCondition;
  scope: StopConditionScope;
  limit?: number;
}

export interface AutonomousWindow {
  enabled: boolean;
  startsAt: string;
  expiresAt: string;
  maxPrsOpened: number;
  maxMergesToMain: number;
  maxReleasesCreated: number;
  maxDeploysToEnvironment: number;
  stopConditions: StopConditionRule[];
}

export interface Budgets {
  maxPrsOpened: number;
  maxMergesToMain: number;
  maxReleasesCreated: number;
  maxDeploysToEnvironment: number;
}

export interface PolicyContract {
  mode: PermissionMode;
  repository: string;
  resourceAccess: ResourceAccess;
  githubCapabilities: GithubCapability[];
  publicationCapabilities: PublicationCapability[];
  publicationPolicy: PublicationPolicy;
  mergePolicy: MergePolicy;
  autonomousWindow: AutonomousWindow;
  budgets: Budgets;
}
