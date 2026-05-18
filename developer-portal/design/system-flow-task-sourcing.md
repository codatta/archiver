# System Flow: Creating a Task to Source Data

> Technical reference for how data-sourcing tasks move through the Codatta/Humanbased ecosystem — from developer intent to delivered data.

---

## 1. System Topology

```
DEMAND SIDE (this repo)                    SUPPLY SIDE (Codatta platform)
─────────────────────                      ──────────────────────────────

developer.humanbased.ai                    app.codatta.io (Frontier Website)
├── webapp (React+Tailwind)                ├── codattaFrontierWebsite (React/Vite)
├── api (FastAPI on Cloud Run)             ├── codatta-frontier-sdk (JS SDK)
├── cli (@humanbased/cli)                  └── codatta-frontier-templates (Web Components)
├── docs (Next.js+MDX)
└── Supabase (Auth, DB, Realtime)          Backend Microservices (Python/FastAPI, DDD)
                                           ├── cfp-gateway     — API routing / service mesh
                                           ├── cfp-metacore    — Task engine (Frontier/Task/Submission)
                                           ├── cfp-user        — Worker identity, qualifications, DID
                                           ├── cfp-audit       — Submission review & quality validation
                                           ├── cfp-promotion   — Rewards & incentives
                                           ├── cfp-asset       — Data asset lifecycle
                                           ├── cfp-scheduler   — Task distribution
                                           ├── task-audit      — Qwen Vision LLM + blockchain verify
                                           └── codattaAdminServer (Java/Spring Boot)

                                           On-Chain Layer
                                           ├── codatta-onchain-protocol (Solidity + Python)
                                           │   ├── FrontierRegistry.sol     — ownership + DID access
                                           │   ├── DatasetVersionRegistry   — dataset versioning
                                           │   ├── RoyaltyEngine.sol        — reward distribution
                                           │   └── ContributionFingerprintRegistry
                                           ├── gas-payment-bundler (Go, ERC-4337)
                                           ├── XNYToken (ERC20)
                                           └── codatta-did / codatta-erc8004

                                           Databases
                                           ├── MySQL on AliCloud RDS (Singapore)
                                           │   ├── cfp_user        — worker accounts
                                           │   └── cfp_metacore    — frontiers, tasks, submissions
                                           └── omnitagServer MySQL — legacy annotation store
```

---

## 2. Key Concept Mapping

| Developer Portal term | cfp-metacore term | Description |
|---|---|---|
| **Vertical** | **Frontier** | A business domain / data category (e.g., Crypto Wallets, Fashion) |
| **Subscription** | — | Developer subscribes to a vertical to receive data |
| **Task Template** (V2) | **Task** | Reusable definition: input/output schema, validation rules |
| **Task Campaign** (V2) | **Activity** | A funded instance: budget, schedule, worker targeting |
| **Task Instance** (V2) | **Submission** | One unit of work assigned to / completed by a worker |
| **Delivery Item** | **Submission (adopted)** | Validated data delivered to developer |

---

## 3. Current Flow (V1 — Passive Pull)

V1 is a **pull-only model**: developers subscribe to verticals and receive whatever the supply side produces. There is no developer-initiated task creation yet.

