# Frontend

React 18 + Vite + Tailwind CSS. Currently implements Module 2's UI
(auth, onboarding, dashboard, case repository), built against
[`../docs/API/api-spec.md`](../docs/API/api-spec.md).

## Requirements

Node.js 20+

## Setup

```bash
cp .env.example .env.local   # point VITE_API_BASE_URL at your backend
npm install
npm run dev                  # http://localhost:5173
```

The backend must be running, and its `CORS_ALLOW_ORIGINS` must include this
dev server's origin. The defaults on both sides already match
(`http://localhost:5173`).

`npm install` generates `package-lock.json` on first run — commit it, so
CI can switch from `npm install` to `npm ci` with real caching.

## Building

```bash
npm run build      # → dist/
npm run preview    # serve the production build locally
```

⚠️ `VITE_API_BASE_URL` is **baked into the bundle at build time**, not read
at runtime. Set it before building; editing it afterwards does nothing
until you rebuild. This catches people out on every hosting platform.

## API calls

Everything goes through `src/api/client.js` — one axios instance that
attaches the bearer token and transparently refreshes it once on a 401.
Don't call `fetch` directly elsewhere; you'd lose both behaviors.

The `/api/v1` prefix is appended there, so `VITE_API_BASE_URL` is a plain
origin with no path, and moving to a new API version is a one-line change.

Tokens live in `localStorage`, read and written only through that module.
On a 401 from any non-auth endpoint the interceptor tries `POST
/auth/refresh` once and retries; if that also fails it clears tokens and
the next protected-route render redirects to `/login`. Parallel 401s share
one in-flight refresh rather than firing several.

## Layout

```
src/
  main.jsx              Entry — router + AuthProvider
  App.jsx               Route table (public vs. ProtectedRoute)
  api/client.js         Axios instance, tokens, refresh-on-401
  context/AuthContext.jsx
  components/
    ProtectedRoute.jsx  Redirects to /login when unauthenticated
    Navbar.jsx
    CaseCard.jsx
    EmptyState.jsx      "No cases match" + reset filters (US-04 AC)
  pages/
    Signup.jsx / Login.jsx
    Onboarding.jsx      Target firm type (mandatory) + preferences
    Dashboard.jsx       Personalized recommendations (FR-04)
    Repository.jsx      Browse / search / filter / sort (US-04)
    CaseDetail.jsx      View, share/withdraw, delete, admin moderate
    Upload.jsx          PDF upload; server-side validation is authoritative
    Profile.jsx         Edit profile, delete account
```

## Adding pages for another module

Add your pages under `src/pages/` and routes in `App.jsx`. Reuse
`src/api/client.js` rather than creating a second axios instance —
otherwise your requests won't carry auth tokens or benefit from the refresh
logic.

## Known limitations (v1.0, matching the PRD's non-goals)

No OAuth login, no case ratings or comments, no bookmarking UI, no native
mobile app (the layout is responsive per NFR-03, but this is a web app).
