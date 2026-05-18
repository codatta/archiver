# Deployment Guide

This document covers the full deployment setup for the Humanbased Developer Portal. Use it to replicate, debug, or scale the infrastructure.

---

## Architecture Overview

```
                                  ┌──────────────────┐
                                  │   Vercel          │
                                  │   developer.      │
                                  │   humanbased.ai   │
                                  │   (webapp)        │
                                  └────────┬─────────┘
                                           │ HTTPS
                                           ▼
┌──────────────┐   HTTPS    ┌──────────────────────────┐   TCP/3306    ┌──────────────┐
│  Browser /   │ ────────── │  Google Cloud Run         │ ───────────► │ DigitalOcean │
│  Frontend    │            │  asia-northeast1          │              │ VPS Proxy    │
└──────────────┘            │  humanbased-api           │              │ (socat)      │
                            └──────────────────────────┘              └──────┬───────┘
                                                                            │ TCP/3306
                                                                            ▼
                                                                   ┌──────────────────┐
                                                                   │ AliCloud PolarDB  │
                                                                   │ (MySQL)           │
                                                                   │ Singapore region  │
                                                                   └──────────────────┘
```

Cloud Run has dynamic IPs that can't be whitelisted in AliCloud PolarDB. The DigitalOcean VPS acts as a TCP proxy with a fixed IP that is whitelisted.

---

## 1. Services & Domains

### Production

| Service | Domain | Platform | Region |
|---------|--------|----------|--------|
| Frontend (webapp) | developer.humanbased.ai | Vercel | Auto |
| Backend (API) | api.humanbased.ai | Google Cloud Run | asia-northeast1 |
| Docs | docs.humanbased.ai | Vercel | Auto |
| DB Proxy (VPS) | 138.197.227.14 (reserved IP) | DigitalOcean | NYC1 |
| Primary DB | Supabase | Supabase Cloud | Tokyo |
| Supply-side DB | codatta-prod.rwlb.singapore.rds.aliyuncs.com | AliCloud PolarDB | Singapore |

### Staging

| Service | Domain | Platform | Region |
|---------|--------|----------|--------|
| Frontend (webapp) | staging.developer.humanbased.ai | Vercel (alias) | Auto |
| Backend (API) | staging.api.humanbased.ai | Cloud Run (`humanbased-api-staging`) | asia-northeast1 |
| Docs | staging.docs.humanbased.ai | Vercel (alias) | Auto |
| Primary DB | Supabase (separate staging project) | Supabase Cloud | Tokyo |
| Supply-side DB | (shared with prod — read-only) | AliCloud PolarDB | Singapore |

---

## 2. DigitalOcean VPS Proxy

### Purpose

Routes MySQL traffic from Cloud Run (dynamic IPs) through a fixed IP that AliCloud PolarDB can whitelist.

### Current Setup

| Field | Value |
|-------|-------|
| Droplet name | okx-proxy |
| OS | Ubuntu 24.04 LTS x64 |
| Size | 512 MB / 10 GB / NYC1 |
| Public IPv4 | 137.184.23.169 |
| Reserved IP | 138.197.227.14 |
| Private IP (VPC) | 10.116.0.7 |

### SSH Access

```bash
ssh -i ~/.ssh/do_proxy root@137.184.23.169
```

The SSH key pair is at `~/.ssh/do_proxy` (ed25519). The public key is authorized on the VPS.

### socat TCP Proxy Service

The VPS runs `socat` as a systemd service to forward MySQL connections:

```
Port 3306 on VPS  →  codatta-prod.rwlb.singapore.rds.aliyuncs.com:3306
```

**Service file:** `/etc/systemd/system/db-proxy.service`

```ini
[Unit]
Description=AliCloud PolarDB MySQL Proxy
After=network.target

[Service]
ExecStart=/usr/bin/socat TCP-LISTEN:3306,fork,reuseaddr TCP:codatta-prod.rwlb.singapore.rds.aliyuncs.com:3306
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Common commands:**

```bash
# Check status
systemctl status db-proxy

