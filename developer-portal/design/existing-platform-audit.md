# Existing Platform Audit — Gap Analysis for Task Launching

> Purpose: Map what already exists across Codatta org repos, identify what the Developer Portal can reuse, and define what's missing.
> Date: 2026-03-27

---

## Existing System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│  CURRENT CODATTA PLATFORM                                               │
│                                                                          │
│  cfp-gateway (Python/Flask)        ← API gateway, ACL, rate limiting    │
│       │                                                                  │
│       ├──► cfp-metacore (Python/FastAPI)   ← Core domain: frontiers,    │
│       │        ├── Frontier CRUD              tasks, submissions,       │
│       │        ├── Task management             activities, audit        │
│       │        ├── Submission pipeline                                   │
│       │        ├── Activity/campaign system                              │
│       │        └── Qualification system                                  │
│       │                                                                  │
│       ├──► cfp-user (Python/FastAPI)       ← User service: auth, DID,  │
│       │        ├── User accounts              badges, qualifications,   │
│       │        ├── Qualification verification  rewards, staking,        │
│       │        ├── Badge/reputation system     social accounts          │
│       │        ├── Reward distribution                                   │
│       │        └── Staking                                               │
│       │                                                                  │
│       ├──► cfp-api (Python/FastAPI)        ← DATA CONSUMER API         │
│       │        ├── Frontier/task data fetch    (this is cfp's version   │
│       │        ├── API key auth (MD5 sig)       of what WE built in     │
│       │        ├── Per-record billing           data_consumer_api)      │
│       │        └── Badge rankings                                        │
│       │                                                                  │
│       ├──► cfp-audit (Python)              ← Audit/review service      │
│       │                                                                  │
│       └──► cfp-scheduler                   ← Task distribution (early)  │
│                                                                          │
│  task-audit (Python, standalone)   ← QA pipeline: Qwen Vision LLM +    │
│       ├── OTC audit                  blockchain verification for        │
│       ├── CEX hot wallet audit       automated quality scoring          │
│       └── Image dedup (Knob)                                            │
│                                                                          │
│  codattaAdminServer (Java/Spring Boot) ← Internal admin panel           │
│                                                                          │
│  WORKER SURFACES:                                                        │
│  codattaFrontierWebsite  ← Desktop web (React/Vite)                     │
│  codattaAppH5            ← Mobile web (H5)                              │
│  codatta-app-ios         ← iOS native app                               │
│  codatta-frontier-sdk    ← TypeScript SDK for building task templates    │
│  codatta-frontier-templates ← Reusable task UI templates                │
│                                                                          │
│  ON-CHAIN:                                                               │
│  codatta-onchain-protocol   ← Submission fingerprinting                 │
│  codatta-did / resolver     ← Decentralized identity                    │
│  gas-payment-*              ← Gasless ERC20 payments                    │
│  XNYToken / locked-staking  ← Token economics                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Key Existing Concepts (mapped to our task-launching design)

### Frontier = Our "Vertical" / "Task Category"

A **Frontier** in the existing platform is a business domain (crypto wallets, fashion, food, etc.). It contains multiple **Tasks**. This maps directly to our concept of data verticals / task templates.

**Existing Frontier entity includes:**
- `frontier_id`, name, description, logo, banner
- Media links (Twitter, Telegram, Discord, website, docs)
- Qualification requirements (reputation threshold)
- Reward configuration (reward type, value)
- Status: ONLINE / OFFLINE
- Dataset URL (for data access)

### Task = Our "Task Template" + "Task Instance" (combined)

The existing platform's **Task** is more tightly coupled than our design:

```
Existing:                          Our Design:
Task {                             TaskTemplate {
  task_id                            id
  frontier_id                        org_id (NEW — multi-tenant)
  name                               name
  task_type: submission|validation   type: collection|annotation|survey|errand
  template_id → UI template          output_schema (structured)
  data_display: {                    instruction_assets
    web_template_url                 surfaces
    app_template_url               }
    gif_resource
  }                                TaskCampaign {
  qualification                      template_id
  reward_info[]                      budget, pricing
  data_requirements                  worker_requirements
}                                    targeting, schedule
                                   }
```

