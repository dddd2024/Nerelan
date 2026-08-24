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
  secretStatus: ConnectionSecretStatusSchema,
  externalSessionStatus: ExternalSessionStatusSchema,
});

export const ConnectionInputSchema = ConnectionSchema.omit({
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
      connection.secretStatus === "environment"
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