# Restart
systemctl restart db-proxy

# View logs
journalctl -u db-proxy -f

# Test connection from VPS
mysql -h 127.0.0.1 -P 3306 -u yizhang4prod -p cfp_metacore -e "SELECT 1"
```

### Firewall (ufw)

```
22/tcp    — SSH
3128/tcp  — Squid proxy (legacy, can be removed)
3306/tcp  — MySQL proxy
```

### Replicating the VPS Setup

To set up a new proxy (e.g., for a different region or scaling):

```bash
# 1. Create a DigitalOcean droplet (Ubuntu 24.04, any size)
# 2. Assign a Reserved IP in the DO console
# 3. SSH in and run:

apt update && apt install socat ufw mysql-client -y

cat > /etc/systemd/system/db-proxy.service << 'EOF'
[Unit]
Description=AliCloud PolarDB MySQL Proxy
After=network.target

[Service]
ExecStart=/usr/bin/socat TCP-LISTEN:3306,fork,reuseaddr TCP:codatta-prod.rwlb.singapore.rds.aliyuncs.com:3306
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now db-proxy

ufw allow 22/tcp
ufw allow 3306/tcp
ufw --force enable

# 4. Whitelist the droplet's PUBLIC IPv4 in AliCloud PolarDB
#    (AliCloud Console → PolarDB → IP Whitelist Templates → developer_portal)
# 5. Test: mysql -h 127.0.0.1 -P 3306 -u yizhang4prod -p cfp_metacore -e "SELECT 1"
```

---

## 3. AliCloud PolarDB (Supply-side MySQL)

### Connection Details

| Field | Value |
|-------|-------|
| Host | codatta-prod.rwlb.singapore.rds.aliyuncs.com |
| Port | 3306 |
| Database | cfp_metacore |
| User | yizhang4prod |
| Access | Read-only (supply-side annotation data) |

### IP Whitelist

Managed in AliCloud Console → PolarDB → IP Whitelist Templates.

| Template | IPs | Purpose |
|----------|-----|---------|
| developer_portal | 137.184.23.169 | DigitalOcean VPS proxy |

When adding a new proxy or service, add its public IP to this template.

### Key Tables

- `cfp_frontier` — Data frontiers (categories of annotation work)
- `cfp_frontier_task` — Tasks within each frontier
- `cfp_task_submission` — Individual data submissions
- `cfp_task_audit_record` — Quality audit records

---

## 4. Google Cloud Run (API)

### Service Details

| Field | Value |
|-------|-------|
| Service name | humanbased-api |
| Region | asia-northeast1 |
| Project | humanbased-api |
| Artifact Registry | asia-northeast1-docker.pkg.dev/humanbased-api/humanbased-api/api |
| Port | 8000 |
| Direct URL | https://humanbased-api-ngqs62idwa-an.a.run.app |

### Environment Variables

Set directly on the Cloud Run service (not in the Docker image):

```
SUPABASE_URL=https://uxafdddzhgdhsabkwmgw.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_***
SUPABASE_SECRET_KEY=sb_secret_***
RESEND_API_KEY=re_***
STRIPE_SECRET_KEY=sk_test_***
STRIPE_PUBLISHABLE_KEY=pk_test_***
STRIPE_WEBHOOK_SECRET=whsec_***
API_URL=https://api.humanbased.ai
WEBAPP_URL=https://developer.humanbased.ai
VITE_API_URL=https://api.humanbased.ai
MYSQL_HOST=138.197.227.14          # VPS Reserved IP (not direct RDS host)
MYSQL_PORT=3306
MYSQL_USER=yizhang4prod
MYSQL_PASSWORD=***
MYSQL_DATABASE=cfp_metacore

