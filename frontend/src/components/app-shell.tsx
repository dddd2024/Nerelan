import { useState, type ReactNode } from "react";
import { Sidebar } from "@/components/sidebar";
import { ConversationPanel } from "@/components/conversation-panel";
import { NewTaskComposer } from "@/components/new-task-composer";
import { cn } from "@/lib/cn";

interface AppShellProps {
  children: ReactNode;
}

/**
 * OpenHands 1.8.0 root-layout adaptation.
 *
 * Upstream source:
 *   frontend/src/routes/root-layout.tsx (tag 1.8.0)
 *   - fixed 75px icon sidebar (`md:w-[75px] md:min-w-[75px]`)
 *   - main workspace `flex flex-col w-full min-w-0 h-full gap-3`
 *   - dark bg-base (#0D0F11), overflow-hidden
 *
 * Structurally ported: the sidebar is a fixed-width vertical icon bar.
 * The conversation panel (task list) is rendered as an overlay via
 * ConversationPanelWrapper, identical to OpenHands' portal pattern.
 * A NewTaskComposer is rendered at the bottom of the workspace, mirroring
 * the OpenHands `InteractiveChatBox` / `CustomChatInput` dock.
 *
 * Modifications: OpenHands branding, agent runtime, sandbox, and
 * conversation APIs replaced with fixture-driven reverse-agent domain
 * (Task / Authority / Policy). No server, websocket, or sandbox code.
 */
export function AppShell({ children }: AppShellProps) {
  const [conversationPanelOpen, setConversationPanelOpen] =
    useState(false);
  const [newTaskComposerOpen, setNewTaskComposerOpen] = useState(false);

  return (
    <div
      data-testid="app-shell"
      className={cn(
        "h-screen flex flex-col md:flex-row bg-ra-base overflow-hidden",
      )}
    >
      <Sidebar
        onNewTask={() => setNewTaskComposerOpen(true)}
        onOpenConversationPanel={() => setConversationPanelOpen(true)}
        onConversationPanelClose={() => setConversationPanelOpen(false)}
        conversationPanelOpen={conversationPanelOpen}
      />

      <div className="flex flex-col w-full min-w-0 flex-1 h-[calc(100%-54px)] md:h-full gap-3">
        <div
          data-testid="workspace-outlet"
          className="flex-1 relative overflow-auto custom-scrollbar"
        >
          {children}
        </div>

        {newTaskComposerOpen && (
          <NewTaskComposer
            open={newTaskComposerOpen}
            onClose={() => setNewTaskComposerOpen(false)}
          />
        )}
      </div>

      <ConversationPanel
        open={conversationPanelOpen}
        onClose={() => setConversationPanelOpen(false)}
      />
    </div>
  );
}
