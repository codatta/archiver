# Product Overview — Humanbased

> This document captures the business-level context and product vision.
> For detailed feature specs and build queue, see [prd.md](./prd.md).
> For the phased plan to add the demand-push campaign flow, see [campaign-launch-roadmap.md](./campaign-launch-roadmap.md).

---

## What is Humanbased?

Humanbased (prev. Codatta) is a **two-sided marketplace for human-executed tasks**.

**Demand side (Developers / Organizations):**
Organizations — from solo developers to enterprises — need human execution at scale: data sourcing, data labeling, surveys, offline errands, mystery shopping, field verification, and any task that requires a credentialed human on the ground.

**Supply side (Human Workers):**
A distributed workforce of credentialed individuals who complete tasks based on their skills, location, and credential-gating (e.g., licensed professionals, verified identities, geographic presence).

The platform matches demand to supply, handles quality assurance (multi-validator consensus), and manages the financial lifecycle from payment to settlement.

---

## The Developer Portal (this repo)

The **Developer Portal** (`developer.humanbased.ai`) is the demand-side interface. It is the primary tool for organizations that consume Humanbased execution. It does NOT serve the supply side (workers have a separate app/interface).

### Core Responsibilities

| Domain | What it does | Status |
|--------|-------------|--------|
| **Task Launching** | Subscribe to data verticals (annotation types), pull incoming results, review quality | V1 shipped (subscription + pull model) |
| **Data Asset & License Management** | Adopt or dispute incoming data items; future: list owned data assets for resale, manage licenses, revoke access on refund | V1 partial (adopt/dispute live; licensing planned) |
| **Data Access Management** | API keys, per-member permissions, domain-gated org membership, subscription-level access control | V1 shipped |
| **Balance Management** | Stripe-funded balance, freeze-on-receive, settle-on-adopt, refund-on-dispute; future: earnings from data resale | V1 shipped (payment); earnings planned |
| **Organization Management** | Onboarding, member invites, role-based access, configurable settings with approval flow | V1 shipped; approval flow planned |
| **Programmatic Access** | REST API + CLI + MCP server for automation and CI/CD integration | V1 shipped |

### What it is NOT

- **Not a worker portal** — workers have their own app for task discovery, completion, and payouts
- **Not an admin panel** — internal Humanbased staff use separate admin endpoints (superadmin-gated)
- **Not a data marketplace (yet)** — V1 is a subscription/pull model; marketplace features (listing data for sale, pricing, discovery) are future scope

---

## Business Model

```
Developer (org)                     Humanbased                      Human Worker
     |                                  |                                |
     |-- subscribes to vertical ------->|                                |
     |-- funds balance (Stripe) ------->|                                |
     |                                  |-- distributes tasks ---------->|
     |                                  |<-- completed work -------------|
     |<-- data delivered (freeze $) ----|                                |
     |-- adopt (settle $) / dispute --->|                                |
     |                                  |-- pays worker (from settle) -->|
```

**Revenue flow:**
1. Developer funds balance via Stripe
2. Data arrives → balance frozen at `unit_price_usd`
3. Developer adopts → frozen funds settle (Humanbased earns margin, pays worker)
4. Developer disputes → if valid, frozen funds refund to developer; if rejected, treated as adopted

**Key financial states:** Available → Frozen → Settled (spent) or Refunded (back to available)

---

## Data Verticals (Annotation Types)

Verticals are the unit of supply organization. Each vertical represents a category of human-executed work:

| Vertical | Example payload |
|----------|----------------|
| Crypto Account Annotation | Wallet address + chain + category (exchange, DeFi, mixer) |
| Fashion Item Annotation | Brand + product name + category + attributes |
| Food Product Intelligence | Brand + category + nutriscore + ingredients |
| *(extensible)* | Any structured annotation schema |

Developers subscribe to verticals and receive a stream of validated data items. Each item carries:
- `payload` — the structured annotation result
- `quality_score` — multi-validator consensus score
- `consensus_ratio` — agreement ratio among validators
- `unit_price_usd` — per-item cost
- `validator_count` — number of independent validators

---

## Platform Architecture (Demand Side)

```
developer.humanbased.ai          api.humanbased.ai              Supabase
  (React + Tailwind)              (FastAPI on Cloud Run)       (Postgres + Auth + Realtime)
        |                               |                            |
        |-- REST API calls ------------>|-- reads/writes ----------->|
        |-- Supabase Realtime ---------------------------------------->| (direct subscription)
        |                               |-- Stripe API ------------> Stripe
        |                               |-- Resend API ------------> Email
```

**Packages:**
- `packages/webapp/` — Frontend SPA (Bun + React + Tailwind)
- `packages/api/` — Backend API (Python FastAPI, deployed to Cloud Run)
- `packages/cli/` — CLI tool for programmatic access
- `packages/mcp/` — MCP server for AI agent integration
- `packages/docs/` — Documentation site (docs.humanbased.ai)
- `shared/` — Shared TypeScript types

---

## Product Roadmap (High Level)

### Shipped (V1)
- Auth, onboarding, org management
- Dashboard with live data stream, waffle chart, adopt/dispute
- API key management, member management
- Subscription management (hardcoded verticals)
- Billing with Stripe, freeze/settle/refund lifecycle
- CLI, API docs, MCP server
- Test/live mode separation
- CI/CD auto-deploy (GitHub Actions)

### In Progress
- Org configurable settings with approval flow (auto-adopt period, per-vertical overrides)
- Production data source connection reliability
- Invitation email delivery improvements

### Planned (V2+)
- **Data Asset Marketplace** — orgs can list adopted data assets for resale; pricing, discovery, licensing
- **License Management** — per-item or per-batch licenses with revocation, expiry, downstream usage tracking
- **Earnings & Payouts** — orgs earn from data resale; withdrawal to bank/crypto
- **Live Vertical Catalog** — dynamic vertical discovery from API (replace hardcoded cards)
- **Audit & Reporting** — itemized billing statements, CSV/PDF export, reconciliation
- **Usage Analytics** — API call tracking, data consumption dashboards, cost forecasting
- **Domain Allowlist API** — backend-enforced auto-join on signup
- **Granular Permissions** — per-endpoint permission checks, not just role-based
- **Webhook Notifications** — push events to developer's systems (new data, dispute resolved, balance low)
- **SDKs** — Python and TypeScript client libraries wrapping the REST API