# Social OAuth (HuggingFace — custom OIDC flow, server-side only)
HF_CLIENT_ID=hf_oauth_client_***
HF_CLIENT_SECRET=***
HF_REDIRECT_URI=https://api.humanbased.ai/v1/auth/huggingface/callback
HF_OAUTH_STATE_SECRET=***   # 32+ random bytes, HMAC-signs the state cookie
```

---

## Social Sign-In Setup (GitHub + HuggingFace)

The portal supports three sign-in methods: email + password, GitHub, and
HuggingFace. Each environment (staging, prod) needs its own OAuth app.

### GitHub OAuth (via Supabase native provider)

Create two GitHub OAuth Apps (one per environment):

1. GitHub → Settings → Developer settings → OAuth Apps → New OAuth App
2. Fields:
   - **Application name:** `Codatta Developer Portal (prod)` / `(staging)`
   - **Homepage URL:** `https://developer.humanbased.ai` (or staging URL)
   - **Authorization callback URL:**
     `https://uxafdddzhgdhsabkwmgw.supabase.co/auth/v1/callback`
3. Copy Client ID and generate a Client Secret
4. In Supabase dashboard → Authentication → Providers → GitHub:
   - Enable
   - Paste client_id + client_secret
   - Save

No API env vars required — Supabase handles the full flow. The frontend
calls `supabase.auth.signInWithOAuth({ provider: 'github' })` and Supabase
redirects through GitHub and back to `/auth/callback`.

**Also enable** Authentication → Settings → "Link accounts with same email"
so GitHub identities auto-link to existing password accounts.

### HuggingFace OAuth (custom backend flow)

HuggingFace is not a Supabase-native provider, so our FastAPI backend
brokers the flow and bridges to Supabase via a magiclink.

1. Register OAuth app at `https://huggingface.co/settings/connected-applications`
   → Create → OAuth App
2. Fields:
   - **App name:** `Codatta Developer Portal (prod)` / `(staging)`
   - **Scope:** `openid profile email`
   - **Redirect URI:** `https://api.humanbased.ai/v1/auth/huggingface/callback`
     (prod) or `https://staging-api.humanbased.ai/...` (staging)
3. Copy Client ID + Client Secret
4. Set env vars on the Cloud Run service:
   - `HF_CLIENT_ID` — from HF
   - `HF_CLIENT_SECRET` — from HF
   - `HF_REDIRECT_URI` — must match exactly what was registered
   - `HF_OAUTH_STATE_SECRET` — generate with `openssl rand -hex 32`

Flow:

```
webapp → GET {API}/v1/auth/huggingface/start
       ← 302 to huggingface.co/oauth/authorize (PKCE + signed state cookie)
HF    → GET {API}/v1/auth/huggingface/callback?code&state
       → POST huggingface.co/oauth/token (client_secret + PKCE verifier)
       → decode id_token, validate iss/aud/exp/email_verified
       → supabase.auth.admin list/create user + generate_link(magiclink)
       ← 302 to Supabase magiclink action_link
       ← Supabase verifies → 302 to webapp /auth/callback
webapp → sync-profile → dashboard or onboarding
```


### Manual Deploy

When CI fails or you need to deploy outside of the normal workflow:

```bash
# 1. Build the Docker image
cd packages/api
docker build -t humanbased-api:latest .

# 2. Tag and push to Artifact Registry
gcloud auth configure-docker asia-northeast1-docker.pkg.dev --quiet
docker tag humanbased-api:latest \
  asia-northeast1-docker.pkg.dev/humanbased-api/humanbased-api/api:<tag>
docker push \
  asia-northeast1-docker.pkg.dev/humanbased-api/humanbased-api/api:<tag>

# 3. Deploy to Cloud Run
gcloud run deploy humanbased-api \
  --image=asia-northeast1-docker.pkg.dev/humanbased-api/humanbased-api/api:<tag> \
  --region=asia-northeast1 \
  --platform=managed \
  --allow-unauthenticated \
  --quiet
```

### Updating Environment Variables

```bash
gcloud run services update humanbased-api \
  --region=asia-northeast1 \
  --update-env-vars="KEY1=value1,KEY2=value2" \
  --quiet
```

