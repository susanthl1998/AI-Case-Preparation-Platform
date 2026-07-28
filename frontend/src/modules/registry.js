/**
 * The single source of truth for the platform's three modules.
 *
 * Both the post-login launcher (`src/pages/Home.jsx`) and the router
 * (`src/App.jsx`) are generated from this list, so adding a module's UI
 * means editing this file — not hunting through the router and the
 * navigation separately and getting them out of sync.
 *
 * ── How to plug in your module ─────────────────────────────────────────
 *
 * 1. Build your screens under `src/modules/<yourModule>/`.
 * 2. Import your landing component below and set it as `Component`.
 * 3. Add any extra screens to that module's `routes` array.
 * 4. Flip `status` from "planned" to "live".
 *
 * That's it — the launcher card, the routing, and the navigation all
 * follow automatically. You should not need to touch `App.jsx`,
 * `Home.jsx`, or `Navbar.jsx`.
 *
 * Every route listed here is already behind authentication, so your
 * components can assume a logged-in user (read it from `useAuth()`).
 *
 * Shape of an entry:
 *   id           stable slug, used as a React key and in tests
 *   moduleNumber 1 | 2 | 3
 *   name         display name on the launcher card
 *   team         who owns it
 *   description  one line, shown on the card
 *   path         landing route for the module
 *   Component    landing component (capitalized — it is a component)
 *   status       "live" | "planned"; "planned" renders a muted card
 *   routes       additional [{ path, Component }] screens
 */
import CasePrepHome from "./casePrep/CasePrepHome.jsx";
import Peer2PeerHome from "./peer2peer/Peer2PeerHome.jsx";

import CaseDetail from "../pages/CaseDetail.jsx";
import Dashboard from "../pages/Dashboard.jsx";
import Repository from "../pages/Repository.jsx";
import Upload from "../pages/Upload.jsx";

export const MODULE_STATUS = {
  LIVE: "live",
  PLANNED: "planned",
};

export const MODULES = [
  {
    id: "case-prep",
    moduleNumber: 1,
    name: "CasePrep with AI",
    team: "Team 1",
    description:
      "Practise cases with an AI interviewer that asks follow-ups and scores your structure.",
    path: "/case-prep",
    Component: CasePrepHome,
    status: MODULE_STATUS.PLANNED,
    routes: [],
  },
  {
    id: "case-repository",
    moduleNumber: 2,
    name: "CaseRepository",
    team: "Team 2",
    description:
      "Browse, search, and filter the shared case library, or upload and share your own cases.",
    path: "/repository",
    Component: Repository,
    status: MODULE_STATUS.LIVE,
    routes: [
      { path: "/dashboard", Component: Dashboard },
      { path: "/upload", Component: Upload },
      { path: "/cases/:id", Component: CaseDetail },
    ],
  },
  {
    id: "peer2peer",
    moduleNumber: 3,
    name: "Peer2Peer Group",
    team: "Team 3",
    description:
      "Form study groups and run live peer-to-peer mock interviews with other students.",
    path: "/peer2peer",
    Component: Peer2PeerHome,
    status: MODULE_STATUS.PLANNED,
    routes: [],
  },
];

/** Every route a module contributes: its landing route plus any extras. */
export function moduleRoutes(module) {
  return [{ path: module.path, Component: module.Component }, ...(module.routes ?? [])];
}

/** Flat list of all module routes, for the router. */
export function allModuleRoutes() {
  return MODULES.flatMap(moduleRoutes);
}

export function getModule(id) {
  return MODULES.find((m) => m.id === id);
}