```
┌─ SUPPLY SIDE ──────────────────────────────────────────────────────────┐
│                                                                        │
│  1. Codatta admin creates Frontier + Tasks + Activity in cfp-metacore  │
│     (via codattaAdminServer — Java/Spring Boot)                        │
│                                                                        │
│  2. cfp-scheduler distributes tasks to eligible workers                │
│     (reputation gating, qualification matching)                        │
│                                                                        │
│  3. Worker opens codattaFrontierWebsite or mobile app                  │
│     → loads task template (Web Component from CDN)                     │
│     → completes work via codatta-frontier-sdk                          │
│     → submits result                                                   │
│                                                                        │
│  4. cfp-metacore stores submission (status: PENDING)                   │
│     → cfp-audit runs auto-review                                       │
│     → task-audit (Qwen Vision LLM + blockchain verify) scores quality  │
│     → rating assigned: 1-5 numeric or S/A/B/C/D grade                 │
│     → on-chain fingerprint registered via ContributionFingerprintReg   │
│     → status moves to SUBMITTED → ADOPT (if auto-approved)            │
│                                                                        │
│  5. cfp-promotion distributes rewards to worker                        │
│     (REGULAR=fixed on submit, DYNAMIC=variable on adopt, AIRDROP)      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              │  ⚠️ GAP: No automated bridge service
                              │  (manual data entry or future polling job)
                              ▼
┌─ DEMAND SIDE (Developer Portal) ───────────────────────────────────────┐
│                                                                        │
│  6. Validated data lands in `delivery_items` table (Supabase)          │
│     Fields: vertical_id, payload, quality_score (0.0-1.0),            │
│     quality_method, validator_count, consensus_ratio, unit_price_usd   │
│                                                                        │
│  7. Developer receives data via:                                       │
│     a) Supabase Realtime subscription (live push to dashboard)         │
│     b) Pull API: GET /v1/data/pull?subscription_id=X&limit=50         │
│     c) CLI: hb data pull --subscription <id>                           │
│                                                                        │
│  8. On receive → balance freeze:                                       │
│     available_usd -= unit_price → frozen_usd += unit_price            │
│     Transaction type: "freeze"                                         │
│                                                                        │
│  9. Developer reviews item → adopts or disputes:                       │
│     ADOPT: frozen -= price → spent += price (type: "settle")           │
│     DISPUTE: stays frozen → admin reviews → refund or force-adopt      │
│                                                                        │
│  10. Auto-adopt: pg_cron job runs hourly, adopts items older than      │
│      org_settings.auto_adopt_hours (default 48h)                       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Current API Endpoints (V1 Data Flow)

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /v1/data/verticals` | Public | List available data verticals |
| `GET /v1/data/pull` | API Key | Pull pending delivery items |
| `POST /v1/data/items/{id}/adopt` | API Key | Adopt item, settle balance |
| `POST /v1/data/items/{id}/dispute` | API Key | Dispute item quality |
| `POST /v1/orgs/{id}/subscriptions` | JWT | Subscribe to a vertical |
| `GET /v1/orgs/{id}/billing/balance` | JWT | Check available/frozen/spent |

---

## 4. Planned Flow (V2 — Task Launching)

Developers will create tasks directly. The adapter pattern decouples the portal from the supply-side backend.

