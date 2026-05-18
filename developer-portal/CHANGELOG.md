# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/). This project uses [Semantic Versioning](https://semver.org/).

---

## [0.2.0] — 2026-03-27

### Features
- Auth: sign up / sign in via Supabase Auth
- Onboarding: 3-step org setup (details, invite members, API key)
- Dashboard: overview with live data stream, waffle chart, adopt/dispute
- API key management: create, reveal, copy, revoke with expiration presets
- Members: invite by email with Resend, role management, remove
- Subscriptions: browse and subscribe to data verticals
- Billing: Stripe Checkout, balance cards (available/frozen/total/spent), transaction history
- Data charge lifecycle: freeze on receive, settle on adopt, refund on valid dispute
- Test/live mode separation for billing
- Account settings: name, email, backup email
- Organization settings: name, slug, domain allowlist, danger zone delete
- API key auth middleware for consumer data endpoints
- Consumer data API: verticals, pull, adopt, dispute, deliveries
- CLI tool: 11 commands for auth, data, billing, subscriptions
- MCP server for AI agent integration
- Documentation site at docs.humanbased.ai
- Simulator: writes to test DB for end-to-end data lifecycle testing
- CI/CD: GitHub Actions auto-deploy for webapp, API, and docs

### Fixes
- Stripe webhook signature validation — recreated endpoint with correct signing secret
- Navbar logo loading on Vercel — copy public assets to dist
- DataSourceModal cancel button during connecting phase
- Invite email sending in onboarding flow
- Production connection reliability (useRef for stable callbacks)
- Overview balance refresh after adopt/dispute

### Infrastructure
- Webapp deployed to Vercel (developer.humanbased.ai)
- API deployed to Google Cloud Run (api.humanbased.ai)
- Docs deployed to Vercel (docs.humanbased.ai)
- GCP Workload Identity Federation for keyless GitHub Actions auth
