/**
 * Vitest setup, applied to every test file (see `test.setupFiles` in
 * vite.config.js).
 */
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  // Unmount anything a test rendered, and drop tokens, so state can't leak
  // between tests. Without this, a test that logs in changes the outcome of
  // whichever test happens to run next — the kind of failure that only
  // shows up in CI, in a different order, on someone else's PR.
  cleanup();
  localStorage.clear();
});
