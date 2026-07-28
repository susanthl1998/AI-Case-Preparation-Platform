/**
 * Module 1 — CasePrep with AI (Team 1). Landing screen.
 *
 * TEAM 1: replace this component's body with your real UI. The route
 * (/case-prep), authentication, navigation, and the launcher card are
 * already wired — see src/modules/registry.js.
 *
 * Backend endpoints for this module live under /api/v1/case-prep
 * (backend/app/api/v1/chat.py and interview.py). Call them through
 * `src/api/client.js`, which attaches the auth token and refreshes it on
 * a 401 — do not use bare fetch, or you lose both behaviors.
 */
import ModulePlaceholder from "../ModulePlaceholder.jsx";

export default function CasePrepHome() {
  return (
    <ModulePlaceholder
      moduleNumber={1}
      name="CasePrep with AI"
      team="Team 1"
      description="Practise cases with an AI interviewer that asks follow-ups and scores your structure."
      buildNotes={[
        "Build your screens in src/modules/casePrep/.",
        "Point registry.js at your landing component and set status to \"live\".",
        "Add extra screens to that entry's routes array — no need to edit App.jsx.",
        "Use api from src/api/client.js for requests; it handles auth for you.",
        "Cases to practise come from Module 2: GET /cases, and POST /cases/{id}/practice when a session finishes.",
      ]}
    />
  );
}
