/**
 * The authentication gate. Every module's screens sit behind it, so a
 * regression here either locks everyone out or — worse — lets anonymous
 * users reach authenticated pages.
 */
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import ProtectedRoute from "./ProtectedRoute.jsx";

const mockUseAuth = vi.fn();
vi.mock("../context/AuthContext.jsx", () => ({
  useAuth: () => mockUseAuth(),
}));

function renderAt(path = "/secret") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/login" element={<div>Login page</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/secret" element={<div>Secret content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  it("renders the page for a signed-in user", () => {
    mockUseAuth.mockReturnValue({ user: { id: 1, email: "a@b.com" }, loading: false });
    renderAt();
    expect(screen.getByText("Secret content")).toBeInTheDocument();
  });

  it("redirects to login when signed out", () => {
    mockUseAuth.mockReturnValue({ user: null, loading: false });
    renderAt();
    expect(screen.getByText("Login page")).toBeInTheDocument();
    expect(screen.queryByText("Secret content")).not.toBeInTheDocument();
  });

  it("waits while the session is still being restored", () => {
    // Without this, a page refresh briefly sees user=null and bounces the
    // user to /login before /auth/me has had a chance to answer.
    mockUseAuth.mockReturnValue({ user: null, loading: true });
    renderAt();
    expect(screen.queryByText("Login page")).not.toBeInTheDocument();
    expect(screen.queryByText("Secret content")).not.toBeInTheDocument();
  });
});
