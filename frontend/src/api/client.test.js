/**
 * Token handling and the auth interceptor.
 *
 * Every authenticated request in every module goes through this module, so
 * a regression here breaks all three teams at once — including in ways
 * that look like a backend bug.
 */
import { beforeEach, describe, expect, it } from "vitest";
import api, {
  API_BASE_URL,
  attachAuthHeader,
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "./client.js";

describe("token storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns null when nothing is stored", () => {
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });

  it("round-trips both tokens", () => {
    setTokens({ access_token: "access-1", refresh_token: "refresh-1" });
    expect(getAccessToken()).toBe("access-1");
    expect(getRefreshToken()).toBe("refresh-1");
  });

  it("keeps the existing refresh token when only an access token is given", () => {
    // This is what a successful /auth/refresh returns — it does not reissue
    // the refresh token, and discarding it would log the user out on the
    // next 401 instead of refreshing again.
    setTokens({ access_token: "access-1", refresh_token: "refresh-1" });
    setTokens({ access_token: "access-2" });

    expect(getAccessToken()).toBe("access-2");
    expect(getRefreshToken()).toBe("refresh-1");
  });

  it("clears both tokens on logout", () => {
    setTokens({ access_token: "a", refresh_token: "r" });
    clearTokens();
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });
});

describe("attachAuthHeader", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("adds a bearer header when a token is stored", () => {
    setTokens({ access_token: "abc123" });
    const config = attachAuthHeader({ headers: {} });
    expect(config.headers.Authorization).toBe("Bearer abc123");
  });

  it("sends no auth header when logged out", () => {
    const config = attachAuthHeader({ headers: {} });
    expect(config.headers.Authorization).toBeUndefined();
  });

  it("does not clobber other headers", () => {
    setTokens({ access_token: "abc123" });
    const config = attachAuthHeader({ headers: { "Content-Type": "application/json" } });
    expect(config.headers["Content-Type"]).toBe("application/json");
    expect(config.headers.Authorization).toBe("Bearer abc123");
  });

  it("tolerates a config with no headers object", () => {
    setTokens({ access_token: "abc123" });
    expect(() => attachAuthHeader({})).not.toThrow();
  });
});

describe("API base URL", () => {
  it("targets the versioned API", () => {
    // Module routers assume this prefix; dropping it 404s every request in
    // every module.
    expect(API_BASE_URL).toMatch(/\/api\/v1$/);
  });

  it("is what the shared axios instance uses", () => {
    expect(api.defaults.baseURL).toBe(API_BASE_URL);
  });

  it("does not double up slashes between host and prefix", () => {
    expect(API_BASE_URL).not.toMatch(/[^:]\/\//);
  });
});