### CI/CD (GitHub Actions)

Workflow: `.github/workflows/deploy-api.yml`

- **Trigger:** Push to `main` or `release/**` that touches `packages/api/**`
- **Auth:** GCP Workload Identity Federation (secrets: `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_AR_REPO`)
- **Known issue:** Merge commits from PRs may fail Workload Identity attribute conditions. If CI deploy fails with "credential rejected by attribute condition", deploy manually using the steps above.

---

## 5. Vercel (Webapp & Docs)

### Webapp

- **Project:** deployed at developer.humanbased.ai
- **Framework:** Bun HTML imports (React + Tailwind)
- **Build:** `cd packages/webapp && bun run build`
- **Trigger:** Push to `main` touching `packages/webapp/**`

### Docs

- **Project:** deployed at docs.humanbased.ai
- **Trigger:** Push to `main` touching `packages/docs/**`

---

## 6. Troubleshooting

### API returns 404 for all routes

The deployed Docker image may be stale. Check which image is running:

```bash
gcloud run services describe humanbased-api \
  --region=asia-northeast1 \
  --format="value(spec.template.spec.containers[0].image)"
```

If the image tag doesn't match the latest `main` commit, redeploy manually.

### MySQL connection timeout from Cloud Run

1. Check VPS proxy is running: `ssh -i ~/.ssh/do_proxy root@137.184.23.169 systemctl status db-proxy`
2. Check VPS firewall allows 3306: `ssh -i ~/.ssh/do_proxy root@137.184.23.169 ufw status`
3. Check AliCloud whitelist includes the VPS public IP (137.184.23.169)
4. Test from VPS: `mysql -h 127.0.0.1 -P 3306 -u yizhang4prod -p cfp_metacore -e "SELECT 1"`

### VPS proxy stops working after reboot

The systemd service should auto-start. If not:

```bash
ssh -i ~/.ssh/do_proxy root@137.184.23.169
systemctl enable --now db-proxy
```

### Cloud Run logs

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="humanbased-api"' \
  --limit=30 \
  --format="table(timestamp, textPayload)"
