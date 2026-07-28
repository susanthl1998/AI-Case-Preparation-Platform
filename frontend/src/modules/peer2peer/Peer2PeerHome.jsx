/**
 * Module 3 — Peer2Peer Group (Team 3). Landing screen.
 *
 * TEAM 3: replace this component's body with your real UI. The route
 * (/peer2peer), authentication, navigation, and the launcher card are
 * already wired — see src/modules/registry.js.
 *
 * Backend endpoints for this module live under /api/v1/peer2peer
 * (backend/app/api/v1/groups.py). Call them through `src/api/client.js`,
 * which attaches the auth token and refreshes it on a 401 — do not use
 * bare fetch, or you lose both behaviors.
 */
import ModulePlaceholder from "../ModulePlaceholder.jsx";

export default function Peer2PeerHome() {
  return (
    <ModulePlaceholder
      moduleNumber={3}
      name="Peer2Peer Group"
      team="Team 3"
      description="Form study groups and run live peer-to-peer mock interviews with other students."
      buildNotes={[
        "Build your screens in src/modules/peer2peer/.",
        "Point registry.js at your landing component and set status to \"live\".",
        "Add extra screens to that entry's routes array — no need to edit App.jsx.",
        "Use api from src/api/client.js for requests; it handles auth for you.",
        "The logged-in user is available from useAuth() in src/context/AuthContext.jsx.",
      ]}
    />
  );
}
