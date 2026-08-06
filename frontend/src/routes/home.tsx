import { Navigate } from "react-router";

/**
 * OpenHands HomeScreen adaptation.
 *
 * Upstream source:
 *   frontend/src/routes/home.tsx (tag 1.8.0)
 *   — `px-0 pt-4 bg-transparent h-full flex flex-col
 *      rounded-xl lg:px-[42px] lg:pt-[42px]`
 *   — HomeHeader (GuideMessage + HomeHeaderTitle)
 *   — NewConversation card
 *   — RecentConversations section
 *
 * Structurally ported: home page shows a header, the NewTaskComposer
 * as a "Start from scratch" card, and the TaskInbox as a recent
 * conversations list. Dark background with rounded corners.
 *
 * Modifications: reverse-agent task model instead of OpenHands
 * conversations; no repo connector (fixture-driven).
 * License: MIT (inherited from OpenHands)
 */
export function HomePage() {
  return <Navigate to="/tasks" replace />;
}
