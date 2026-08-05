import { useState } from "react";
import { PermissionSelector } from "@/components/permission-selector";
import { CustomPolicyEditor } from "@/components/custom-policy-editor";
import { AuthorizationSummary } from "@/components/authorization-summary";
import { profileToPolicy } from "@/lib/profile-mapper";
import type { PermissionMode, PolicyContract } from "@/types";

export function SettingsPage() {
  const [mode, setMode] = useState<PermissionMode>("CONTROLLER_REVIEW");
  const [policy, setPolicy] = useState<PolicyContract>(() =>
    profileToPolicy("CONTROLLER_REVIEW"),
  );
  const [editorOpen, setEditorOpen] = useState(false);

  const handleMode = (next: PermissionMode) => {
    setMode(next);
    setPolicy(profileToPolicy(next));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500">
          Default permission profiles. Custom policies are delegation requests
          only.
        </p>
      </div>
      <div className="max-w-xs">
        <PermissionSelector value={mode} onChange={handleMode} />
      </div>
      <AuthorizationSummary policy={policy} />
      <button
        type="button"
        onClick={() => setEditorOpen(true)}
        className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        data-testid="open-custom-editor"
      >
        Edit custom policy
      </button>
      <CustomPolicyEditor
        open={editorOpen}
        policy={policy}
        onChange={setPolicy}
        onClose={() => setEditorOpen(false)}
      />
    </div>
  );
}
