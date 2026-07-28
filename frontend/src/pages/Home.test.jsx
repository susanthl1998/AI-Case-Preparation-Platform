/**
 * The post-login launcher. This is the screen that proves the platform is
 * one product rather than three projects, so its contents are worth
 * pinning down.
 */
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { MODULES } from "../modules/registry.js";
import Home from "./Home.jsx";

function renderHome() {
  return render(
    <MemoryRouter>
      <Home />
    </MemoryRouter>
  );
}

describe("Home", () => {
  it("shows a card for all three modules", () => {
    renderHome();
    for (const module of MODULES) {
      expect(screen.getByTestId(`module-card-${module.id}`)).toBeInTheDocument();
    }
  });

  it("names each module", () => {
    renderHome();
    expect(screen.getByText("CasePrep with AI")).toBeInTheDocument();
    expect(screen.getByText("CaseRepository")).toBeInTheDocument();
    expect(screen.getByText("Peer2Peer Group")).toBeInTheDocument();
  });

  it("links each card to its module's route", () => {
    renderHome();
    for (const module of MODULES) {
      const card = screen.getByTestId(`module-card-${module.id}`);
      expect(card).toHaveAttribute("href", module.path);
    }
  });

  it("credits the owning team on each card", () => {
    renderHome();
    for (const module of MODULES) {
      const card = screen.getByTestId(`module-card-${module.id}`);
      expect(within(card).getByText(module.team)).toBeInTheDocument();
    }
  });

  it("distinguishes available modules from ones still being built", () => {
    renderHome();
    const repository = screen.getByTestId("module-card-case-repository");
    expect(within(repository).getByText("Available")).toBeInTheDocument();

    const casePrep = screen.getByTestId("module-card-case-prep");
    expect(within(casePrep).getByText("In development")).toBeInTheDocument();
  });

  it("renders whatever the registry declares, not a hardcoded list", () => {
    // The launcher must stay generated: when Team 1 or Team 3 flips their
    // module to live, this page has to follow without being edited.
    renderHome();
    const cards = screen.getAllByTestId(/^module-card-/);
    expect(cards).toHaveLength(MODULES.length);
  });
});
