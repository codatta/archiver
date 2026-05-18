# Humanbased Developer Portal

**Production:** [developer.humanbased.ai](https://developer.humanbased.ai) · [api.humanbased.ai](https://api.humanbased.ai) · [docs.humanbased.ai](https://docs.humanbased.ai)

---

## Mission

**Humanbased** (prev. Codatta) is a two-sided marketplace for human-executed tasks. Organizations on the demand side need reliable, high-quality human work at scale — data annotation, field verification, surveys, content moderation, and any task that requires a credentialed person. A distributed workforce on the supply side completes these tasks, validated by multi-contributor consensus and (in later phases) anchored on-chain for provenance.

The **Developer Portal** is the demand-side command center. It gives organizations a self-service path from sign-up to live data in minutes — no sales calls, no integration meetings. Browse available data verticals, subscribe, pull validated results via API, and manage quality through adopt/dispute decisions that directly affect your balance.

### Why this matters

| For developers | For the platform |
|---------------|-----------------|
| Programmatic access to human-validated data via REST API, CLI, and MCP server | Self-service reduces support overhead to near zero |
| Transparent quality (consensus scores, validator counts, per-item audit) | Financial lifecycle (freeze/settle/refund) automates revenue collection |
| Sandbox mode for risk-free integration testing | Usage data informs supply allocation and pricing |

> For the full business context and domain model, see [`prod_overview.md`](./prod_overview.md).

---

## Phased Rollout

The developer portal is being built and released in phases. Each phase is self-contained — it ships value on its own and lays the foundation for the next.

| Phase | Name | Status | What it delivers |
|-------|------|--------|-----------------|
| **V1** | Data consumption | **Shipped** | Auth, onboarding, dashboard, API key management, subscription + pull model, adopt/dispute, Stripe billing, CLI, MCP server, sandbox/production modes |
| **V1.x** | UX hardening | **In progress** | Password strength module, skippable onboarding, real-time availability checks, OAuth sign-in (GitHub + HuggingFace), production reliability fixes |
| **Phase 0** | Campaign foundation | Planned | Campaign/task/instance schema, minimal CRUD API — prerequisite for all campaign work |
| **Phase 1** | Pre-set campaign launch | Planned | End-to-end campaign launch with hard-coded templates (robotics video, supply + annotation), fixed UI, off-chain data lineage |
| **Phase 2** | Campaign management | Planned | Campaign lifecycle (pause, resume, cancel), progress tracking, result export |
| **Phase 3** | Dynamic campaign builder | Planned | Custom task DAGs, configurable quality gates, parameter templates |
| **Phase 4** | Compensation & trust | Planned | Contributor compensation models, KYB/trust tier gating, per-vertical pricing |
| **Phase 5** | On-chain anchoring | Planned | Task instance lineage written on-chain for provenance and auditability |

**Detailed specs:**
- V1 features and build queue: [`prd.md`](./prd.md)
- Campaign launch phases 0–5: [`campaign-launch-roadmap.md`](./campaign-launch-roadmap.md)
- Domain model and vision (upstream): [`codatta/huge_leap`](https://github.com/codatta/huge_leap) — `docs/model/prd.md`, `docs/specs/developer-portal.md`, `docs/specs/data-lineage.md`
- Team collaboration model: [`ai-native-collaboration.md`](./ai-native-collaboration.md)

---

## What Is This?

The **Developer Portal** is the self-service interface for organizations that consume data from the Humanbased platform. It covers the full lifecycle of data consumption: discovering data sources, subscribing, pulling data via API, reviewing quality, managing your team and API keys, and handling billing — all without needing to talk to anyone.

**Design principle: self-service.** Everything an org needs to go from sign-up to pulling live data should be completable in the portal without any manual intervention from the Humanbased team.

**Scope: demand side only.** This portal serves data consumers (developers, orgs). It does not serve human workers (they have a separate app) and is not an internal admin panel.

### What the portal covers

| Area | What it does |
|------|-------------|
| **Task launching** | Browse data frontiers (verticals), subscribe, pull incoming results |
| **Data management** | Adopt or dispute received data items; account balance reflects each decision |
| **Access control** | API keys with scoped permissions, per-member roles, domain-gated org membership |
| **Team management** | Member invites (email + domain allowlist), role assignment, pending invitations |
| **Billing** | Stripe-funded balance, freeze-on-receive, settle-on-adopt, refund-on-dispute |
| **Programmatic access** | REST API, CLI (`@humanbased/cli`), MCP server |

---

## Sandbox vs. Production

The portal runs in two modes, switchable via the toggle in the top bar:

| | Sandbox | Production |
|-|---------|------------|
| **Data source** | Simulated — replays real payload shapes with mock values | Live — real submissions from AliCloud PolarDB (via VPS proxy) |
| **Billing** | Not active | Balance freezes/settles on adopt/dispute |
| **Use case** | Integration testing, onboarding | Actual data consumption |

Sandbox mode is safe to use for testing API key wiring and subscription flows. Switch to production when you want real data.

---

## What Has Been Built

### Primary use case: consuming live and historical data via API

The main workflow today:

1. Sign up → create org → generate API key
2. Browse frontiers in the dashboard, subscribe to a data source
3. Pull data via the REST API using your API key:

```bash
curl "https://api.humanbased.ai/v1/live/pull?subscription_id=<id>&limit=50" \
  -H "Authorization: Bearer hb_live_sk_..."
```

4. For each item received, either adopt or dispute it.

### Data lifecycle: arrival → dispute → adopted

```
Submission arrives
       │
       ▼
  Delivered to org (balance frozen)
       │
       ├─── Dispute ──► Dispute review process
       │                      │
       │                      ├─ Upheld → balance refunded, item removed
       │                      └─ Rejected → item adopted, balance settled
       │
       └─── Adopt ───► Balance settled, item owned
                (auto-adopt after 48h if no action taken)
```

**Dispute resolution process:**
- Consumer calls `POST /v1/live/items/{id}/dispute` with an optional reason
- Dispute is logged in `consumer_feedback` (Supabase)
- A frozen balance hold is created for the disputed item
- Future: dispute triggers re-audit on the supply side; outcome updates the balance

**Account balance reflection:**
- Item delivered → amount **frozen** (not yet settled)
- Adopt (manual or auto after 48h) → frozen amount **settled** (deducted)
- Dispute upheld → frozen amount **released** (refunded)
- The Overview dashboard shows: available balance, frozen amount, total funded

### Other completed features

- **Social sign-in:** GitHub OAuth (Supabase native) + HuggingFace OAuth (custom backend OIDC flow) — see [OAuth Setup](#oauth-setup) below
- Email/password auth with Supabase; OTP email verification flow
- 3-step onboarding: org setup, member invites, first API key
- Auto-join on signup for orgs with domain allowlist configured
- Batched invite notification emails (5-min debounce, single summary per inviter)
- Invitation awareness: UI shows "Existing user" vs "New user" badge on invite form
- API key management: masked display, creation banner (shown once), revoke
- Org settings: name, slug, email, domain allowlist, danger zone
- Full member management: invite, role change (owner/admin/member), revoke invitation

---

## What Has Not Been Used in Production Yet

| Feature | Status | Notes |
|---------|--------|-------|
| **Supabase supply schema** (`supply.*` tables) | Schema created, migration partial | `domains.py` / `live_data.py` still query AliCloud MySQL. Will switch when staging pipeline validates parity. |
| **Stripe billing** | Test mode only | Keys are `sk_test_*`. No real charges yet. |
| **Webhook endpoints** | Table exists | Delivery webhooks not yet wired |
| **Task launching** | Not implemented | Subscriptions are read-only pull today; pushing tasks to workers is future scope |
| **Data marketplace** | Not started | Listing owned data for resale is V2+ |
| **MCP server** (`packages/mcp/`) | Built, not deployed | Works locally; no production endpoint |

---

## System Architecture

### Hybrid data backend

```
Developer Portal (frontend)
        │
        ▼
 API — api.humanbased.ai (Google Cloud Run)
        │
        ├── Supabase Postgres ──── Users, orgs, API keys, subscriptions,
        │   (project uxafd...)      billing, invitations, consumer feedback
        │
        └── AliCloud PolarDB ───── Frontier definitions, tasks, submissions,
            (MySQL, read-only)      audit records  ← LIVE PRODUCTION DATA
            via DigitalOcean VPS
            proxy (socat)
```

**Why hybrid?** Supabase handles all demand-side state (auth, keys, billing). The supply-side annotation data lives in AliCloud PolarDB (`cfp_metacore`) which is the source of truth for what contributors submitted. The API reads supply data via a DigitalOcean VPS proxy because Cloud Run IPs are dynamic and can't be whitelisted in AliCloud.

**Future:** A full migration of supply-side tables into Supabase's `supply` schema is in progress (PR #48 created the schema; data migration is partial). This migration will be completed and validated once a staging environment is available.

### Monorepo structure

| Package | Purpose | Stack |
|---------|---------|-------|
| `packages/webapp/` | Frontend portal | React 19, Tailwind CSS, Bun HTML imports |
| `packages/api/` | REST API | Python, FastAPI, uvicorn, uv |
| `packages/cli/` | CLI tool (`@humanbased/cli`) | TypeScript, Bun |
| `packages/mcp/` | MCP server | TypeScript |
| `packages/docs/` | Documentation site | Next.js, MDX |
| `shared/` | Shared TypeScript types | TypeScript |

---

## System Responsibilities

The Developer Portal is composed of three runtime services, each with a clear responsibility:

| Service | Responsibility |
|---------|---------------|
| **Webapp** (`packages/webapp/`) | All UI rendering, client-side routing, and user interactions. Static SPA served by Vercel. Calls the API for all data. |
| **API** (`packages/api/`) | Authentication, authorization, business logic, database access, Stripe billing, email delivery. The single backend for all clients (webapp, CLI, MCP). |
| **Docs** (`packages/docs/`) | Public developer documentation. Independent deployment — no runtime dependency on the API. |

Key invariants:
- The webapp **never** talks to databases directly — all data flows through the API.
- The API is the **single source of truth** for auth (Supabase), billing (Stripe), and supply-side data (AliCloud PolarDB via VPS proxy).
- Environment-specific configuration (API URL, Supabase keys) is injected at build time via `scripts/inject-env.ts` — the webapp has no hardcoded dependency on any single environment.

---

## Deployment

### Environments

| Environment | Branch | Webapp URL | API URL | Purpose |
|-------------|--------|-----------|---------|---------|
| **Production** | `main` | [developer.humanbased.ai](https://developer.humanbased.ai) | [api.humanbased.ai](https://api.humanbased.ai) | Live traffic |
| **Staging** | `staging` | [staging.developer.humanbased.ai](https://staging.developer.humanbased.ai) | [staging.api.humanbased.ai](https://staging.api.humanbased.ai) | Pre-production validation |
| **Local dev** | any | `localhost:3000` | `localhost:8001` | Development |

### Runtime environment injection

The webapp resolves `API_URL`, `SUPABASE_URL`, and `SUPABASE_PUBLISHABLE_KEY` at runtime via `window.__ENV__`:

| Layer | How env vars are injected |
|-------|--------------------------|
| **Vercel build** (staging/prod) | `scripts/inject-env.ts` runs post-build: reads `process.env`, writes `dist/env.js`, injects `<script>` into `dist/index.html` |
| **Local dev** | `server.ts` serves `/env.js` dynamically from `process.env`; `main.tsx` loads it before rendering |

Key env vars to configure per environment:

| Variable | Vercel (Preview) | Vercel (Production) | Cloud Run |
|----------|-----------------|--------------------|----|
| `API_URL` | `https://staging.api.humanbased.ai` | `https://api.humanbased.ai` | `https://api.humanbased.ai` |
| `SUPABASE_URL` | (shared) | (shared) | (shared) |
| `SUPABASE_PUBLISHABLE_KEY` | (shared) | (shared) | — |

### Policy

- **`main` is protected.** All work happens on feature branches. PRs require approval from **@beingzy** before merge. No direct commits to `main`.
- **Production deploys automatically** on merge to `main` via GitHub Actions (no manual step needed).
- **Staging deploys automatically** on push to the `staging` branch via Vercel preview deployments and Cloud Run staging service.

### CI/CD

| Package | Platform | Staging trigger | Production trigger |
|---------|----------|----|-----|
| `packages/webapp/` | Vercel | Push to `staging` → `staging.developer.humanbased.ai` | Push to `main` → `developer.humanbased.ai` |
| `packages/api/` | Google Cloud Run (`asia-northeast1`) | Push to `staging` → `staging.api.humanbased.ai` | Push to `main` → `api.humanbased.ai` |
| `packages/docs/` | Vercel | Push to `staging` → preview URL | Push to `main` → `docs.humanbased.ai` |

### Manual trigger (when CI doesn't auto-fire)

```bash
gh workflow run deploy-webapp.yml --ref main
gh workflow run deploy-api.yml --ref main
```

---

## Development

### Prerequisites

- [Bun](https://bun.sh) >= 1.1
- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Quick start

```bash
# Install all dependencies
cd packages/webapp && bun install
cd packages/api && uv sync

# Run both servers from repo root
bun run dev
# webapp → localhost:3000   API → localhost:8000

# Frontend only (points at production API by default)
cd packages/webapp && bun run dev

# Frontend pointing at local API
cd packages/webapp && bun run dev:local-api
# Sets API_URL=http://localhost:8001 → served via /env.js
```

### Quality gate (must pass before every commit)

```bash
# API
cd packages/api && uv run ruff check . && uv run pytest

# Webapp
cd packages/webapp && bun run build && bun test
```

---

## OAuth Setup

The portal supports three sign-in methods: **email + password**, **GitHub**, and **HuggingFace**. GitHub uses Supabase's native OAuth provider. HuggingFace uses a custom backend OIDC flow (`packages/api/app/routes/auth_hf.py`).

### Provider configuration per environment

| Provider | Config location | Production | Staging |
|----------|----------------|------------|---------|
| **GitHub** | Supabase Dashboard → Providers | Shared — one GitHub OAuth App, callback to Supabase | Same (shared Supabase project) |
| **HuggingFace** | Cloud Run env vars | Separate HF OAuth App, redirect to `api.humanbased.ai` | Separate HF OAuth App, redirect to staging API |

| Env var | Production (Cloud Run) | Staging (Cloud Run) |
|---------|----------------------|---------------------|
| `HF_CLIENT_ID` | Prod HF app client ID | Staging HF app client ID |
| `HF_CLIENT_SECRET` | Prod HF app secret | Staging HF app secret |
| `HF_REDIRECT_URI` | `https://api.humanbased.ai/v1/auth/huggingface/callback` | `https://humanbased-api-staging-294116912851.asia-northeast1.run.app/v1/auth/huggingface/callback` |
| `HF_OAUTH_STATE_SECRET` | Shared — same HMAC key | Shared — same HMAC key |
| GitHub credentials | Supabase Dashboard (shared) | Same |

### Why separate OAuth apps per environment

OAuth providers bind a **redirect URI** to each registered app. When HuggingFace returns the authorization code, it sends the user's browser to that exact URI — if it doesn't match, the flow fails. Since staging and production have different API domains, each needs its own registered app with the correct redirect URI.

Separating keys also provides:

- **Blast radius isolation** — a leaked or revoked staging key doesn't take down production sign-in
- **Independent rate limits** — load testing on staging won't exhaust production's OAuth quota
- **Audit trail** — provider dashboards show per-app usage, making it easy to distinguish staging traffic from real users
- **Safe rotation** — rotate staging keys freely without coordinating a production maintenance window

GitHub is the exception: Supabase handles the full OAuth flow (token exchange, session creation) within its own infrastructure, so both environments share one GitHub OAuth App through the shared Supabase project. If staging moves to a separate Supabase project in the future, a second GitHub OAuth App will also be needed.

---

## Internal Developer Notes

### Use `prd.md` as your source of truth

[`prd.md`](prd.md) is the authoritative product spec for this repo. Before starting any work:

- Check the **Build Queue** section for prioritized items
- Each entry has acceptance criteria, solution design, and test cases — read them before writing code
- After completing a feature, mark it `[x]` in prd.md with the commit hash
- If you discover a bug or want to add a feature not in prd.md, **add it to prd.md first** and get confirmation before building

When to use prd.md:
- **New feature request** → add to Build Queue, confirm with @beingzy, then build
- **Bug report** → add under `🐛 Bug Fixes` with root cause and fix design
- **Architecture decisions** → document in the relevant phase section so future context is preserved

### PR description requirements

Every PR should include:

```markdown
## Summary
- What changed and why (2–4 bullets, not a file list)

## Test plan
- [ ] Unit/integration tests pass
- [ ] Manual smoke test: describe what you actually clicked/curled
- [ ] No regressions in adjacent flows

🤖 Generated with Claude Code
```

Keep the title under 70 characters and in conventional commit format (`feat:`, `fix:`, `chore:`, `docs:`).

PRs that touch the API should note which endpoints changed and whether the response contract changed. PRs that touch the deploy workflow should describe *why* the change is safe — deploy failures block everyone.

### Coding conventions

- **API params:** MySQL queries use `%s` tuple params (`mysql_db.py`); never use f-strings for SQL values
- **Supply data:** query via `mysql_db.py` (AliCloud); `supply_db.py` (Supabase) is dormant until staging validates the migration
- **Frontend fetches:** use `apiFetch` from `src/lib/api.ts` — it handles auth headers automatically
- **Styling:** Tailwind utility classes + `THEME` constants from `src/lib/config.ts` — no inline hex values
- **No type shortcuts:** fix the actual type; never use `as any` or `@ts-ignore`
