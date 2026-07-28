/**
 * The module registry is the platform's integration contract on the
 * frontend: the launcher, the router, and the navigation are all generated
 * from it. These tests pin the parts other teams depend on, so a bad edit
 * fails in CI rather than silently removing someone's module from the app.
 */
import { describe, expect, it } from "vitest";
import { MODULES, MODULE_STATUS, allModuleRoutes, getModule, moduleRoutes } from "./registry.js";

describe("MODULES", () => {
  it("declares exactly the three platform modules", () => {
    expect(MODULES).toHaveLength(3);
    expect(MODULES.map((m) => m.moduleNumber).sort()).toEqual([1, 2, 3]);
  });

  it("uses the agreed display names", () => {
    // These are user-visible and referenced in the demo script — a rename
    // should be a deliberate edit here, not a side effect of a refactor.
    expect(MODULES.map((m) => m.name)).toEqual([
      "CasePrep with AI",
      "CaseRepository",
      "Peer2Peer Group",
    ]);
  });

  it("attributes each module to its owning team", () => {
    expect(getModule("case-prep").team).toBe("Team 1");
    expect(getModule("case-repository").team).toBe("Team 2");
    expect(getModule("peer2peer").team).toBe("Team 3");
  });

  it("gives every module the fields the launcher renders", () => {
    for (const module of MODULES) {
      expect(typeof module.id).toBe("string");
      expect(module.id).not.toBe("");
      expect(typeof module.name).toBe("string");
      expect(typeof module.description).toBe("string");
      expect(module.description.length).toBeGreaterThan(0);
      expect(typeof module.team).toBe("string");
      expect(typeof module.Component).toBe("function");
      expect(module.path.startsWith("/")).toBe(true);
    }
  });

  it("only uses known status values", () => {
    const allowed = Object.values(MODULE_STATUS);
    for (const module of MODULES) {
      expect(allowed).toContain(module.status);
    }
  });

  it("has unique ids and landing paths", () => {
    expect(new Set(MODULES.map((m) => m.id)).size).toBe(MODULES.length);
    expect(new Set(MODULES.map((m) => m.path)).size).toBe(MODULES.length);
  });

  it("marks Module 2 live, since it is implemented", () => {
    expect(getModule("case-repository").status).toBe(MODULE_STATUS.LIVE);
  });
});

describe("moduleRoutes", () => {
  it("puts the landing route first", () => {
    const module = getModule("case-repository");
    expect(moduleRoutes(module)[0].path).toBe(module.path);
  });

  it("includes a module's extra screens", () => {
    const paths = moduleRoutes(getModule("case-repository")).map((r) => r.path);
    expect(paths).toContain("/dashboard");
    expect(paths).toContain("/upload");
    expect(paths).toContain("/cases/:id");
  });

  it("handles a module with no extra routes", () => {
    expect(moduleRoutes(getModule("peer2peer"))).toHaveLength(1);
  });

  it("does not fail when routes is undefined", () => {
    // Guards the `?? []` in moduleRoutes: a team adding an entry without a
    // routes key should not blank the whole app with a TypeError.
    const bare = { path: "/x", Component: () => null };
    expect(moduleRoutes(bare)).toHaveLength(1);
  });
});

describe("allModuleRoutes", () => {
  it("returns a usable route for every module", () => {
    const routes = allModuleRoutes();
    for (const module of MODULES) {
      expect(routes.some((r) => r.path === module.path)).toBe(true);
    }
    for (const route of routes) {
      expect(typeof route.Component).toBe("function");
    }
  });

  it("never registers the same path twice", () => {
    // Two modules claiming one path means React Router silently renders
    // only the first — the second team's screen just never appears.
    const paths = allModuleRoutes().map((r) => r.path);
    expect(new Set(paths).size).toBe(paths.length);
  });
});

describe("getModule", () => {
  it("finds a module by id", () => {
    expect(getModule("peer2peer").name).toBe("Peer2Peer Group");
  });

  it("returns undefined for an unknown id", () => {
    expect(getModule("nope")).toBeUndefined();
  });
});
