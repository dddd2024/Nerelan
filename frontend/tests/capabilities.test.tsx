import { describe, it, expect } from "vitest";
import { renderWithProviders } from "./test-utils";
import { GithubCapabilitiesEditor } from "@/components/github-capabilities-editor";
import { PublicationEditor } from "@/components/publication-editor";
import type {
  GithubCapability,
  PublicationCapability,
  PublicationPolicy,
  PolicyContract,
} from "@/types";
import { profileToPolicy } from "@/lib/profile-mapper";

describe("capabilities editors", () => {
  it("merge_pr and push_main toggle independently", async () => {
    const policy: PolicyContract = profileToPolicy("OWNER_CONTROL");
    let caps: GithubCapability[] = [...policy.githubCapabilities];
    const { getByTestId, rerender } = renderWithProviders(
      <GithubCapabilitiesEditor
        value={caps}
        onChange={(n) => {
          caps = n;
        }}
      />,
    );

    const merge = getByTestId("cap-merge_pr") as HTMLInputElement;
    const pushMain = getByTestId("cap-push_main") as HTMLInputElement;
    expect(merge.checked).toBe(true);
    expect(pushMain.checked).toBe(false);

    // Toggle push_main on; merge_pr stays on (independent).
    pushMain.click();
    rerender(
      <GithubCapabilitiesEditor
        value={caps}
        onChange={(n) => {
          caps = n;
        }}
      />,
    );
    expect((getByTestId("cap-merge_pr") as HTMLInputElement).checked).toBe(true);
    expect((getByTestId("cap-push_main") as HTMLInputElement).checked).toBe(true);
  });

  it("release and deploy toggle independently", async () => {
    let caps: PublicationCapability[] = ["create_github_release"];
    const policy: PublicationPolicy = {
      allowedArtifactOrPackage: ["pkg"],
      allowedRegistry: [],
      allowedRepository: ["repo"],
      allowedEnvironment: ["preview"],
      rollbackStrategy: "redeploy",
    };
    const { getByTestId, rerender } = renderWithProviders(
      <PublicationEditor
        capabilities={caps}
        onCapabilitiesChange={(n) => {
          caps = n;
        }}
        policy={policy}
        onPolicyChange={() => {}}
      />,
    );

    const release = getByTestId("pub-create_github_release") as HTMLInputElement;
    const deployProd = getByTestId(
      "pub-deploy_production",
    ) as HTMLInputElement;
    expect(release.checked).toBe(true);
    expect(deployProd.checked).toBe(false);

    deployProd.click();
    rerender(
      <PublicationEditor
        capabilities={caps}
        onCapabilitiesChange={(n) => {
          caps = n;
        }}
        policy={policy}
        onPolicyChange={() => {}}
      />,
    );
    expect((getByTestId("pub-create_github_release") as HTMLInputElement).checked).toBe(true);
    expect((getByTestId("pub-deploy_production") as HTMLInputElement).checked).toBe(true);
  });

  it("renders all 11 GitHub capabilities", () => {
    const { getByTestId } = renderWithProviders(
      <GithubCapabilitiesEditor value={[]} onChange={() => {}} />,
    );
    const all: GithubCapability[] = [
      "read_repository",
      "create_issue",
      "update_issue",
      "create_branch",
      "push_task_branch",
      "open_draft_pr",
      "mark_ready",
      "request_review",
      "merge_pr",
      "delete_merged_branch",
      "push_main",
    ];
    for (const c of all) {
      expect(getByTestId(`cap-${c}`)).toBeTruthy();
    }
  });
});
