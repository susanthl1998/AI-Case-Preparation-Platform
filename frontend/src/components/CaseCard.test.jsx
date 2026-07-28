/**
 * Case cards and the empty state — both encode US-04 acceptance criteria,
 * so these tests double as a check that the AC still holds.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import CaseCard from "./CaseCard.jsx";
import EmptyState from "./EmptyState.jsx";

const aCase = {
  id: 7,
  title: "BrightBrew Coffee Co.",
  case_type: "MERGERS_ACQUISITIONS",
  difficulty: "HARD",
  industry: "Retail",
  contributor: "Jane D.",
  practice_count: 4,
};

function renderCard(overrides = {}) {
  return render(
    <MemoryRouter>
      <CaseCard caseItem={{ ...aCase, ...overrides }} />
    </MemoryRouter>
  );
}

describe("CaseCard", () => {
  it("shows title, case type, difficulty and contributor", () => {
    // US-04 AC, verbatim: these four fields are the requirement.
    renderCard();
    expect(screen.getByText("BrightBrew Coffee Co.")).toBeInTheDocument();
    expect(screen.getByText(/M&A/)).toBeInTheDocument();
    expect(screen.getByText("HARD")).toBeInTheDocument();
    expect(screen.getByText(/Jane D\./)).toBeInTheDocument();
  });

  it("links to the case detail page", () => {
    renderCard();
    expect(screen.getByRole("link")).toHaveAttribute("href", "/cases/7");
  });

  it("shows the industry when there is one", () => {
    renderCard();
    expect(screen.getByText(/Retail/)).toBeInTheDocument();
  });

  it("omits the industry separator when there is none", () => {
    renderCard({ industry: null });
    expect(screen.queryByText(/·/)).not.toBeInTheDocument();
  });

  it("falls back to the raw case type if it is not in the label map", () => {
    // A new taxonomy value added backend-first must not render blank.
    renderCard({ case_type: "SOMETHING_NEW" });
    expect(screen.getByText(/SOMETHING_NEW/)).toBeInTheDocument();
  });

  it("pluralises the practice count", () => {
    renderCard({ practice_count: 1 });
    expect(screen.getByText("1 practice")).toBeInTheDocument();
  });

  it("uses the plural form for zero", () => {
    renderCard({ practice_count: 0 });
    expect(screen.getByText("0 practices")).toBeInTheDocument();
  });
});

describe("EmptyState", () => {
  it("shows a default message", () => {
    render(<EmptyState />);
    expect(screen.getByText(/no cases match/i)).toBeInTheDocument();
  });

  it("shows a custom message when given one", () => {
    render(<EmptyState message="Nothing here yet." />);
    expect(screen.getByText("Nothing here yet.")).toBeInTheDocument();
  });

  it("offers a reset when a handler is supplied", async () => {
    // US-04 AC: an empty result must offer a way to reset the filters.
    const onReset = vi.fn();
    render(<EmptyState onReset={onReset} />);

    await userEvent.click(screen.getByRole("button", { name: /reset filters/i }));
    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it("hides the reset button when there is nothing to reset", () => {
    render(<EmptyState />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
