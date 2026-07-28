/**
 * The stand-in screen for modules still being built. It exists so all
 * three launcher cards lead somewhere real during the demo, and so the
 * owning team can see exactly where their code goes.
 */
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import CasePrepHome from "./casePrep/CasePrepHome.jsx";
import ModulePlaceholder from "./ModulePlaceholder.jsx";
import Peer2PeerHome from "./peer2peer/Peer2PeerHome.jsx";

function renderIn(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("ModulePlaceholder", () => {
  it("identifies the module and its owning team", () => {
    renderIn(
      <ModulePlaceholder moduleNumber={3} name="Peer2Peer Group" team="Team 3" description="Study groups." />
    );
    expect(screen.getByText("Peer2Peer Group")).toBeInTheDocument();
    // Match the header line as a whole rather than /Team 3/ on its own:
    // the body copy ("… Team 3 only needs to drop their screens in") also
    // contains the team name, so a loose match finds two elements.
    expect(screen.getByText("Module 3 · Team 3")).toBeInTheDocument();
  });

  it("says plainly that the module is unfinished", () => {
    renderIn(<ModulePlaceholder moduleNumber={1} name="X" team="Team 1" description="Y" />);
    expect(screen.getByText(/still in development/i)).toBeInTheDocument();
  });

  it("lists build notes when given them", () => {
    renderIn(
      <ModulePlaceholder
        moduleNumber={1}
        name="X"
        team="Team 1"
        description="Y"
        buildNotes={["First step", "Second step"]}
      />
    );
    expect(screen.getByText("First step")).toBeInTheDocument();
    expect(screen.getByText("Second step")).toBeInTheDocument();
  });

  it("renders without build notes", () => {
    expect(() =>
      renderIn(<ModulePlaceholder moduleNumber={1} name="X" team="Team 1" description="Y" />)
    ).not.toThrow();
  });

  it("offers a way back to the launcher", () => {
    renderIn(<ModulePlaceholder moduleNumber={1} name="X" team="Team 1" description="Y" />);
    expect(screen.getByRole("link", { name: /back to all modules/i })).toHaveAttribute("href", "/");
  });
});

describe("module landing screens", () => {
  it("Module 1 renders with guidance for Team 1", () => {
    renderIn(<CasePrepHome />);
    expect(screen.getByText("CasePrep with AI")).toBeInTheDocument();
    expect(screen.getByText(/src\/modules\/casePrep/)).toBeInTheDocument();
  });

  it("Module 3 renders with guidance for Team 3", () => {
    renderIn(<Peer2PeerHome />);
    expect(screen.getByText("Peer2Peer Group")).toBeInTheDocument();
    expect(screen.getByText(/src\/modules\/peer2peer/)).toBeInTheDocument();
  });
});
