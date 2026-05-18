# Deployment Handoff — Vercel + DNS

> **Audience.** Whoever owns Vercel dashboard access and DNS for `humanbased.ai`. Intended for **qinghua** or **lihao**.
>
> **Goal.** Wire the contributor portal frontend so every `main` push deploys to staging (not production), and route the staging URL + staging API URL to the right platforms. The GCP side and GitHub secrets are already done — this is the last piece before the first end-to-end demo.
>
> **Budget.** ~30–45 min if Vercel + DNS access is already in place.

---

## Context — why "main deploys to staging"

We're in a V1 temporary treatment. All feature branches target `main`, but `main` is wired to deploy to **staging** only, not production. Production is reserved/frozen until `I4-1` ships. After that, we flip to a release-branch model. Details in `prd.md` → Infrastructure Architecture → Service URLs.

## What's already done (no action needed)

| Component | Status |
|---|---|
| GCP service account + IAM roles + WIF provider scoped to this repo | ✅ |
| GitHub repo secrets (`GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`, `GCP_PROJECT_ID`) | ✅ |
| GitHub Environments `Staging` + `Production` with Supabase keys | ✅ |
| Dockerfile for API + GH Action deploying to Cloud Run `contributor-api-staging` on `main` push | ✅ (pending PR merge) |

## What this doc asks you to do

1. **Vercel** — freeze production deploys, point preview at staging Supabase, add the staging domain
2. **DNS** — two CNAME records for the two staging URLs
3. **Smoke test** — verify the staging URL loads

---

## Part 1 — Vercel (frontend)

**Vercel project:** `contributor-portal` under `inductive-network` org.

Dashboard root: https://vercel.com/inductive-network/contributor-portal

### Step 1.1 — Freeze production (change Production Branch)

Today, `main` is Vercel's Production Branch, so every merge auto-deploys to production. We change this so `main` pushes become **Preview** deployments instead.

1. Go to https://vercel.com/inductive-network/contributor-portal/settings/git
2. Under **Production Branch**, change the value from `main` to `release/production`
3. Save

The `release/production` branch doesn't exist and won't be pushed to. This freezes production deploys until we're ready for V1 exit. (When we're ready to exit, we create and push that branch.)

### Step 1.2 — Add Preview-scoped env vars (staging values)

1. Go to https://vercel.com/inductive-network/contributor-portal/settings/environment-variables
2. For each variable below, click **Add**, check only the **Preview** environment box:

| Name | Value |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://jbugexmhyxggatppgfcv.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | (staging publishable key — see note below) |
| `NEXT_PUBLIC_API_URL` | `https://staging.api.contributor.humanbased.ai` |

**Note on the staging publishable key.** Already stored as `SUPABASE_PUBLISHABLE_KEY` in the GitHub `Staging` environment — same value. Ask Yi for it, or grab it from the Supabase dashboard:
https://supabase.com/dashboard/project/jbugexmhyxggatppgfcv/settings/api-keys (publishable key, not service_role).

**Also populate Production scope** with the prod equivalents (they'll sit frozen but be ready when we flip):

| Name (Production scope) | Value |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://uxafdddzhgdhsabkwmgw.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | (prod publishable key) |
| `NEXT_PUBLIC_API_URL` | `https://api.contributor.humanbased.ai` |

### Step 1.3 — Add the staging domain

1. Go to https://vercel.com/inductive-network/contributor-portal/settings/domains
2. Click **Add** → enter `staging.contributor.humanbased.ai`
3. In the branch dropdown, select `main` (so the domain always tracks the latest main deploy)
4. Vercel shows the DNS record to create — copy it. Typically:
   ```
   Type:   CNAME
   Name:   staging.contributor
   Value:  cname.vercel-dns.com
   ```
5. Add this record at the DNS provider (see Part 2)

### Step 1.4 — Trigger a redeploy

After env vars are set, the previous deploy is stale. Force a rebuild:

```bash
# From the repo root
vercel --yes
```

Or just push a trivial commit to `main`.

---

## Part 2 — DNS

DNS provider for `humanbased.ai`: **TBD — confirm with Yi before starting.** Most likely Cloudflare or Route53.

Two CNAME records to add:

| Host / subdomain | Type | Value | Source |
|---|---|---|---|
| `staging.contributor` | CNAME | `cname.vercel-dns.com` (confirm in Vercel Step 1.3) | Vercel |
| `staging.api.contributor` | CNAME | (value printed by `gcloud run domain-mappings create` — ask Yi) | Cloud Run |

**The API domain record (`staging.api.contributor`) depends on a gcloud command Yi will run** after the first API deploy finishes. Coordinate timing — Yi adds the Cloud Run domain mapping, copies the CNAME value, pastes it here.

**Both records — TTL 300 (5 min) for easier iteration during V1.**

---

## Part 3 — Smoke test

After DNS propagates (usually 5–15 min):

```bash
# Frontend staging
curl -I https://staging.contributor.humanbased.ai
# Expect: 200 OK, served by Vercel

# API staging (after Yi confirms Cloud Run + domain mapping)
curl https://staging.api.contributor.humanbased.ai/health/
# Expect: {"status":"ok"} or similar
```

Open `https://staging.contributor.humanbased.ai` in a browser. Sign up with a test email. The auth flow should hit the staging Supabase project (verify in the Supabase dashboard → Auth → Users).

---

## Part 4 — Handback

When done, post in #infra or ping Yi with:

- [ ] Confirmation that Vercel Production Branch is `release/production`
- [ ] Confirmation that Preview + Production scopes both have the 3 env vars set
- [ ] Confirmation that `staging.contributor.humanbased.ai` resolves and serves the Next.js app
- [ ] (After Yi adds Cloud Run domain mapping) confirmation that `staging.api.contributor.humanbased.ai` resolves and `/health/` returns 200
- [ ] Any gotchas encountered so we can document them

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Suspended installation" on GitHub when connecting Vercel | Old Vercel GitHub App was suspended | Unsuspend at https://github.com/organizations/codatta/settings/installations → Vercel → Configure → Unsuspend |
| Main push deploys to Production anyway | Production Branch not changed | Re-check Step 1.1; branch value must be `release/production` |
| Staging env vars not applied | Variable scoped to Production only | Re-open env var, check **Preview** box |
| DNS doesn't resolve | Propagation lag or wrong CNAME | `dig staging.contributor.humanbased.ai` — check target matches Vercel's value |
| API CORS error from frontend | `WEBAPP_URL` on Cloud Run doesn't match staging frontend URL | Redeploy API after domain is wired; CORS set from env var |

## Reference

- [`docs/deployment.md`](./deployment.md) — the GCP/API side of the runbook
- [`prd.md`](../prd.md) → Infrastructure Architecture → Service URLs — the URL scheme rationale
- [`prd.md`](../prd.md) → Build Queue → `I0-3` — the broader shared-infra safety work this feeds into