```
┌─ DEVELOPER PORTAL ─────────────────────────────────────────────────────┐
│                                                                        │
│  1. Developer creates Task Template (reusable spec)                    │
│     POST /v1/orgs/{org_id}/task-templates                              │
│     {                                                                  │
│       name, description,                                               │
│       type: "collection" | "annotation" | "survey" | "errand",         │
│       output_schema: { JSON Schema },                                  │
│       instruction_assets: [ urls ],                                    │
│       supported_surfaces: ["web", "mobile_app", "api"]                 │
│     }                                                                  │
│                                                                        │
│  2. Developer creates Task Campaign (funded instance)                  │
│     POST /v1/orgs/{org_id}/task-campaigns                              │
│     {                                                                  │
│       template_id,                                                     │
│       budget_usd, unit_price_usd,                                      │
│       worker_requirements: {                                           │
│         actor_types: ["human", "agent"],                               │
│         countries: ["US", "JP"],                                       │
│         languages: ["en"],                                             │
│         min_reputation: 0.6,                                           │
│         credentials: ["verified_education"],                           │
│         skills: ["data_labeling"]                                      │
│       },                                                               │
│       distribution: { strategy: "broadcast", max_per_worker: 10 },     │
│       schedule: { start_at, end_at, max_results: 1000 }               │
│     }                                                                  │
│                                                                        │
│  3. Portal reserves budget:                                            │
│     available_usd -= budget_usd → reserved_usd += budget_usd          │
│                                                                        │
└────────────┬───────────────────────────────────────────────────────────┘
             │
             ▼
┌─ ADAPTER LAYER ────────────────────────────────────────────────────────┐
│                                                                        │
│  TaskDistributionPort (abstract interface)                             │
│  ├── launch_campaign(campaign) → external_ref                          │
│  ├── pause_campaign(external_ref)                                      │
│  ├── resume_campaign(external_ref)                                     │
│  ├── cancel_campaign(external_ref)                                     │
│  └── poll_results(external_ref) → [TaskInstance]                       │
│                                                                        │
│  Implementations:                                                      │
│  ├── CfpAdapter (current) → calls cfp-metacore REST API               │
│  │   ├── POST /frontier/create  → creates Frontier in metacore         │
│  │   ├── POST /activity/create  → creates Activity (reward pool)       │
│  │   ├── GET  /submission/list  → polls completed submissions          │
│  │   └── Auth: s2s service token (TBD with platform team)              │
│  │                                                                     │
│  └── V2Adapter (future) → calls new system (TBD)                      │
│      └── Zero portal code changes when swapped                         │
│                                                                        │
└────────────┬───────────────────────────────────────────────────────────┘
             │
             ▼
┌─ SUPPLY SIDE (cfp-metacore) ───────────────────────────────────────────┐
│                                                                        │
│  4. cfp-metacore creates:                                              │
│     Frontier → maps from TaskTemplate                                  │
│     Task(s)  → submission type + validation type                       │
│     Activity → maps from TaskCampaign (budget, schedule)               │
│                                                                        │
│  5. cfp-scheduler distributes to eligible workers                      │
│     (filtered by qualifications, reputation, geo, language)            │
│                                                                        │
│  6. Workers complete tasks via Frontier Website / SDK / mobile         │
│     → submission stored in cfp-metacore (MySQL)                        │
│     → auto-audit pipeline runs (cfp-audit + task-audit)                │
│     → quality score assigned                                           │
│                                                                        │
└────────────┬───────────────────────────────────────────────────────────┘
             │
             │  Results flow back via:
             │  a) Webhook push (cfp-metacore → portal, HMAC-signed)
             │  b) Polling fallback (portal → cfp-metacore)
             ▼
┌─ DEVELOPER PORTAL (results) ──────────────────────────────────────────┐
│                                                                        │
│  7. Portal creates task_instances in Supabase                          │
│     Maps cfp status → portal status:                                   │
│       PENDING    → pending_review                                      │
│       SUBMITTED  → pending_review                                      │
│       ADOPT      → adopted                                             │
│       REFUSED    → disputed                                            │
│       REPORT_SPAM → disputed                                           │
│                                                                        │
│  8. Quality score normalization:                                       │
│     cfp grade  → portal score (0.0-1.0)                                │
│     S = 0.97, A = 0.85, B = 0.70, C = 0.50, D = 0.30                 │
│     Numeric 1-5 → divide by 5                                         │
│                                                                        │
│  9. Same billing lifecycle as V1:                                      │
│     receive → freeze → adopt (settle) or dispute (→ refund/force)      │
│                                                                        │
│  10. Monitoring dashboard shows:                                       │
│      progress (collected/target), quality histogram, cost vs budget,   │
│      submissions over time, worker geo spread, dispute rate            │
│                                                                        │
│  11. Results export: JSON or CSV (filtered by status/quality)          │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Database Schemas

### Demand Side — Supabase (Portal)

```sql
-- Current V1 tables
delivery_items (
  id uuid PK,
  vertical_id uuid FK,
  org_id uuid FK,
  environment text,        -- 'test' | 'live'
  payload jsonb,           -- the actual data
  quality_score float,     -- 0.0-1.0
  quality_method text,     -- 'lvm_+blockchain', 'multi_validator'
  validator_count int,
  consensus_ratio float,
  unit_price_usd decimal,
  status text,             -- 'pending' | 'adopted' | 'disputed' | 'refunded'
  underfunded boolean,
  created_at timestamptz
)

accounts (
  id uuid PK,
  org_id uuid FK,
  environment text,
  balance_available_usd decimal,
  balance_frozen_usd decimal,
  balance_spent_usd decimal
)

transactions (
  id uuid PK,
  account_id uuid FK,
  type text,               -- 'topup' | 'freeze' | 'settle' | 'refund'
  amount_usd decimal,
  balance_after_usd decimal,
  description text,
  environment text
)

subscriptions (
  id uuid PK,
  org_id uuid FK,
  vertical_id uuid FK,
  delivery_mode text,      -- 'pull' | 'push'
  filters jsonb,
  auto_accept boolean,
  status text
)

verticals (id, slug, name, description, base_price_usd)
topics (id, vertical_id, slug, name, description)
api_keys (id, org_id, name, hash, status, expires_at, last_used_at)
organizations (id, name, slug, org_email, logo_url, onboarding_completed)
users (id, auth_id, email, full_name, is_admin)
org_memberships (id, org_id, user_id, role)
org_settings (id, org_id, auto_adopt_hours)

