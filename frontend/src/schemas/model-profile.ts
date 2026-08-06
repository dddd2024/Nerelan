import { z } from "zod";

export const ModelProviderSchema = z.enum([
  "openai-compatible",
  "litellm-proxy",
]);

export const ModelExecutorSchema = z.enum(["openhands", "codex-acp"]);

export const SecretStatusSchema = z.enum([
  "missing",
  "session",
  "environment",
]);

const profileId = z
  .string()
  .min(1, "配置 ID 不能为空")
  .max(80, "配置 ID 不能超过 80 个字符")
  .regex(
    /^[a-z0-9][a-z0-9._-]*$/,
    "配置 ID 只能包含小写字母、数字、点、下划线和连字符",
  );

const baseUrl = z
  .string()
  .url("Base URL 必须是有效 URL")
  .refine((value) => {
    const parsed = new URL(value);
    return !parsed.username && !parsed.password;
  }, "Base URL 不能包含用户名或密码");

export const ModelProfileSchema = z.object({
  id: profileId,
  name: z.string().trim().min(1, "配置名称不能为空").max(120),
  provider: ModelProviderSchema,
  baseUrl,
  modelId: z.string().trim().min(1, "Model ID 不能为空").max(200),
  executor: ModelExecutorSchema,
  enabled: z.boolean(),
  isDefault: z.boolean(),
  secretStatus: SecretStatusSchema,
});

export const ModelProfileInputSchema = ModelProfileSchema.omit({
  secretStatus: true,
}).extend({
  apiKey: z.string().max(4096).optional(),
  apiKeyEnv: z
    .string()
    .trim()
    .regex(/^[A-Z_][A-Z0-9_]*$/, "环境变量名格式无效")
    .optional(),
});

export const ModelConnectionResultSchema = z.object({
  ok: z.boolean(),
  status: z.string().min(1),
  message: z.string().min(1),
  latencyMs: z.number().nonnegative().nullable().optional(),
});

export type ModelProvider = z.infer<typeof ModelProviderSchema>;
export type ModelExecutor = z.infer<typeof ModelExecutorSchema>;
export type SecretStatus = z.infer<typeof SecretStatusSchema>;
export type ModelProfile = z.infer<typeof ModelProfileSchema>;
export type ModelProfileInput = z.infer<typeof ModelProfileInputSchema>;
export type ModelConnectionResult = z.infer<
  typeof ModelConnectionResultSchema
>;
