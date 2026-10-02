import { z } from "zod";

const providerId = z
  .string()
  .min(1, "Provider ID 不能为空")
  .max(80, "Provider ID 不能超过 80 个字符")
  .regex(
    /^[a-z0-9][a-z0-9._-]{0,79}$/,
    "Provider ID 只能包含小写字母、数字、点、下划线和连字符",
  );

export const ConnectionProviderSchema = providerId;

export const AuthMethodSchema = z.enum([
  "api_key",
  "account_login",
  "external_cli_session",
  "none",
]);

export const ConnectionSecretStatusSchema = z.enum([
  "missing",
  "session",
  "environment",
  "not_applicable",
  "stored",
  "store_locked",
  "replacement_required",
]);

export const ExternalSessionStatusSchema = z.enum([
  "missing",
  "available",
  "executor_managed",
  "not_applicable",
]);

export const ConnectionVerificationCapabilitySchema = z.enum([
  "supported",
  "credential_missing",
  "executor_managed",
  "connection_disabled",
]);

const accessId = z
  .string()
  .min(1, "ID 不能为空")
  .max(80, "ID 不能超过 80 个字符")
  .regex(
    /^[a-z0-9][a-z0-9._-]*$/,
    "ID 只能包含小写字母、数字、点、下划线和连字符",
  );

const baseUrl = z
  .string()
  .url("Base URL 必须是有效 URL")
  .refine((value) => {
    const parsed = new URL(value);
    return !parsed.username && !parsed.password;
  }, "Base URL 不能包含用户名或密码");

export const ConnectionSchema = z.object({
  connectionId: accessId,
  name: z.string().trim().min(1, "名称不能为空").max(120),
  provider: ConnectionProviderSchema,
  baseUrl,
  authMethod: AuthMethodSchema,
  enabled: z.boolean(),
  credentialConfigured: z.boolean(),
  secretStatus: ConnectionSecretStatusSchema,
  externalSessionStatus: ExternalSessionStatusSchema,
  upstreamProviderId: providerId.nullable().optional(),
  protocolFamily: providerId.nullable().optional(),
  executorProviderId: providerId.optional(),
});

export const ConnectionInputSchema = ConnectionSchema.omit({
  credentialConfigured: true,
  secretStatus: true,
  externalSessionStatus: true,
}).extend({
  apiKey: z.string().max(4096).optional(),
  apiKeyEnv: z
    .string()
    .trim()
    .regex(/^[A-Z_][A-Z0-9_]*$/, "环境变量名格式无效")
    .optional(),
  clearSecret: z.boolean().optional(),
});

export const ExecutorSchema = z.object({
  executorId: z.string().min(1).max(80),
  name: z.string().min(1).max(120),
  operational: z.boolean(),
  capabilities: z.array(z.string()),
  readinessStatus: z.string().optional(),
});

export const BindingSchema = z.object({
  bindingId: accessId,
  name: z.string().trim().min(1, "名称不能为空").max(120),
  executorId: z.string().min(1, "执行器 ID 不能为空").max(80),
  connectionId: z.string().min(1, "连接 ID 不能为空").max(80),
  modelId: z.string().trim().min(1, "Model ID 不能为空").max(200),
  enabled: z.boolean(),
});

export const BindingInputSchema = BindingSchema;

export type ConnectionProvider = z.infer<typeof ConnectionProviderSchema>;
export type AuthMethod = z.infer<typeof AuthMethodSchema>;
export type ConnectionSecretStatus = z.infer<typeof ConnectionSecretStatusSchema>;
export type ExternalSessionStatus = z.infer<typeof ExternalSessionStatusSchema>;
export type ConnectionVerificationCapability = z.infer<
  typeof ConnectionVerificationCapabilitySchema
>;
export type Connection = z.infer<typeof ConnectionSchema>;
export type ConnectionInput = z.infer<typeof ConnectionInputSchema>;
export type Executor = z.infer<typeof ExecutorSchema>;
export type Binding = z.infer<typeof BindingSchema>;
export type BindingInput = z.infer<typeof BindingInputSchema>;

export function connectionVerificationCapability(
  connection: Connection,
): ConnectionVerificationCapability {
  if (!connection.enabled) return "connection_disabled";

  if (connection.authMethod === "api_key") {
    return connection.secretStatus === "session" ||
      connection.secretStatus === "environment" ||
      connection.secretStatus === "stored"
      ? "supported"
      : "credential_missing";
  }

  if (connection.authMethod === "none") return "supported";

  return "executor_managed";
}