-- Planned V2 tables
task_templates (
  id uuid PK,
  org_id uuid FK,
  name text,
  description text,
  type text,               -- 'collection' | 'annotation' | 'survey' | 'errand'
  output_schema jsonb,
  instruction_assets jsonb,
  supported_surfaces text[],
  created_by uuid FK,
  created_at timestamptz
)

task_campaigns (
  id uuid PK,
  template_id uuid FK,
  status text,             -- 'draft' | 'scheduled' | 'running' | 'paused' | 'completed'
  budget_usd decimal,
  unit_price_usd decimal,
  worker_requirements jsonb,
  targeting jsonb,
  distribution jsonb,
  schedule jsonb,
  external_ref jsonb,      -- opaque adapter state (e.g. cfp frontier_id)
  created_at timestamptz
)

task_instances (
  id uuid PK,
  campaign_id uuid FK,
  worker_id text,          -- opaque supply-side ID
  status text,             -- 'available' | 'claimed' | 'submitted' | 'pending_review' | 'adopted' | 'disputed'
  input_data jsonb,
  output_data jsonb,
  quality_score float,
  unit_price_usd decimal,
  submitted_at timestamptz,
  reviewed_at timestamptz
)
```

### Supply Side — MySQL on AliCloud RDS

```sql
-- cfp_user database
cfp_customer_user (
  id bigint PK,
  status int,              -- account status
  avatar varchar,
  did varchar,             -- decentralized identity
  referee_code varchar,    -- referral code
  signup_channel varchar,  -- 'referral-landing', 'organic', etc.
  signup_device varchar,   -- 'WEB', 'IOS', 'ANDROID'
  created_at datetime,
  last_login_at datetime
)

cfp_customer_user_account (
  id bigint PK,
  user_id bigint FK,
  account_type varchar,    -- 'block_chain' | 'email' | 'dynamic' | 'ton'
  chain varchar,           -- 'BSC', 'ETH', 'SOL', etc.
  address varchar,         -- wallet address or email
  connector varchar        -- 'wallet' | 'email' | 'dynamic'
)

cfp_user_qualification (
  id bigint PK,
  user_id bigint FK,
  type varchar,            -- qualification type
  data json,               -- {basic_info, language_skills, education, occupation}
  audit_status varchar     -- education verification status
)

cfp_login_log (user_id, login_at, device, ip)

-- cfp_metacore database (inferred from code + docs)
frontier (
  id bigint PK,
  name varchar,
  description text,
  status int,
  creator_id bigint,
  created_at datetime
)

task (
  id bigint PK,
  frontier_id bigint FK,
  type varchar,            -- 'submission' | 'validation'
  template_id varchar,     -- Web Component template reference
  config json,             -- input schema, instructions
  qualification_rules json
)

activity (
  id bigint PK,
  frontier_id bigint FK,
  reward_mode varchar,     -- 'REGULAR' | 'DYNAMIC' | 'AIRDROP'
  budget decimal,
  unit_reward decimal,
  start_at datetime,
  end_at datetime
)

submission (
  id bigint PK,
  task_id bigint FK,
  user_id bigint FK,
  status varchar,          -- 'PENDING' | 'SUBMITTED' | 'ADOPT' | 'REFUSED' | 'REPORT_SPAM'
  data json,               -- worker's output
  rating int,              -- 1-5 numeric
  grade varchar,           -- 'S' | 'A' | 'B' | 'C' | 'D'
  submitted_at datetime,
  reviewed_at datetime
)
```

---

## 6. Authentication Topology

Two **completely independent** identity systems. No shared auth.

```
DEMAND SIDE                              SUPPLY SIDE
───────────                              ───────────

Supabase Auth (JWT)                      cfp-user (cookie-based sessions)
├── Email/password signup                ├── Wallet connect (MetaMask, etc.)
├── JWT in Authorization header          ├── Email signup (rare — 1% of users)
├── org_memberships for RBAC             ├── DID registration (835 users)
└── API keys (hb_live_sk_*)              └── Qualifications + reputation score
    for programmatic access                  for task eligibility

Only touch point: TaskDistributionPort adapter
(s2s auth mechanism TBD with platform team)
```

---

## 7. Quality Assurance Pipeline

```
Worker submits data
       │
       ▼
cfp-metacore stores submission (PENDING)
       │
       ▼
cfp-audit: template-based auto-review
       │
       ▼
