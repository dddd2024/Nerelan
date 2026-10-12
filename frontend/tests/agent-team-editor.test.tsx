import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";
import { AgentTeamEditor } from "@/components/agent-team-editor";
import { getDefaultModelControlClient } from "@/lib/model-control-client";

it("assigns team roles to saved bindings and persists the roster", async () => {
  const client = getDefaultModelControlClient();
  const bindings = await client.listBindings();
  expect(bindings.length).toBeGreaterThan(0);
  const target = bindings[0];
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><AgentTeamEditor bindings={bindings} /></QueryClientProvider>);

  const user = userEvent.setup();
  const save = await screen.findByRole("button", { name: "保存 Agent 团队" });
  expect(save).toBeDisabled();
  for (const label of ["规划者", "复杂编码", "常规编码", "简单任务", "审查者"]) {
    expect(screen.getByLabelText(`${label}的模型绑定`)).toBeInTheDocument();
  }
  await waitFor(() => expect(screen.getByLabelText("简单任务的模型绑定")).toBeEnabled());
  await user.selectOptions(screen.getByLabelText("简单任务的模型绑定"), target.bindingId);
  expect(save).toBeEnabled();
  await user.click(save);

  await waitFor(async () => {
    const roster = await client.getAgentRoster();
    expect(roster.simple).toMatchObject({ bindingId: target.bindingId, modelId: target.modelId });
  });
  await waitFor(() => expect(screen.getByRole("button", { name: "保存 Agent 团队" })).toBeDisabled());
});
