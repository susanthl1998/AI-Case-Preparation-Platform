/**
 * The transparent token-refresh flow.
 *
 * Kept in its own file because it swaps the axios adapter, and because it
 * is the subtlest thing in the frontend: when it breaks, users get
 * apparently random logouts that are painful to reproduce by hand.
 *
 * The adapter is axios's pluggable transport. Replacing it means these
 * tests exercise the real interceptor chain — no network, no mocking of
 * our own code.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import api, { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./client.js";

const originalAdapter = api.defaults.adapter;

function ok(data, config) {
  return { data, status: 200, statusText: "OK", headers: {}, config, request: {} };
}

function unauthorized(config) {
  const error = new Error("Request failed with status code 401");
  error.isAxiosError = true;
  error.config = config;
  error.response = { data: {}, status: 401, statusText: "Unauthorized", headers: {}, config };
  return error;
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  api.defaults.adapter = originalAdapter;
});

describe("refresh on 401", () => {
  it("refreshes the token and retries the original request", async () => {
    setTokens({ access_token: "expired", refresh_token: "refresh-1" });

    let protectedCalls = 0;
    let refreshCalls = 0;

    api.defaults.adapter = async (config) => {
      if (config.url === "/auth/refresh") {
        refreshCalls += 1;
        return ok({ access_token: "fresh" }, config);
      }
      protectedCalls += 1;
      if (protectedCalls === 1) throw unauthorized(config);
      return ok({ items: [] }, config);
    };

    const response = await api.get("/cases");

    expect(response.data).toEqual({ items: [] });
    expect(refreshCalls).toBe(1);
    expect(protectedCalls).toBe(2);
    expect(getAccessToken()).toBe("fresh");
  });

  it("keeps the user logged in by preserving the refresh token", async () => {
    setTokens({ access_token: "expired", refresh_token: "refresh-1" });

    let protectedCalls = 0;
    api.defaults.adapter = async (config) => {
      if (config.url === "/auth/refresh") return ok({ access_token: "fresh" }, config);
      protectedCalls += 1;
      if (protectedCalls === 1) throw unauthorized(config);
      return ok({}, config);
    };

    await api.get("/cases");

    expect(getRefreshToken()).toBe("refresh-1");
  });

  it("retries only once, then gives up", async () => {
    // A server that 401s even with a fresh token must not become an
    // infinite refresh loop hammering the API.
    setTokens({ access_token: "expired", refresh_token: "refresh-1" });

    let protectedCalls = 0;
    api.defaults.adapter = async (config) => {
      if (config.url === "/auth/refresh") return ok({ access_token: "fresh" }, config);
      protectedCalls += 1;
      throw unauthorized(config);
    };

    await expect(api.get("/cases")).rejects.toBeDefined();
    expect(protectedCalls).toBe(2);
  });

  it("logs the user out when the refresh token is rejected", async () => {
    setTokens({ access_token: "expired", refresh_token: "stale" });

    api.defaults.adapter = async (config) => {
      throw unauthorized(config);
    };

    await expect(api.get("/cases")).rejects.toBeDefined();

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });

  it("does not attempt a refresh when there is no refresh token", async () => {
    clearTokens();

    let refreshCalls = 0;
    api.defaults.adapter = async (config) => {
      if (config.url === "/auth/refresh") refreshCalls += 1;
      throw unauthorized(config);
    };

    await expect(api.get("/cases")).rejects.toBeDefined();
    expect(refreshCalls).toBe(0);
  });

  it("does not refresh when login itself fails", async () => {
    // A wrong password is a 401 too. Refreshing there would swallow the
    // error the login form needs to show, and could loop.
    setTokens({ refresh_token: "refresh-1" });

    let refreshCalls = 0;
    api.defaults.adapter = async (config) => {
      if (config.url === "/auth/refresh") refreshCalls += 1;
      throw unauthorized(config);
    };

    await expect(api.post("/auth/login", {})).rejects.toBeDefined();
    expect(refreshCalls).toBe(0);
  });

  it("shares one refresh across requests that fail together", async () => {
    // A page loading several resources in parallel will 401 several times
    // at once; each firing its own refresh would race, and all but one of
    // the resulting tokens would be discarded.
    setTokens({ access_token: "expired", refresh_token: "refresh-1" });

    let refreshCalls = 0;
    const seen = {};

    api.defaults.adapter = async (config) => {
      if (config.url === "/auth/refresh") {
        refreshCalls += 1;
        return ok({ access_token: "fresh" }, config);
      }
      seen[config.url] = (seen[config.url] ?? 0) + 1;
      if (seen[config.url] === 1) throw unauthorized(config);
      return ok({ url: config.url }, config);
    };

    const [a, b, c] = await Promise.all([
      api.get("/cases"),
      api.get("/dashboard"),
      api.get("/profile/me"),
    ]);

    expect(refreshCalls).toBe(1);
    expect([a.data.url, b.data.url, c.data.url]).toEqual(["/cases", "/dashboard", "/profile/me"]);
  });

  it("propagates errors that are not 401s", async () => {
    setTokens({ access_token: "valid", refresh_token: "refresh-1" });

    let refreshCalls = 0;
    api.defaults.adapter = async (config) => {
      if (config.url === "/auth/refresh") refreshCalls += 1;
      const error = new Error("boom");
      error.isAxiosError = true;
      error.config = config;
      error.response = { data: {}, status: 500, statusText: "Server Error", headers: {}, config };
      throw error;
    };

    await expect(api.get("/cases")).rejects.toBeDefined();
    expect(refreshCalls).toBe(0);
    expect(getAccessToken()).toBe("valid");
  });
});
