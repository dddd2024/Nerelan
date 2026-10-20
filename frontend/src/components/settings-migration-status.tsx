import { useQuery } from "@tanstack/react-query";
import type { Connection } from "@/schemas/model-access";
import { getDefaultModelControlClient, type MagpieRuntime } from "@/lib/model-control-client";

type Tone = "ok" | "pending" | "muted" | "error";

const TONE_CLASS: Record<Tone, string> = {
  ok: "border-ra-status-success/40 text-ra-status-success",
  pending: "border-ra-status-warning/40 text-ra-status-warning",
  muted: "border-ra-border text-ra-text-secondary",
  error: "border-ra-status-error/40 text-ra-status-error",
};

/* Every badge here is derived from an observation (Magpie host probe, the
   connection list). Nothing is inferred from the view mode the user picked on
   the usage page, so the panel can never claim a migration that the routing
   layer has not performed. */
export function SettingsMigrationStatus({ connections, connectionsFailed }: {
  connections: Connection[];
  connectionsFailed: boolean;
}) {
  const magpie = useQuery({
    queryKey: ["settings", "magpie-runtime"],
    queryFn: async () => (await getDefaultModelControlClient().getMagpie()).runtime,
    staleTime: 60_000,
  });
  const magpieBadge = magpie.isPending
    ? { label: "正在检查", tone: "muted" as const, detail: "正在读取 Magpie 状态。" }
    : magpie.isError
      ? { label: "数据不可用", tone: "error" as const, detail: "无法读取 Magpie 状态；这不代表 Magpie 未运行。" }
      : magpieRuntimeBadge(magpie.data);
  const enabled = connections.filter((connection) => connection.enabled).length;
  const localBadge = connectionsFailed
    ? { label: "数据不可用", tone: "error" as const, detail: "无法读取本地连接。" }
    : enabled > 0
      ? { label: "本地连接仍在使用", tone: "pending" as const, detail: `${enabled} 个启用的本地连接仍负责任务派发。` }
      : { label: "没有启用的本地连接", tone: "muted" as const, detail: "当前没有启用的本地连接。" };

  return (
    <section data-testid="settings-migration-status" aria-labelledby="settings-migration-status-title"
      className="rounded-md border border-ra-border px-3 py-3">
      <h2 id="settings-migration-status-title" className="text-sm font-medium text-ra-text">迁移状态</h2>
      <dl className="mt-2 grid gap-2 text-xs sm:grid-cols-3">
        <StatusItem name="Magpie 接入" testId="migration-magpie" {...magpieBadge} />
        <StatusItem name="实际路由" testId="migration-routing" label="实际路由待验证" tone="pending"
          detail="尚未验证任务是否经由 Magpie 路由，请以运行记录中的实际模型为准。" />
        <StatusItem name="本地连接" testId="migration-local" {...localBadge} />
      </dl>
    </section>
  );
}

function magpieRuntimeBadge(runtime: MagpieRuntime): { label: string; tone: Tone; detail: string } {
  switch (runtime.status) {
    case "STARTED":
    case "ALREADY_RUNNING":
      return { label: "只读已接入", tone: "ok", detail: `已观测到 Magpie，提供 ${runtime.model_count} 个模型；仅用于只读展示。` };
    case "MAGPIE_DISABLED":
      return { label: "未接入", tone: "muted", detail: "未启用 Magpie。" };
    case "UNREACHABLE":
    case "START_FAILED":
      return {
        label: "不可用", tone: "error",
        detail: `Magpie 当前不可达（${runtime.status}${runtime.reason ? `：${runtime.reason}` : ""}）。`,
      };
    default:
      return { label: "未知", tone: "muted", detail: `无法识别的 Magpie 状态（${runtime.status || "空"}）。` };
  }
}

function StatusItem({ name, label, tone, detail, testId }: {
  name: string; label: string; tone: Tone; detail: string; testId: string;
}) {
  return (
    <div data-testid={testId} className="min-w-0">
      <dt className="text-ra-text-tertiary">{name}</dt>
      <dd className="mt-1">
        <span className={`inline-flex rounded border px-1.5 py-0.5 font-medium ${TONE_CLASS[tone]}`}>{label}</span>
        <span className="mt-1 block text-ra-text-secondary">{detail}</span>
      </dd>
    </div>
  );
}
