import type { DiskState } from "@/lib/platform-client";

type Disk = DiskState | null | undefined;

const gb = (value: number) => `${Number(value.toFixed(value < 10 ? 2 : 0))} GB`;

/** "磁盘剩 4.8 GB（共 100 GB）"; empty when the host could not read it. */
export function diskFreeLine(disk: Disk): string {
  if (!disk || disk.free_gb === null) return "";
  return `磁盘剩 ${gb(disk.free_gb)}${disk.total_gb ? `（共 ${gb(disk.total_gb)}）` : ""}`;
}

/** Why no new task starts and what ends it; empty when dispatch is not held. */
export function diskHoldLine(disk: Disk): string {
  if (!disk?.hold) return "";
  const waiting = disk.waiting_task_count > 0 ? `，${disk.waiting_task_count} 个任务等待中` : "";
  const free = disk.free_gb === null ? "剩余空间暂时读不到" : diskFreeLine(disk);
  return `磁盘空间不足，暂停启动新任务${waiting} · ${free}，低于下限 ${gb(disk.floor_gb)}。正在运行的任务继续；空间恢复到 ${gb(disk.resume_gb)} 后自动继续，不消耗重试次数。`;
}
