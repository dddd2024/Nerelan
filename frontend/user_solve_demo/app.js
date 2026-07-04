const EMBEDDED_FIXTURES = {
  fixtures: [
    {
      fixture_name: "candidate",
      ui_state: {
        display_state: "candidate_pending_validation",
        tone: "attention",
        label: "Candidate pending validation",
        next_action_kind: "validate_candidate"
      },
      response: {
        status: "candidate_found",
        validation_status: "pending",
        evidence_status: "building",
        public_message: "Offline fixture preview only.",
        answer: "flag{demo_candidate}",
        candidates: [{ value: "flag{demo_candidate}", confidence: 0.64, validation_status: "pending" }],
        next_action: { kind: "validate_candidate", label: "Validate the candidate before final acceptance." },
        fallback_summary: { executed: false, selected_step: { name: "fast_strings" }, missing_evidence: [] }
      }
    },
    {
      fixture_name: "missing-evidence",
      ui_state: {
        display_state: "needs_more_evidence",
        tone: "info",
        label: "Needs more evidence",
        next_action_kind: "fallback"
      },
      response: {
        status: "deep_analysis_running",
        validation_status: "unavailable",
        evidence_status: "building",
        public_message: "More evidence is needed before a final answer can be verified.",
        candidates: [],
        next_action: { kind: "fallback", label: "Collect more evidence with fast_strings." },
        fallback_summary: { executed: false, selected_step: { name: "fast_strings" }, missing_evidence: ["targeted_decompile_missing"] }
      }
    },
    {
      fixture_name: "blocked",
      ui_state: {
        display_state: "blocked",
        tone: "blocked",
        label: "Blocked",
        next_action_kind: "blocked"
      },
      response: {
        status: "blocked",
        validation_status: "unavailable",
        evidence_status: "failed",
        public_message: "The fixture is blocked by a policy or environment requirement.",
        candidates: [],
        next_action: { kind: "blocked", label: "Resolve the blocking condition before continuing." },
        fallback_summary: { executed: false, selected_step: null, missing_evidence: [] }
      }
    },
    {
      fixture_name: "failed",
      ui_state: {
        display_state: "failed",
        tone: "danger",
        label: "Failed",
        next_action_kind: "review"
      },
      response: {
        status: "failed",
        validation_status: "unavailable",
        evidence_status: "partial",
        public_message: "No candidate answer was found in the supplied fixture.",
        candidates: [],
        next_action: { kind: "review", label: "Review the supplied analysis result." },
        fallback_summary: { executed: false, selected_step: { name: "fast_strings" }, missing_evidence: [] }
      }
    },
    {
      fixture_name: "verified",
      ui_state: {
        display_state: "verified",
        tone: "success",
        label: "Verified",
        next_action_kind: "return_answer"
      },
      response: {
        status: "verified",
        validation_status: "passed",
        evidence_status: "complete",
        public_message: "A supplied fixture candidate has passed validation evidence.",
        answer: "flag{demo_verified}",
        candidates: [{ value: "flag{demo_verified}", confidence: 0.98, validation_status: "passed" }],
        next_action: { kind: "return_answer", label: "Return the verified answer." },
        fallback_summary: { executed: false, selected_step: { name: "fast_strings" }, missing_evidence: [] }
      }
    }
  ]
};

let demoFixtures = EMBEDDED_FIXTURES.fixtures;

const title = document.querySelector("#fixtureTitle");
const message = document.querySelector("#message");
const stateLabel = document.querySelector("#stateLabel");
const validationLabel = document.querySelector("#validationLabel");
const statusValue = document.querySelector("#statusValue");
const evidenceValue = document.querySelector("#evidenceValue");
const nextActionValue = document.querySelector("#nextActionValue");
const candidateValue = document.querySelector("#candidateValue");
const fallbackValue = document.querySelector("#fallbackValue");
const buttons = Array.from(document.querySelectorAll("[data-fixture]"));

function formatName(name) {
  return name
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function renderFixture(name) {
  const fixture = demoFixtures.find((item) => item.fixture_name === name) || demoFixtures[0];
  const response = fixture.response;
  const uiState = fixture.ui_state;
  const candidate = response.answer || (response.candidates && response.candidates[0] && response.candidates[0].value) || "None";
  const fallback = response.fallback_summary && response.fallback_summary.selected_step
    ? response.fallback_summary.selected_step.name
    : "None";

  title.textContent = formatName(fixture.fixture_name);
  message.textContent = response.public_message || "";
  stateLabel.textContent = uiState.label;
  stateLabel.className = `state-label ${uiState.tone}`;
  validationLabel.textContent = response.validation_status || "not_started";
  statusValue.textContent = response.status || "ready";
  evidenceValue.textContent = response.evidence_status || "none";
  nextActionValue.textContent = (response.next_action && response.next_action.kind) || "review";
  candidateValue.textContent = candidate;
  fallbackValue.textContent = fallback;

  buttons.forEach((button) => {
    button.classList.toggle("active", button.dataset.fixture === fixture.fixture_name);
  });
}

async function loadFixtures() {
  try {
    const response = await fetch("fixtures/catalog.json", { cache: "no-store" });
    if (!response.ok) return;
    const payload = await response.json();
    if (Array.isArray(payload.fixtures) && payload.fixtures.length > 0) {
      demoFixtures = payload.fixtures;
    }
  } catch {
    demoFixtures = EMBEDDED_FIXTURES.fixtures;
  }
}

buttons.forEach((button) => {
  button.addEventListener("click", () => renderFixture(button.dataset.fixture));
});

loadFixtures().finally(() => renderFixture("candidate"));
