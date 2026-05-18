# Deployment Runbook — V1 (temporary main→staging mode)

> **Scope.** Mechanics for deploying the contributor portal to staging. Under the V1 temporary treatment, every commit on `main` deploys to staging only; production targets are reserved but frozen. Exit trigger: `I4-1` ships.
>
> **Not yet covered here.** Broader infrastructure concerns (env resolution order, runtime-role creation, seed-script safety wrapper, promotion protocol) are tracked under `I0-3` in `prd.md` and will land in `docs/infrastructure.md` separately.

---

## Current state — 2026-04-17

| Component | Status |
|---|---|
| GCP service account + IAM roles | ✅ Done (executed via gcloud) |
| Workload Identity Federation (OIDC provider scoped to this repo) | ✅ Done |
| GitHub repo secrets for GCP (`GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`, `GCP_PROJECT_ID`) | ✅ Done |
| GitHub environments (`Staging`, `Production`) with Supabase keys | ✅ Done |
| Dockerfile + .dockerignore for API | ✅ In this PR |
| GH Action `deploy-staging-api.yml` | ✅ In this PR |
| First API deploy to Cloud Run staging | ⏳ Pending — triggers on first `main` push after this PR merges, or via `gh workflow run` |
| Cloud Run custom domain `staging.api.contributor.humanbased.ai` | ⏳ Pending (1 gcloud command after first deploy) |
| Vercel Production Branch flipped + Preview env vars + staging domain | ⏳ **Delegated** (see `docs/deployment-handoff.md`) |
| DNS CNAMEs | ⏳ **Delegated** (see `docs/deployment-handoff.md`) |
| Supabase migration applied to staging | ⏳ Pending (after API is healthy) |

---

## Target environments

| Service | URL | GCP/Vercel target |
|---|---|---|
| Frontend (prod, frozen) | `contributor.humanbased.ai` | Vercel project `contributor-portal`, Production (unused) |
| Frontend (staging) | `staging.contributor.humanbased.ai` | Vercel project `contributor-portal`, Preview alias |
| API (prod, frozen) | `api.contributor.humanbased.ai` | Cloud Run service (not provisioned) |
| API (staging) | `staging.api.contributor.humanbased.ai` | Cloud Run service `contributor-api-staging` in `asia-northeast1` |
| DB (staging) | Supabase project `jbugexmhyxggatppgfcv` | Shared with developer portal staging |
| DB (prod) | Supabase project `uxafdddzhgdhsabkwmgw` | Shared with developer portal production — **untouched during V1** |

---

## What's provisioned in GCP (project `humanbased-api`)

| Resource | Name | Purpose |
|---|---|---|
| Artifact Registry repo | `humanbased-api` (Docker, `asia-northeast1`) | Shared with developer portal; contributor images pushed under image name `contributor-api` |
| Workload Identity Pool | `github-pool` (existing, reused) | — |
| OIDC Provider | `github-contributor-provider` (attribute condition: `assertion.repository=='codatta/contributor-portal'`) | Only this repo's GH Actions can mint GCP tokens |
| Service Account | `github-contributor-deployer@humanbased-api.iam.gserviceaccount.com` | The SA GH Actions impersonates |
| IAM roles on SA | `roles/run.admin`, `roles/iam.serviceAccountUser`, `roles/artifactregistry.writer` | Minimum to build + push + deploy |

**Not used:** GCP Secret Manager. Supabase keys live in GitHub Environment secrets and are passed into Cloud Run via `--env-vars-file` at deploy time. Trade-off: keys are visible via `gcloud run services describe`; rotation requires redeploy.

---

## Secrets + variables — source of truth

### GitHub repo-level

Already set via `gh` CLI:

| Name | Type | Value |
|---|---|---|
| `GCP_PROJECT_ID` | Variable | `humanbased-api` |
| `GCP_WIF_PROVIDER` | Secret | `projects/294116912851/locations/global/workloadIdentityPools/github-pool/providers/github-contributor-provider` |
| `GCP_DEPLOY_SA` | Secret | `github-contributor-deployer@humanbased-api.iam.gserviceaccount.com` |

### GitHub Environments (same names in each, different values)

| Env | Secret | Source |
|---|---|---|
| `Staging` | `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY` | Staging Supabase project `jbugexmhyxggatppgfcv` |
| `Production` | `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY` | Production Supabase project `uxafdddzhgdhsabkwmgw` |

---

## Triggering the first API deploy

Once this PR merges, either push any change to `packages/api/**` or trigger manually:

```bash
gh workflow run deploy-staging-api.yml --ref main
gh run watch
```

On success, Cloud Run assigns a default URL like `https://contributor-api-staging-XXXX-an.a.run.app`. Verify:

```bash
URL=$(gcloud run services describe contributor-api-staging \
  --region asia-northeast1 --format 'value(status.url)')
curl "$URL/health/"
```

## After first deploy — custom domain

```bash
gcloud run domain-mappings create \
  --service contributor-api-staging \
  --domain staging.api.contributor.humanbased.ai \
  --region asia-northeast1
```

This prints the DNS records (typically a CNAME to `ghs.googlehosted.com`) that must be added at the DNS provider for `humanbased.ai`. See `docs/deployment-handoff.md`.

---

## Applying the Supabase migration to staging (last step)

Run only after the API is healthy and has read staging Supabase successfully:

```bash
# Option A: Supabase dashboard SQL editor
#   https://supabase.com/dashboard/project/jbugexmhyxggatppgfcv/sql/new
#   Paste sql-query/migrations/001_contribution_schema.sql, run

# Option B: CLI
cd sql-query
supabase link --project-ref jbugexmhyxggatppgfcv
supabase db push
```

Coordinate with the developer-portal team before applying — shared staging DB.

---

## Verification checklist

- [ ] `deploy-staging-api.yml` workflow green on last main commit
- [ ] `curl https://<cloud-run-default-url>/health/` returns 200
- [ ] Custom-domain CNAME resolves: `curl https://staging.api.contributor.humanbased.ai/health/`
- [ ] Vercel `staging.contributor.humanbased.ai` loads, hits staging Supabase + staging API
- [ ] Sign-up / sign-in works against staging Supabase
- [ ] Migration applied to staging Supabase; contributor tables visible in dashboard

## Rollback

```bash
# Cloud Run — roll back to previous revision
gcloud run services update-traffic contributor-api-staging \
  --region asia-northeast1 \
  --to-revisions <previous-revision-name>=100

# Vercel — redeploy a prior commit
vercel rollback <deployment-url>
```

## Exit the temporary mode (when I4-1 ships)

1. Create `release/production` branch from main
2. Push first commit → Vercel auto-deploys to Production → `contributor.humanbased.ai`
3. Provision Cloud Run `contributor-api` (prod service) with production Supabase secrets from `Production` GitHub environment
4. Add a `deploy-production-api.yml` workflow gated on `workflow_dispatch` or tag push, with `environment: Production`
5. Register production DNS CNAMEs
6. Remove this "Temporary treatment" section from the runbook

---

## Delegated setup

Vercel + DNS work is handed off — see `docs/deployment-handoff.md` for the step-by-step playbook intended for whoever owns those platforms.
