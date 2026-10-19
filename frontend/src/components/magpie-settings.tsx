import { useEffect, useState } from "react";
import { getDefaultModelControlClient, type ModelControlClient, type MagpieSettings, type MagpieRuntime } from "@/lib/model-control-client";

export function MagpieSettingsEditor({ client = getDefaultModelControlClient() }: {
  client?: Pick<ModelControlClient, "getMagpie" | "saveMagpie">;
}) {
  const [settings, setSettings] = useState<MagpieSettings | null>(null);
  const [runtime, setRuntime] = useState<MagpieRuntime | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    let active = true;
    async function refresh() {
      try {
        const state = await client.getMagpie();
        if (!active) return;
        setSettings(current => current ?? state.settings);
        setRuntime(state.runtime);
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : String(cause));
      }
    }
    void refresh();
    const timer = setInterval(() => void refresh(), 60_000);
    return () => { active = false; clearInterval(timer); };
  }, [client]);
  async function save() {
    setError(""); setSaved(false); setSaving(true);
    try {
      if (!settings) return;
      await client.saveMagpie(settings);
      setSaved(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally { setSaving(false); }
  }
  return <section aria-label="Magpie" className="space-y-3 rounded-lg border p-4">
    <h2>Magpie</h2>
    {runtime && <div role="status">
      <p>{runtime.status}{runtime.reason ? ` (${runtime.reason})` : ""}</p>
      <p>Last probe: {runtime.last_probe_at ?? "Never"}</p>
      <p>Models served: {runtime.model_count}</p>
    </div>}
    {settings && <>
      <label className="block"><input type="checkbox" checked={settings.enabled}
        onChange={e => setSettings({ ...settings, enabled: e.target.checked })} /> Start Magpie with Nerelan</label>
      <label className="block">Magpie executable<input className="block w-full rounded border p-2" value={settings.executable}
        placeholder={"F:\\magpie\\magpie.exe"} onChange={e => setSettings({ ...settings, executable: e.target.value })} /></label>
      <label className="block">Magpie base URL<input className="block w-full rounded border p-2" value={settings.base_url}
        onChange={e => setSettings({ ...settings, base_url: e.target.value })} /></label>
      <button type="button" disabled={saving} onClick={() => void save()}>Save Magpie settings</button>
      <p>Changes apply on the next host check (within 60 seconds). Nerelan never stops Magpie.</p>
      {saved && <p>Magpie settings saved.</p>}
    </>}
    {error && <p role="alert">{error}</p>}
  </section>;
}