task-audit: Qwen Vision LLM assessment
       │  ├── Image/screenshot quality check
       │  └── Blockchain tx hash verification (for crypto data)
       │
       ▼
Rating assigned: 1-5 numeric or S/A/B/C/D grade
       │
       ▼
On-chain fingerprint via ContributionFingerprintRegistry
       │
       ▼
Status: PENDING → SUBMITTED → ADOPT (auto) or stays for manual review
       │
       ▼
Portal normalizes: grade → 0.0-1.0 score
  S=0.97  A=0.85  B=0.70  C=0.50  D=0.30
```

---

## 8. Billing Lifecycle

```
Developer tops up via Stripe checkout
       │
       ▼
  ┌─────────────────┐
  │    AVAILABLE     │ ← topup credited here
  └────────┬────────┘
           │ data received (pull or push)
           │ freeze: available -= price
           ▼
  ┌─────────────────┐
  │     FROZEN       │ ← held pending review
  └───┬─────────┬───┘
      │         │
   adopt     dispute
      │         │
      ▼         ▼
  ┌────────┐  ┌──────────────────┐
  │ SPENT  │  │ FROZEN (pending) │
  └────────┘  └───┬──────────┬───┘
                  │          │
             admin accept  admin reject
             (refund)      (force adopt)
                  │          │
                  ▼          ▼
             ┌────────┐  ┌────────┐
             │AVAILABLE│  │ SPENT  │
             └────────┘  └────────┘

Auto-adopt: pg_cron hourly job settles items > auto_adopt_hours (default 48h)
```

---

## 9. Infrastructure & Deployment

| Component | Platform | Region | Domain |
|---|---|---|---|
| Portal webapp | Vercel | Auto | developer.humanbased.ai |
| Portal API | Google Cloud Run | asia-northeast1 | api.humanbased.ai |
| Portal docs | Vercel | Auto | docs.humanbased.ai |
| Supabase | Supabase Cloud | Tokyo | project uxafdddzhg... |
| cfp-metacore + services | AliCloud | Singapore | Internal API |
| cfp-user + metacore DB | AliCloud RDS MySQL | Singapore | Internal |
| Frontier Website | Vercel/similar | — | app.codatta.io |
| Task templates | Aliyun OSS CDN | — | Versioned URLs |
| Smart contracts | Base / BNB Chain | — | On-chain |

---

## 10. Production Scale (as of 2026-03-27)

| Metric | Value | Notes |
|---|---|---|
| Registered users (supply) | 19.5M | 96% from single referral campaign |
| Active workers (90d) | ~400 | Real addressable workforce |
| Active workers (180d) | ~23K | Realistic campaign planning baseline |
| Total submissions | 4M | Across all frontiers |
| Unique submitters | 175K | 0.9% of user base |
| Adoption rate | 89.9% | High quality signal |
| Primary wallet chain | BNB Chain (84%) | Binance ecosystem |
| KYC / verified education | 0 | Zero adoption |
| Social bindings | 32.6K | X/Discord/Telegram |

**Implication**: Plan task campaigns for ~23K worker scale, not headline 19.5M.

---

## 11. Critical Gaps for V2

| Gap | Severity | Owner | Notes |
|---|---|---|---|
| Developer → cfp-metacore bridge | Critical | Portal + Platform | No way to create frontiers from portal |
| s2s auth mechanism | Critical | Platform team | CfpAdapter needs service token |
| Multi-tenant task creation | Critical | cfp-metacore | Currently admin-only |
| Campaign/budget model | Critical | Portal (new tables) | Budget reservation billing |
| Auth bridge Supabase ↔ cfp-user | High | Integration layer | Independent identity by design |
| Developer-set pricing | High | cfp-metacore + cfp-api | Currently platform sets prices |
| Schema builder UI | High | Portal frontend | Visual output_schema editor |
| Webhook from cfp-metacore | High | Platform team | Push results to portal |
| Geo-fencing | Medium | cfp-metacore + worker apps | Country/region filtering |
| Distribution strategies | Medium | cfp-scheduler | broadcast/sequential/round-robin |
| Campaign monitoring dashboard | Medium | Portal frontend | Progress, quality, cost charts |
| Results export (CSV/JSON) | Medium | Portal API + frontend | Batch download |
| AI agent identity (supply) | Low | cfp-user | Future: agent actor_type |