```

---

## 7. Scaling Considerations

### Adding a second proxy region

To reduce latency (e.g., proxy in Singapore closer to AliCloud):

1. Create a new DigitalOcean droplet in SGP1
2. Assign a Reserved IP
3. Replicate the socat setup (see Section 2)
4. Whitelist the new IP in AliCloud PolarDB
5. Update Cloud Run `MYSQL_HOST` to the new proxy IP

### Multiple Cloud Run regions

If you deploy the API to additional regions, each will need a proxy VPS with a whitelisted IP, or use a single proxy and accept the latency.

### Connection pooling

The current `aiomysql` pool config (`minsize=0, maxsize=10, pool_recycle=300`) works for moderate traffic. For higher load:

- Increase `maxsize` on the Cloud Run side
- Consider running PgBouncer or ProxySQL on the VPS for connection multiplexing
- Monitor with `SHOW PROCESSLIST` on the VPS

---

## 8. Staging Environment

### Branch Model

```
feat/* ──► PR to staging ──► staging (auto-deploy)
                                ↓
                         manual QA / sign-off
                                ↓
              PR: staging → main ──► production (auto-deploy)
```

- **`staging`** — integration branch, deploys to staging on every push
- **`main`** — stable production branch, deploys to prod on every push
- **`feat/*`, `fix/*`** — feature branches, target `staging` via PR
- **`release/**`** — hotfix release branches, deploy to prod

`staging` does not require passing CI to merge — it is permissive for active development. `main` retains its full quality gate.

### Setting Up Staging Infrastructure

Before `staging` can deploy, create these resources:

#### Cloud Run Staging Service

```bash
# Create the staging service (first deploy creates it, or manually):
gcloud run deploy humanbased-api-staging \
  --image=asia-northeast1-docker.pkg.dev/humanbased-api/humanbased-api/api:latest \
  --region=asia-northeast1 \
  --platform=managed \
  --allow-unauthenticated \
  --quiet

# Set non-Supabase staging env vars (one-time, or when values change):
gcloud run services update humanbased-api-staging \
  --region=asia-northeast1 \
  --update-env-vars="\
RESEND_API_KEY=<same-or-test-key>,\
STRIPE_SECRET_KEY=<test-mode-key>,\
STRIPE_PUBLISHABLE_KEY=<test-mode-key>,\
STRIPE_WEBHOOK_SECRET=<staging-webhook-secret>,\
API_URL=https://staging.api.humanbased.ai,\
WEBAPP_URL=https://staging.developer.humanbased.ai,\
VITE_API_URL=https://staging.api.humanbased.ai,\
MYSQL_HOST=138.197.227.14,\
MYSQL_PORT=3306,\
MYSQL_USER=yizhang4prod,\
MYSQL_PASSWORD=***,\
MYSQL_DATABASE=cfp_metacore" \
  --quiet

# Supabase env vars are injected automatically by deploy-api.yml on every
# staging deploy, sourced from GitHub → Settings → Environments → staging:
#   SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_SECRET_KEY
```

Map the staging domain in Cloud Run:

```bash
gcloud run domain-mappings create \
  --service=humanbased-api-staging \
  --domain=staging.api.humanbased.ai \
  --region=asia-northeast1
```

#### Supabase Staging Project (separate from production)

Staging uses a **separate Supabase project** — not a branch of the prod project. This gives full isolation: staging signups, orgs, API keys, and billing data never touch production.

**One-time setup:**

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) → New project
   - Name: `humanbased-staging`
   - Region: Tokyo (ap-northeast-1)
   - Save the project password
2. Export the prod schema and apply it to staging:
   ```bash
   # From the repo root (requires supabase CLI: brew install supabase/tap/supabase)
   supabase db dump --db-url "postgres://postgres:<prod-password>@db.uxafdddzhgdhsabkwmgw.supabase.co:5432/postgres" \
     --schema public > /tmp/schema.sql
   # Apply to staging (replace <staging-ref> with the new project ref)
   psql "postgres://postgres:<staging-password>@db.<staging-ref>.supabase.co:5432/postgres" \
     < /tmp/schema.sql
   ```
3. In the staging Supabase dashboard → Project Settings → API, copy:
   - **Project URL** (`https://<staging-ref>.supabase.co`)
   - **Publishable key** (`sb_publishable_...`)
   - **Secret key** (`sb_secret_...`)
4. Add these to GitHub → repo Settings → Environments → **staging**:
   - `SUPABASE_URL`
   - `SUPABASE_PUBLISHABLE_KEY`
   - `SUPABASE_SECRET_KEY`

After this, every push to `staging` will automatically inject the correct Supabase credentials into `humanbased-api-staging` via `deploy-api.yml`.

**Schema sync:** When prod schema changes (migrations), re-run the dump/apply above, or apply the same migration SQL directly to the staging project.

#### Vercel Staging Domains

In the Vercel dashboard for each project, add the staging domains:

1. **Webapp project** → Settings → Domains → Add `staging.developer.humanbased.ai`
2. **Docs project** → Settings → Domains → Add `staging.docs.humanbased.ai`

The CI workflows alias `staging` branch deployments to these domains automatically.

#### DNS Records

Add CNAME records for the staging subdomains:

| Record | Type | Value |
|--------|------|-------|
| `staging.developer.humanbased.ai` | CNAME | `cname.vercel-dns.com` |
| `staging.docs.humanbased.ai` | CNAME | `cname.vercel-dns.com` |
| `staging.api.humanbased.ai` | CNAME | `humanbased-api-staging-ngqs62idwa-an.a.run.app` (update after first deploy) |

### Creating the `staging` Branch

After this PR is merged to `main`:

```bash
git checkout main && git pull
git checkout -b staging
git push -u origin staging
```

From this point on, feature branches target `staging` instead of `main`.