**Key difference:** The existing system does NOT separate template from campaign. A "task" is both the definition and the running instance. Our design separates them so developers can reuse templates across campaigns.

### Submission = Our "Task Instance" (completed)

```
Existing SubmissionRecord:          Our TaskInstance:
  submission_id                       id
  task_name, frontier_name            campaign_id
  data_submission: { data, taskId }   output_data
  status: PENDING|ADOPT|REFUSED       status: available|claimed|...|adopted|disputed
  result: S|A|B|C|D (grade)          quality_score (numeric)
  rewards[]                           unit_price_usd
  submission_time                     submitted_at
```

### Frontier SDK = Worker-side task interaction

The `codatta-frontier-sdk` provides:
- `getTaskDetail(taskId)` — fetch task definition
- `submitTask(taskId, data)` — submit work
- `getTaskList(frontier_id, ...)` — browse available tasks
- `getSubmissionList(...)` — view submission history
- `getSubmissionDetail(submissionId)` — view single submission
- `uploadFile(file)` — file upload for task attachments
- `getSpecTaskInfo/submitSpecTask` — special task types
- `getVerificationCode/checkEmail` — qualification verification

**Auth:** Cookie-based (`auth` token), with channel detection (iOS app vs web).

### Activity = Our "Campaign" (partial)

The existing metacore has an **Activity** system:
- `POST /activity/create` — create activity
- `POST /activity/biz/list` — list activities
- `POST /activity/info` — get activity detail
- `POST /activity/status/stop` — stop activity
- `POST /activity/submission/list` — list activity submissions
- `POST /activity/submission/reward/distribution` — distribute rewards

This is close to our Campaign concept but appears to be admin-driven (internal), not developer-facing.

### Quality Assurance

**Existing pipeline (task-audit repo):**
1. **Qwen Vision LLM** — automated screenshot/image quality assessment
2. **Blockchain verification** — cross-check tx hashes against on-chain data
3. **Rating: 1-5 scale** (not S/A/B/C/D which is the final grade)
4. **No multi-validator consensus in the traditional sense** — uses LLM + blockchain ground truth as "validators"

**Existing grading (cfp-metacore/frontier SDK):**
- S > A > B > C > D letter grades
- `quality_score` is a numeric reputation-weighted score
- `chain_status`: 0 (not submitted) → 1 (pending) → 2 (processing) → 3 (confirmed) → 4 (failed)
- On-chain fingerprinting of submissions

---

## Gap Analysis

### What EXISTS and we can REUSE

| Component | Existing | Reuse Strategy |
|-----------|---------|----------------|
| **Frontier/Task model** | cfp-metacore | Call metacore API to create frontiers/tasks, OR read its DB |
| **Worker surfaces** | Web + H5 + iOS apps | Workers already have apps — new tasks show up automatically |
| **Frontier SDK** | codatta-frontier-sdk | Workers use existing SDK to discover and submit tasks |
| **Task templates (UI)** | codatta-frontier-templates | Reusable React components for task UIs |
| **File upload** | Frontier SDK `uploadFile()` | Workers can upload photos/files via existing infra |
| **Quality pipeline** | task-audit (Qwen + blockchain) | Extend for new task types |
| **User qualifications** | cfp-user qualification system | Credential gating already exists |
| **Reputation/badges** | cfp-user badge system | Worker reputation scoring exists |
| **On-chain fingerprinting** | codatta-onchain-protocol | Submission integrity verification exists |
| **Admin panel** | codattaAdminServer | Internal review/management exists |
| **API gateway** | cfp-gateway | Rate limiting, ACL, routing exists |

### What's MISSING (gaps to fill)

