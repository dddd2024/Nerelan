import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { BindingList } from "@/components/binding-list";

it("shows why a binding is never dispatched, and nothing for the others", () => {
  const base = { executorId: "opencode", connectionId: "magpie", enabled: true };
  render(<BindingList connections={[]} selectedId={null} onSelect={() => undefined} bindings={[
    { ...base, bindingId: "paid", name: "Paid", modelId: "codex/gpt-6", dispatchBlock: "provider:codex" },
    { ...base, bindingId: "ok", name: "Ok", modelId: "copilot/gpt-6" }]} />);
  expect(screen.getByTestId("binding-blocked-paid")).toHaveTextContent("这是付费订阅账号（codex）");
  expect(screen.queryByTestId("binding-blocked-ok")).toBeNull();
});
