import { useState } from "react";
import { Link } from "react-router";
import { useDoctorReport } from "@/hooks/use-platform";
import { doctorChecklist } from "@/lib/doctor-checklist";

const DISMISSED_KEY = "nerelan.readiness.dismissed";

function wasDismissed() {
  try { return sessionStorage.getItem(DISMISSED_KEY) === "1"; }
  catch { return false; }
}

export function ReadinessChecklist() {
  const [dismissed, setDismissed] = useState(wasDismissed);
  const query = useDoctorReport(!dismissed);
  const checklist = query.data ? doctorChecklist(query.data) : undefined;
  if (dismissed || (!query.isError && !checklist?.needsAttention)) return null;

  return (
    <section aria-label="准备情况" className="mb-5 rounded-lg border border-ra-border p-4 text-sm text-ra-text">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-medium">准备情况</h2>
        <div className="flex gap-3">
          <button type="button" disabled={query.isFetching} onClick={() => void query.refetch()}
            className="text-ra-accent disabled:opacity-50">重新检查</button>
          <button type="button" className="text-ra-text-secondary" onClick={() => {
            setDismissed(true);
            try { sessionStorage.setItem(DISMISSED_KEY, "1"); } catch { /* Storage may be disabled. */ }
          }}>本次不再显示</button>
        </div>
      </div>
      {query.isError ? <p role="alert" className="mt-3">无法检查准备情况，请确认任务服务已启动后重新检查。</p> : null}
      <ul className="mt-3 space-y-3">
        {checklist?.items.map((item) => (
          <li key={item.id}>
            <span className="font-medium">{item.name}</span>
            <span className="ml-2 text-ra-text-secondary">{item.state}</span>
            <p className="mt-1 text-xs text-ra-text-secondary">{item.message}{item.href && (
              <> <Link to={item.href} className="text-ra-accent hover:underline">前往设置</Link></>
            )}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