export const ConnectionProbeResultSchema = z.object({
  ok: z.boolean(),
  status: z.string(),
  message: z.string(),
  latencyMs: z.number().nullable(),
});

export type ConnectionProbeResult = z.infer<typeof ConnectionProbeResultSchema>;

export const ConnectionModelsResultSchema = z.object({
  ok: z.boolean(),
  status: z.string(),
  message: z.string(),
  latencyMs: z.number().nullable(),
  models: z.array(z.string().min(1).max(200)).max(1000).default([]),
  connectionId: accessId.optional(),
  configurationRevision: z.string().min(1).max(200).nullable().optional(),
  catalogRevision: z.string().min(1).max(200).nullable().optional(),
  observedAt: z.string().max(80).nullable().optional(),
  source: z.literal("provider_advertised").nullable().optional(),
  entitlement: z.literal("not_observed").optional(),
  modelRecords: z.array(z.object({
    modelId: z.string().min(1).max(200),
    displayName: z.string().max(120).nullable().optional(),
    ownedBy: z.string().max(80).nullable().optional(),
  })).max(1000).default([]),
});

export type ConnectionModelsResult = z.infer<typeof ConnectionModelsResultSchema>;

export const CatalogBindingInputSchema = z.object({
  connectionId: accessId,
  configurationRevision: z.string().min(1).max(200),
  catalogRevision: z.string().min(1).max(200),
  executorId: accessId,
  modelId: z.string().min(1).max(200),
});
export type CatalogBindingInput = z.infer<typeof CatalogBindingInputSchema>;

export const CatalogBindingResultSchema = z.object({
  binding: BindingSchema,
  created: z.boolean(),
  reusedManual: z.boolean(),
  configurationRevision: z.string().min(1).max(200),
  catalogRevision: z.string().min(1).max(200),
  source: z.enum(["manual", "discovered"]),
  advertisedModelId: z.string().min(1).max(200),
  availability: z.literal("advertised_unverified"),
});
export type CatalogBindingResult = z.infer<typeof CatalogBindingResultSchema>;

export const ModelSelectionInputSchema = z.object({
  selectionMode: z.enum(["automatic", "manual"]),
  manualBindingRef: accessId.optional(),
  purpose: z.string().min(1).max(80).optional(),
  requiredCapabilities: z.array(z.string().min(1).max(80)).max(16).optional(),
  orchestrationMode: z.enum(["single", "sequential_team"]).optional(),
  executorPreference: accessId.optional(),
  preferredBindingRefs: z.array(accessId).max(32).optional(),
});
export type ModelSelectionInput = z.infer<typeof ModelSelectionInputSchema>;

export const ModelSelectionCandidateSchema = z.object({
  bindingRef: accessId,
  connectionId: accessId,
  executorId: accessId,
  modelId: z.string().max(200),
  configurationRevision: z.string().min(1).max(200).nullable(),
  catalogRevision: z.string().min(1).max(200).nullable(),
  source: z.enum(["manual", "discovered"]),
  eligible: z.boolean(),
  reasonCodes: z.array(z.string().max(100)).max(30),
  explanation: z.string().max(2000),
  availability: z.enum(["advertised_unverified", "not_observed"]),
  underlyingIdentity: z.null(),
  underlyingIdentityStatus: z.literal("not_observed"),
  cost: z.null(),
  quality: z.null(),
});
export const ModelSelectionResultSchema = z.object({
  previewOnly: z.literal(true),
  status: z.enum(["recommended", "manual_blocked", "no_eligible_pairing"]),
  message: z.string().max(2000),
  policyId: z.literal("catalog-preview-v1"),
  recommended: ModelSelectionCandidateSchema.nullable(),
  candidates: z.array(ModelSelectionCandidateSchema).max(4096),
  evidenceUnknowns: z.array(z.string().max(80)).max(20),
});
export type ModelSelectionResult = z.infer<typeof ModelSelectionResultSchema>;

export const AccountAuthStatusSchema = z.object({
  status: z.enum([
    "idle",
    "busy",
    "awaiting_browser",
    "expired",
    "failed",
    "canceled",
    "authenticated",
    "verification_pending",
    "provider_logout_required",
  ]),
  provider: z.literal("openai"),
  externalSessionStatus: ExternalSessionStatusSchema.optional(),
  authorizationUrl: z.string().url().optional(),
  callbackMethod: z.enum(["auto", "code"]).optional(),
  instructions: z.string().max(2000).optional(),
  expiresInSeconds: z.number().int().positive().max(900).optional(),
});

export type AccountAuthStatus = z.infer<typeof AccountAuthStatusSchema>;