| Gap | Description | Severity | Owner |
|-----|-------------|----------|-------|
| **Developer → Metacore bridge** | Developer Portal has no API connection to cfp-metacore. We can't create frontiers/tasks from our portal. | **Critical** | Developer Portal + Platform team |
| **Multi-tenant task creation** | Existing tasks are created by Codatta admins only. No concept of "org X creates their own task type." | **Critical** | cfp-metacore needs org_id on frontiers/tasks |
| **Campaign/budget model** | Existing "Activity" is admin-only. No developer-facing campaign with budget caps, targeting, scheduling. | **Critical** | Developer Portal (new) |
| **Budget reservation billing** | Existing billing is per-record consumption. No upfront budget reservation for campaigns. | **High** | Developer Portal billing extension |
| **Schema builder** | Existing tasks have `data_requirements` but it's not a structured JSON Schema that developers define via UI. | **High** | Developer Portal frontend (new) |
| **Geo-fencing** | No location-based task targeting in existing system. | **Medium** | cfp-metacore + worker apps |
| **Distribution strategies** | No broadcast/sequential/round-robin controls. Tasks are available to all qualified workers. | **Medium** | cfp-scheduler (extend) |
| **Campaign monitoring dashboard** | No real-time progress tracking for a specific campaign. | **Medium** | Developer Portal frontend (new) |
| **Results export** | No CSV/JSON export of campaign results. | **Low** | Developer Portal API (new) |
| **Auth bridge** | Developer Portal uses Supabase Auth; cfp-* uses cookie-based auth with its own user table. Different auth systems. | **High** | Integration layer needed |
| **Price model (developer sets price)** | Existing pricing is set by Codatta. Developer-defined pricing per task is new. | **High** | cfp-metacore + cfp-api changes |
| **Task seeding (bulk input)** | No mechanism for developer to upload batch input data for workers. | **Medium** | New API endpoint |

### What CONFLICTS (design decisions needed)

| Conflict | Existing | Our Design | Resolution |
|----------|---------|------------|------------|
| **Task ↔ Template separation** | Combined | Separate (Template + Campaign) | Add `template_id` FK to existing task model, or manage templates in Developer Portal only |
| **Quality grading** | S/A/B/C/D letters | 0.0–1.0 numeric score | Map: S=0.95+, A=0.85+, B=0.70+, C=0.50+, D=<0.50 |
| **Payment flow** | Worker earns XNY tokens + points | Developer pays USD via Stripe | Need USD→XNY bridge, or dual payment: dev pays USD, worker gets XNY |
| **Status lifecycle** | PENDING→SUBMITTED→ADOPT/REFUSED | available→claimed→submitted→pending_review→adopted/disputed | Extend existing statuses, map between systems |
| **Auth identity** | cfp-user (cookie, DID) | Supabase Auth (JWT) | API bridge: Developer Portal JWT → service-to-service token for cfp-metacore calls |

---

## Recommended Integration Architecture

### Adapter pattern (swappable backend)

The current cfp-metacore system is temporary. All integration goes through a `TaskDistributionPort` interface with a `CfpAdapter` implementation. When the new system is ready, a `V2Adapter` replaces it — zero portal code changes.

