import "./index.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { HomePage } from "@/routes/home";
import { TasksPage } from "@/routes/tasks";
import { TaskDetailPage } from "@/routes/task-detail";
import { ApprovalsPage } from "@/routes/approvals";
import { SettingsPage } from "@/routes/settings";
import { InboxPage } from "@/routes/inbox";
import { RoadmapPage } from "@/routes/roadmap";
import { RunsPage } from "@/routes/runs";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
    },
  },
});

const rootEl = document.getElementById("root");
if (!rootEl) {
  throw new Error("Root element #root not found");
}

createRoot(rootEl).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/tasks/:taskId" element={<TaskDetailPage />} />
            <Route path="/approvals" element={<ApprovalsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/inbox" element={<InboxPage />} />
            <Route path="/roadmap" element={<RoadmapPage />} />
            <Route path="/runs" element={<RunsPage />} />
            <Route path="*" element={<Navigate to="/tasks" replace />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
