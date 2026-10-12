import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({ interpret: vi.fn(), fetchJob: vi.fn(), apply: vi.fn() }));
vi.mock("@/lib/platform-client", async (original) => ({
  ...(await original<typeof import("@/lib/platform-client")>()),
  interpretAgentPolicy: api.interpret,
  fetchAgentPolicyJob: api.fetchJob,
  applyAgentPolicy: api.apply,
}));

import { AgentTeamEditor } from "@/components/agent-team-editor";
import { getDefaultModelControlClient } from "@/lib/model-control-client";

it("turns a preference sentence into a proposal that applies only on confirmation", async () => {
  const bindings = await getDefaultModelControlClient().listBindings();
  const target = bindings[0];
  const proposal = { roles: { coder: target.bindingId }, excluded: [], explanation: "日常编码交给免费模型。" };
  api.interpret.mockResolvedValue({ id: "job-1", text: "编码尽量免费", status: "PROPOSED", error: "", proposal });
  api.apply.mockResolvedValue({ job: { id: "job-1", text: "编码尽量免费", status: "APPLIED", error: "", proposal } });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><AgentTeamEditor bindings={bindings} /></QueryClientProvider>);

  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Agent 团队偏好"), "编码尽量免费");
  await user.click(screen.getByRole("button", { name: "让系统理解并给出安排" }));
  expect(api.interpret).toHaveBeenCalledWith("编码尽量免费");
  const shown = await screen.findByTestId("agent-policy-proposal");
  expect(shown).toHaveTextContent("日常编码交给免费模型。");
  expect(shown).toHaveTextContent(target.modelId);
  expect(api.apply).not.toHaveBeenCalled();

  await user.click(screen.getByRole("button", { name: "确认应用" }));
  expect(api.apply).toHaveBeenCalledWith("job-1");
  await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("已应用到 Agent 团队"));
});