```
Developer Portal                         Codatta Platform
(developer.humanbased.ai)               (existing — TEMPORARY)

┌───────────────────────┐
│ Developer Portal API  │
│ (packages/api/)       │
│                       │
│ Source of truth:      │
│  Templates (Supabase) │
│  Campaigns (Supabase) │
│  Billing   (Supabase) │
│                       │
│ ┌───────────────────┐ │
│ │TaskDistributionPort│ │  ← Abstract interface
│ │                   │ │
│ │ ┌───────────────┐ │ │     ┌──────────────────────┐
│ │ │ CfpAdapter    │─┼─┼────►│ cfp-metacore          │
│ │ │ (now)         │ │ │ s2s │  /frontier/create     │
│ │ └───────────────┘ │ │     │  /task/publish        │
│ │ ┌───────────────┐ │ │     │  /activity/create     │
│ │ │ V2Adapter     │ │ │     │  /submission/list     │
│ │ │ (future)      │ │ │     └──────────┬───────────┘
│ │ └───────────────┘ │ │               │
│ └───────────────────┘ │               ▼
│                       │     ┌──────────────────────┐
│ Identity:             │     │ Worker Surfaces       │
│  Human devs (Supabase)│     │  Human: Web+H5+iOS   │
│  AI agents (API keys) │     │  AI: API workers      │
│  actor_type on all    │     │  Uses Frontier SDK    │
│                       │     └──────────┬───────────┘
└───────────┬───────────┘               │
            │                           ▼
            │  polling          ┌──────────────────────┐
            │◄──────────────────│ task-audit            │
            │  (sync_results)   │  Qwen + blockchain    │
            │                   │  Quality scoring      │
            ▼                   └──────────────────────┘
┌───────────────────────┐
│ Supabase              │
│  task_templates       │
│  task_campaigns       │  ← has external_ref (opaque adapter state)
│  task_instances       │  ← has external_submission_id
│  accounts/transactions│
└───────────────────────┘
```

### Data flow

1. Developer creates template + campaign in Developer Portal → stored in Supabase
2. On launch: `CfpAdapter.launch_campaign()` → creates Frontier + Tasks + Activity in cfp-metacore → stores `external_ref` on campaign
3. Workers see tasks via existing Frontier SDK surfaces → no worker-side changes
4. Workers complete tasks → cfp-metacore stores submissions
5. Polling job: `CfpAdapter.sync_results()` → pulls new submissions → creates `task_instances` rows → triggers billing (freeze/settle)
6. Developer reviews results in portal → adopt/dispute → billing lifecycle
7. **When V2 is ready:** New campaigns use `V2Adapter`. Active cfp campaigns continue with `CfpAdapter` until completed. Coexistence, no migration.

### Identity model (independent, dual-actor)

```
DEMAND SIDE (this repo)                    SUPPLY SIDE (cfp-user, separate)
┌─────────────────────────────┐           ┌─────────────────────────────┐
│ Supabase Auth               │           │ cfp-user + DID              │
│                             │           │                             │
│ users (human developers)    │           │ users (human workers)       │
│ api_keys (AI agents)        │           │ api agents (AI workers)     │
│  └─ actor_type: human|agent │           │  └─ actor_type: human|agent │
│  └─ agent_name, metadata    │           │  └─ DID, reputation, creds  │
│                             │           │                             │
│ NO coupling to supply side  │           │ NO coupling to demand side  │
└─────────────────────────────┘           └─────────────────────────────┘
        │                                          │
        └──────────► Task Distribution ◄───────────┘
                     (adapter layer)
```

---

## Implementation Priority (revised)

### Phase T1 — Portal-only (no platform dependency)
- DB migrations: `task_templates`, `task_campaigns`, `task_instances`
- `TaskDistributionPort` interface + `MockAdapter` (returns simulated results)
- Template & campaign CRUD API + frontend (4-step wizard)
- Budget reservation billing logic
- `actor_type` on `api_keys` for agent identity
- Can start **immediately** — no coordination needed

### Phase T2 — CfpAdapter (requires 1 coordination point: s2s auth)
- `CfpAdapter` implementation talking to cfp-metacore
- Single coordination need: agree on s2s auth mechanism with platform team
- Multi-tenancy workaround: prefix frontier names with org slug (no metacore schema change)
- Results polling job (every 30s)
- Status + quality mapping (S/A/B/C/D → numeric)
- `external_ref` and `external_submission_id` tracking

### Phase T3 — V2 swap (when new system is ready)
- `V2Adapter` drop-in replacement
- Config flip: `TASK_DISTRIBUTION_ADAPTER=v2`
- Dual-adapter coexistence during transition
- Same test suite validates both adapters
