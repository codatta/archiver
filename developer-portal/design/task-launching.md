# Feature Design: Task Launching

> Status: **Design Draft**
> Author: Product + Engineering
> Dependencies: V1 billing lifecycle, subscription system, worker platform (separate repo)
> Portal scope: Developer Portal (`developer.humanbased.ai`) — demand side only
> Related: [prod_overview.md](../prod_overview.md), [prd.md](../prd.md)
> Platform audit: [existing-platform-audit.md](./existing-platform-audit.md) — what exists in codatta org, gaps, integration plan

---

## Problem

V1 is a **passive pull model** — developers subscribe to data verticals and receive whatever the supply side produces. Developers cannot:

- Define what data they need (schema, criteria, location, urgency)
- Control who works on it (credentials, skills, geography)
- Set quality thresholds before delivery
- Monitor progress toward a defined goal
- Launch one-off campaigns vs. ongoing streams

This limits Humanbased to pre-packaged data verticals. Task launching unlocks the full marketplace: developers define demand, workers fulfill it.

---

## Architecture Principles

### 1. Adapter Pattern — Swappable Task Distribution Backend

The current task-launching system (cfp-metacore) is **temporary and will be refactored**. The Developer Portal must:
- Integrate with the current system **now** for immediate value
- Swap to the new system **later** without rewriting portal code or API contracts

**Solution:** All communication with the task distribution backend goes through a **TaskDistributionPort** (interface). We ship two adapters:

```
Developer Portal API
        │
        ▼
┌─────────────────────────────┐
│  TaskDistributionPort       │  ← Interface (our contract)
│  (abstract)                 │
│                             │
│  launch_campaign()          │
│  pause_campaign()           │
│  cancel_campaign()          │
│  get_campaign_status()      │
│  sync_results()             │
│  map_status()               │
└──────┬──────────────┬───────┘
       │              │
       ▼              ▼
┌─────────────┐ ┌──────────────┐
│ CfpAdapter  │ │ V2Adapter    │
│ (current)   │ │ (future)     │
│             │ │              │
│ Calls       │ │ Calls new    │
│ cfp-metacore│ │ task system  │
│ /frontier/* │ │ TBD          │
│ /task/*     │ │              │
└─────────────┘ └──────────────┘
```

**Rules:**
- The Developer Portal owns the **source of truth** for templates, campaigns, and billing (Supabase)
- The adapter is a **one-way sync**: portal pushes to backend, backend pushes results back via webhook
- Swapping adapters = changing one config value + deploying the new adapter. Zero frontend changes, zero API contract changes, zero DB migration
- The adapter translates between our domain model and the backend's (e.g., `TaskCampaign` → cfp's `Frontier + Task + Activity`)

**Port interface (Python):**

```python
class TaskDistributionPort(ABC):
    """Abstract interface for task distribution backends.
    Swap implementations by changing TASK_DISTRIBUTION_ADAPTER in config."""

    @abstractmethod
    async def launch_campaign(self, campaign: TaskCampaign, template: TaskTemplate) -> ExternalRef:
        """Push campaign to worker platform. Returns external IDs for tracking."""

    @abstractmethod
    async def pause_campaign(self, ref: ExternalRef) -> bool:
        """Pause task distribution. Workers can't claim new tasks."""

    @abstractmethod
    async def resume_campaign(self, ref: ExternalRef) -> bool:
        """Resume paused campaign."""

    @abstractmethod
    async def cancel_campaign(self, ref: ExternalRef) -> bool:
        """Cancel campaign. Unclaimed tasks removed from worker surfaces."""

    @abstractmethod
    async def seed_tasks(self, ref: ExternalRef, items: list[dict]) -> int:
        """Push batch input data to create task instances on worker platform."""

    @abstractmethod
    async def sync_results(self, ref: ExternalRef, since: datetime) -> list[TaskResult]:
        """Pull completed/graded results since timestamp. Called by polling job."""

    @abstractmethod
    async def map_status(self, external_status: str) -> str:
        """Map backend-specific status to our canonical status enum."""


@dataclass
class ExternalRef:
    """Opaque reference to the campaign on the external platform."""
    adapter: str          # "cfp" | "v2"
    frontier_id: str      # cfp-specific
    task_ids: list[str]   # cfp-specific
    activity_id: str      # cfp-specific
    raw: dict             # any adapter-specific state
```

**CfpAdapter mapping:**

| Our concept | cfp-metacore concept | Adapter action |
|-------------|---------------------|----------------|
| TaskTemplate | Frontier + Task type definition | Create Frontier via `/frontier/create`, configure task type |
| TaskCampaign (launch) | Activity + Task instances | Create Activity via `/activity/create`, publish Tasks |
| Campaign pause | Activity stop | Call `/activity/status/stop` |
| Seed tasks | Task instances with input_data | Batch create via task API |
| Sync results | Submission list | Poll `/submission/list` + `/submission/detail` |
| Status mapping | PENDING→pending_review, ADOPT→adopted, REFUSED→disputed | `map_status()` |

### 2. Independent Identity — Demand & Supply, Human & AI

Both sides of the marketplace support **two actor types**: human users and AI agents. The identity systems are **independent** — the Developer Portal does NOT share auth with the worker platform.

```
                    DEMAND SIDE                         SUPPLY SIDE
                (Developer Portal)                  (Worker Platform)

        ┌─────────────────────────┐        ┌─────────────────────────┐
        │  Humanbased Identity    │        │  Codatta Identity       │
        │  (Supabase Auth)        │        │  (cfp-user + DID)       │
        │                         │        │                         │
        │  ┌───────┐ ┌─────────┐ │        │  ┌───────┐ ┌─────────┐ │
        │  │ Human │ │ AI Agent│ │        │  │ Human │ │ AI Agent│ │
        │  │ Dev   │ │ (MCP/   │ │        │  │ Worker│ │ (Auto-  │ │
        │  │       │ │  SDK)   │ │        │  │       │ │  labeler│ │
        │  └───────┘ └─────────┘ │        │  └───────┘ └─────────┘ │
        │                         │        │                         │
        │  actor_type: human|agent│        │  actor_type: human|agent│
        │  org_id: uuid           │        │  DID, reputation, creds │
        └────────────┬────────────┘        └────────────┬────────────┘
                     │                                  │
                     │    ┌──────────────────┐          │
                     └───►│ Task Distribution │◄─────────┘
                          │ (adapter layer)   │
                          └──────────────────┘
```

**Why independent:**
- Demand-side model (orgs, members, API keys, billing) has nothing in common with supply-side (individuals, DID, reputation, staking, credentials)
- Coupling them creates a fragile cross-team dependency on every auth change
- The only touchpoint is the task distribution adapter, which already abstracts the boundary
- Both sides evolve independently — we can add agent support without coordinating with cfp-user

**AI agent identity on demand side:**

| Aspect | Human Developer | AI Agent |
|--------|----------------|----------|
| Auth | Supabase email+password / SSO | API key (`hb_live_sk_*`) or service token |
| Identity | `users` table, `org_memberships` | `api_keys` table with `actor_type = 'agent'` |
| Permissions | Role-based (owner/admin/member) | Key-scoped (per-key permission set) |
| Actions | Full portal UI + API | API + MCP only (no UI session) |
| Audit trail | `user_id` on all actions | `api_key_id` on all actions |
| Rate limits | Standard | Configurable per key |

**AI agent identity on supply side (informational — not our repo):**

| Aspect | Human Worker | AI Agent Worker |
|--------|-------------|----------------|
| Auth | Cookie + DID | Service token + DID |
| Identity | cfp-user account | cfp-user account with `actor_type = 'agent'` |
| Capabilities | All surfaces (mobile/desktop) | API-only task completion |
| Quality | Multi-validator consensus | Same pipeline, flagged as machine-generated |
| Credentials | Human-verified (ID, certs) | Model capability attestation |
| Reputation | Badge system | Separate agent reputation track |

---

## Concept Model

```
┌─────────────────────────────────────────────────────────────┐
│  Developer Portal (this repo)                               │
│                                                             │
│  Task Template ──► Task Campaign ──► Monitoring & Results   │
│  (what to do)      (who, when,       (progress, quality,    │
│                     how much)         approve, export)       │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────┐
│  TaskDistributionPort        │  ← Adapter interface
│  ┌────────────────────────┐  │
│  │ CfpAdapter (now)       │  │  ← Talks to cfp-metacore
│  │ V2Adapter  (future)    │  │  ← Drop-in replacement
│  └────────────────────────┘  │
└────────────┬─────────────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
┌──────────┐   ┌──────────┐
│  Human   │   │  AI      │
│  Workers │   │  Agent   │
│  (mobile │   │  Workers │
│  +desktop)   │  (API)   │
└──────────┘   └──────────┘
```

---

## Core Entities

### Task Template

A reusable definition of **what needs to be done**. Think of it as a "job spec."

```
TaskTemplate {
  id: uuid
  org_id: uuid
  name: string                    // "Storefront Photo Collection — Tokyo"
  type: enum                      // collection | annotation | survey | errand
  description: string             // Instructions for workers (markdown)

  // Schema — what the worker submits
  input_schema: jsonb             // developer provides context per task instance
  output_schema: jsonb            // what the worker must return (JSON Schema)

  // Attachments & examples
  instruction_assets: Asset[]     // images, PDFs, videos showing how to do the task
  example_outputs: Asset[]        // gold-standard examples for quality reference

  // Quality
  validators_required: int        // min validators per item (default: 3)
  consensus_threshold: float      // min agreement ratio (default: 0.7)
  auto_approve_above: float       // auto-adopt if quality_score >= this (optional)
  auto_reject_below: float        // auto-dispute if quality_score < this (optional)

  // Surface
  surfaces: enum[]                // [mobile, desktop, api] — where workers see this

  // Metadata
  status: enum                    // draft | active | archived
  created_at: timestamptz
  updated_at: timestamptz
}
```

### Task Campaign

An **instance of running a template** with budget, targeting, and scheduling.

```
TaskCampaign {
  id: uuid
  org_id: uuid
  template_id: uuid FK
  name: string                    // "Q2 Tokyo Storefronts — Shibuya District"

  // Budget
  budget_usd: decimal             // total budget cap
  price_per_task_usd: decimal     // what the org pays per completed task
  price_model: enum               // fixed | bidding | dynamic

  // Volume
  target_count: int               // how many completions needed (null = unlimited)
  max_per_worker: int             // max tasks one worker can do (anti-gaming)

  // Targeting — who can work on this
  worker_requirements: {
    actor_types: string[]         // ["human"] | ["agent"] | ["human","agent"] (default: both)
    credentials: string[]         // human: ["verified_identity", "food_safety_cert"]
                                  // agent: ["vision_capable", "multilingual"]
    skills: string[]              // ["photography", "japanese_language"]
    min_reputation: float         // min worker reputation score
    geo_fence: GeoFence | null    // { center: {lat, lng}, radius_km: 50 } (human only)
    countries: string[]           // ["JP", "US"] — ISO country codes (human only)
    languages: string[]           // ["ja", "en"]
  }

  // Schedule
  start_at: timestamptz           // when tasks become available to workers
  end_at: timestamptz | null      // deadline (null = no deadline)
  timezone: string                // for display purposes

  // Distribution
  priority: enum                  // low | normal | high | urgent
  distribution_strategy: enum     // broadcast | sequential | round_robin

  // Lifecycle
  status: enum                    // draft | scheduled | active | paused | completed | cancelled
  created_at: timestamptz

  // Aggregates (computed)
  completed_count: int
  approved_count: int
  disputed_count: int
  spent_usd: decimal
}
```

### Task Instance

A **single unit of work** assigned to or claimed by a worker. Maps to `delivery_items` in V1.

```
TaskInstance {
  id: uuid
  campaign_id: uuid FK

  // Input — context the developer provides for this specific item
  input_data: jsonb               // e.g., { "address": "1-2-3 Shibuya", "photo_angle": "front" }

  // Output — what the worker submits
  output_data: jsonb | null       // filled by worker
  output_assets: Asset[]          // photos, recordings, files

  // Worker
  assigned_worker_id: uuid | null
  claimed_at: timestamptz | null
  submitted_at: timestamptz | null

  // Quality (filled by validation pipeline)
  quality_score: float | null
  consensus_ratio: float | null
  validator_count: int

  // Financial (same as V1 delivery_items)
  unit_price_usd: decimal
  status: enum                    // available | claimed | submitted | pending_review
                                  //   | adopted | disputed | refunded

  // Surface
  surface: enum                   // mobile | desktop | api (where it was completed)
  worker_location: point | null   // GPS at submission time (if mobile)

  created_at: timestamptz
}
```

---

## Task Types & Surface Routing

| Type | Description | Primary Surface | Example |
|------|-------------|----------------|---------|
| **Collection** | Gather real-world data requiring physical presence | Mobile | "Photo every ramen shop within 2km of Shibuya station" |
| **Annotation** | Label, categorize, or enrich existing data | Desktop | "Classify these 10K wallet addresses as exchange/DeFi/mixer" |
| **Survey** | Structured questionnaire answered by qualified respondents | Mobile + Desktop | "Rate this product's packaging on 5 criteria" |
| **Errand** | Physical-world action with verification | Mobile | "Visit this store and verify the posted price of item X" |

### Surface capabilities

| Capability | Mobile | Desktop |
|-----------|--------|---------|
| GPS / location proof | Yes | No |
| Camera / photo capture | Yes | Limited |
| Long-form data entry | Limited | Yes |
| Bulk annotation (100+ items) | No | Yes |
| Offline mode | Yes (queue + sync) | No |
| Real-time collaboration | No | Yes (future) |

---

## Developer Portal UX — Task Launcher

### New nav item: "Tasks"

Added to the dashboard nav between "Subscriptions" and "Members":

```
Overview | API Keys | Subscriptions | Tasks | Members | Billing | Docs ↗
```

### Tasks Landing Page

```
┌─────────────────────────────────────────────────────────────────┐
│ Tasks                                            [+ New Task]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─── Active Campaigns ───────────────────────────────────────┐ │
│  │ Campaign Name        Type        Progress   Budget   Status│ │
│  │ Tokyo Storefronts    collection  847/1000   $2,540   active│ │
│  │ Wallet Labels Q2     annotation  12.4K/50K  $620     active│ │
│  │ Product Survey #3    survey      302/500    $151     active│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─── Templates ──────────────────────────────────────────────┐ │
│  │ Template Name           Type         Campaigns   Last Used │ │
│  │ Storefront Photo        collection   3           2d ago    │ │
│  │ Crypto Wallet Classify  annotation   7           5h ago    │ │
│  │ Food Product Survey     survey       2           1w ago    │ │
│  │ Price Verification      errand       1           3d ago    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─── Draft ──────────────────────────────────────────────────┐ │
│  │ Untitled Task           annotation   —           draft     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Task Creation Flow (4 steps)

#### Step 1 — Type & Basics

```
┌─────────────────────────────────────────────────┐
│ New Task                              Step 1/4  │
├─────────────────────────────────────────────────┤
│                                                 │
│  Task Type                                      │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────┐ │
│  │ 📷       │ │ 🏷️       │ │ 📋     │ │ 🏃   │ │
│  │Collection│ │Annotation│ │ Survey │ │Errand│ │
│  └──────────┘ └──────────┘ └────────┘ └──────┘ │
│                                                 │
│  Template Name                                  │
│  [Storefront Photo Collection               ]   │
│                                                 │
│  Description (instructions for workers)         │
│  [Rich text editor with markdown support    ]   │
│  [                                          ]   │
│  [                                          ]   │
│                                                 │
│  Surfaces                                       │
│  [x] Mobile   [ ] Desktop   [ ] API            │
│                                                 │
│                          [Save Draft] [Next →]  │
└─────────────────────────────────────────────────┘
```

#### Step 2 — Schema & Examples

```
┌─────────────────────────────────────────────────┐
│ New Task                              Step 2/4  │
├─────────────────────────────────────────────────┤
│                                                 │
│  Input Schema (what you provide per task)        │
│  ┌─────────────────────────────────────────────┐│
│  │ + Add Field                                 ││
│  │ address      text      required             ││
│  │ photo_angle  select    [front/side/back]    ││
│  │ notes        text      optional             ││
│  └─────────────────────────────────────────────┘│
│                                                 │
│  Output Schema (what the worker submits)         │
│  ┌─────────────────────────────────────────────┐│
│  │ + Add Field                                 ││
│  │ photo        image     required             ││
│  │ store_name   text      required             ││
│  │ is_open      boolean   required             ││
│  │ menu_items   array     optional             ││
│  └─────────────────────────────────────────────┘│
│                                                 │
│  Example Outputs (helps workers understand)      │
│  [Upload examples]  3 uploaded                  │
│                                                 │
│  Instruction Assets (guides, reference photos)   │
│  [Upload assets]    1 uploaded                  │
│                                                 │
│                       [← Back] [Save] [Next →]  │
└─────────────────────────────────────────────────┘
```

#### Step 3 — Quality & Pricing

```
┌─────────────────────────────────────────────────┐
│ New Task                              Step 3/4  │
├─────────────────────────────────────────────────┤
│                                                 │
│  Quality Settings                               │
│  Validators per task    [ 3 ]                   │
│  Consensus threshold    [ 0.70 ]                │
│  Auto-approve above     [ 0.95 ] (optional)     │
│  Auto-reject below      [ 0.30 ] (optional)     │
│                                                 │
│  Pricing                                        │
│  Price model   (•) Fixed  ( ) Dynamic           │
│  Price per task  [$0.50              ]           │
│                                                 │
│  ℹ️ Platform fee: 20%. Worker receives $0.40.    │
│     With 3 validators, effective cost: $1.50/item│
│                                                 │
│                       [← Back] [Save] [Next →]  │
└─────────────────────────────────────────────────┘
```

#### Step 4 — Campaign (launch)

```
┌─────────────────────────────────────────────────┐
│ New Task                              Step 4/4  │
├─────────────────────────────────────────────────┤
│                                                 │
│  Campaign Name                                  │
│  [Q2 Tokyo Storefronts — Shibuya            ]   │
│                                                 │
│  Targeting                                      │
│  Credentials   [+ Add]  verified_identity       │
│  Skills        [+ Add]  photography             │
│  Countries     [+ Add]  🇯🇵 Japan               │
│  Geo-fence     [Set on map]  Shibuya, 5km       │
│  Min reputation  [ 4.0 ] / 5.0                  │
│                                                 │
│  Volume & Schedule                              │
│  Target count    [ 1000 ] completions           │
│  Max per worker  [ 20   ]                       │
│  Budget cap      [$1,500]                       │
│  Start           [2026-04-01  09:00 JST     ]   │
│  End             [2026-06-30  23:59 JST     ]   │
│  Priority        ( ) Low (•) Normal ( ) High    │
│                                                 │
│  Distribution                                   │
│  (•) Broadcast — all qualified workers see it   │
│  ( ) Sequential — one at a time, first-come     │
│  ( ) Round robin — evenly distributed           │
│                                                 │
│  ┌─ Summary ──────────────────────────────────┐ │
│  │ 1,000 tasks × $0.50 × 3 validators        │ │
│  │ = $1,500 max spend (capped at budget)      │ │
│  │ Current balance: $3,784.86                 │ │
│  │ ✓ Sufficient funds                         │ │
│  └────────────────────────────────────────────┘ │
│                                                 │
│              [← Back] [Save Draft] [🚀 Launch]  │
└─────────────────────────────────────────────────┘
```

### Campaign Detail / Monitoring

```
┌─────────────────────────────────────────────────────────────────┐
│ Tokyo Storefronts — Shibuya          ● Active    [Pause] [Stop]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ 847      │  │ 812      │  │ 35       │  │ $1,271.50    │   │
│  │ Completed│  │ Approved │  │ Disputed │  │ Spent        │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│                                                                 │
│  Progress ████████████████████████░░░░░░  847 / 1,000 (84.7%) │
│  Budget   ████████████████████░░░░░░░░░░  $1,271 / $1,500     │
│  Time     ██████████████░░░░░░░░░░░░░░░░  43 / 90 days left   │
│                                                                 │
│  ┌─ Quality Distribution ─────────────────────────────────────┐ │
│  │  ■■■■■■■■■■■■■■■■■■■ 0.9–1.0  (72%)                      │ │
│  │  ■■■■■■             0.7–0.9  (22%)                        │ │
│  │  ■■                 0.5–0.7  (4%)                          │ │
│  │  ■                  < 0.5    (2% — auto-rejected)          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─ Completion by Surface ────────────────────────────────────┐ │
│  │  Mobile: 831 (98%)    Desktop: 16 (2%)                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─ Recent Submissions ───────────────────────────────────────┐ │
│  │ (same LiveStream component from V1, filtered to campaign)  │ │
│  │ ID        Worker    Quality  Surface  Time    Actions      │ │
│  │ a3f8...   w-1042    0.97     📱       2m ago  Adopt Dispute│ │
│  │ b7e2...   w-0891    0.94     📱       5m ago  Adopt Dispute│ │
│  │ ...                                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─ Geo Heatmap (collection/errand only) ─────────────────────┐ │
│  │  [Map showing completion density by location]              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  [Export Results CSV]  [Export Results JSON]  [API Endpoint →] │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Design

### Templates

```
POST   /v1/orgs/{org_id}/tasks/templates              Create template
GET    /v1/orgs/{org_id}/tasks/templates              List templates
GET    /v1/orgs/{org_id}/tasks/templates/{id}         Get template
PATCH  /v1/orgs/{org_id}/tasks/templates/{id}         Update template
DELETE /v1/orgs/{org_id}/tasks/templates/{id}         Archive template
```

### Campaigns

```
POST   /v1/orgs/{org_id}/tasks/campaigns              Create campaign (draft)
GET    /v1/orgs/{org_id}/tasks/campaigns              List campaigns (?status=active)
GET    /v1/orgs/{org_id}/tasks/campaigns/{id}         Get campaign + stats
PATCH  /v1/orgs/{org_id}/tasks/campaigns/{id}         Update campaign
POST   /v1/orgs/{org_id}/tasks/campaigns/{id}/launch  Launch campaign
POST   /v1/orgs/{org_id}/tasks/campaigns/{id}/pause   Pause campaign
POST   /v1/orgs/{org_id}/tasks/campaigns/{id}/resume  Resume campaign
POST   /v1/orgs/{org_id}/tasks/campaigns/{id}/cancel  Cancel campaign (refund uncommitted)
```

### Task Instances (results)

```
GET    /v1/orgs/{org_id}/tasks/campaigns/{id}/items           List submissions
GET    /v1/orgs/{org_id}/tasks/campaigns/{id}/items/{item_id} Get single item
POST   /v1/orgs/{org_id}/tasks/campaigns/{id}/items/{item_id}/adopt    Adopt
POST   /v1/orgs/{org_id}/tasks/campaigns/{id}/items/{item_id}/dispute  Dispute
POST   /v1/orgs/{org_id}/tasks/campaigns/{id}/export          Export results (CSV/JSON)
```

### Bulk Input (seed tasks)

```
POST   /v1/orgs/{org_id}/tasks/campaigns/{id}/seed    Upload input_data for batch of task instances
                                                        Body: { items: [{input_data: {...}}, ...] }
                                                        For collection/errand: "go to these 1000 addresses"
                                                        For annotation: "label these 50K items"
```

---

## Financial Integration (extends V1 billing)

Task launching reuses the existing billing lifecycle with additions:

| Event | Available | Frozen | Spent | Transaction |
|-------|-----------|--------|-------|-------------|
| Campaign launched | −budget_cap | +budget_cap | — | `campaign_reserve` |
| Task completed & delivered | — | — | — | (already reserved) |
| Task adopted | — | −price | +price | `settle` |
| Task disputed (valid) | +price | −price | — | `refund` |
| Campaign completed/cancelled | +remaining | −remaining | — | `campaign_release` |

**New transaction types:** `campaign_reserve`, `campaign_release`

**Budget enforcement:** Campaign cannot launch if `available_balance < budget_cap`. Campaign auto-pauses if reserved funds are exhausted.

---

## Database (new tables)

```sql
-- Task templates
CREATE TABLE task_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations(id),
  name text NOT NULL,
  type text NOT NULL CHECK (type IN ('collection','annotation','survey','errand')),
  description text,
  input_schema jsonb DEFAULT '{}',
  output_schema jsonb DEFAULT '{}',
  instruction_assets jsonb DEFAULT '[]',
  example_outputs jsonb DEFAULT '[]',
  validators_required int NOT NULL DEFAULT 3,
  consensus_threshold numeric(3,2) NOT NULL DEFAULT 0.70,
  auto_approve_above numeric(3,2),
  auto_reject_below numeric(3,2),
  surfaces text[] NOT NULL DEFAULT '{mobile,desktop}',
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','active','archived')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Task campaigns
CREATE TABLE task_campaigns (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations(id),
  template_id uuid NOT NULL REFERENCES task_templates(id),
  name text NOT NULL,
  budget_usd numeric(12,4) NOT NULL,
  price_per_task_usd numeric(10,4) NOT NULL,
  price_model text NOT NULL DEFAULT 'fixed' CHECK (price_model IN ('fixed','dynamic')),
  target_count int,
  max_per_worker int DEFAULT 100,
  worker_requirements jsonb DEFAULT '{}',
  start_at timestamptz,
  end_at timestamptz,
  timezone text DEFAULT 'UTC',
  priority text NOT NULL DEFAULT 'normal' CHECK (priority IN ('low','normal','high','urgent')),
  distribution_strategy text NOT NULL DEFAULT 'broadcast'
    CHECK (distribution_strategy IN ('broadcast','sequential','round_robin')),
  status text NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft','scheduled','active','paused','completed','cancelled')),
  environment text NOT NULL DEFAULT 'test',
  created_at timestamptz NOT NULL DEFAULT now(),

  -- Adapter state — opaque reference to external platform
  external_ref jsonb,              -- stores ExternalRef (adapter, frontier_id, task_ids, etc.)
  adapter text,                    -- 'cfp' | 'v2' | null (draft, not yet launched)

  -- Aggregates (updated by triggers or periodic refresh)
  completed_count int NOT NULL DEFAULT 0,
  approved_count int NOT NULL DEFAULT 0,
  disputed_count int NOT NULL DEFAULT 0,
  spent_usd numeric(12,4) NOT NULL DEFAULT 0
);

-- Task instances (extends delivery_items concept)
CREATE TABLE task_instances (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id uuid NOT NULL REFERENCES task_campaigns(id),
  org_id uuid NOT NULL REFERENCES organizations(id),
  input_data jsonb DEFAULT '{}',
  output_data jsonb,
  output_assets jsonb DEFAULT '[]',
  assigned_worker_id uuid,
  worker_actor_type text DEFAULT 'human' CHECK (worker_actor_type IN ('human','agent')),
  claimed_at timestamptz,
  submitted_at timestamptz,
  quality_score numeric(4,2),
  consensus_ratio numeric(4,2),
  validator_count int NOT NULL DEFAULT 0,
  unit_price_usd numeric(10,4) NOT NULL,
  status text NOT NULL DEFAULT 'available' CHECK (status IN (
    'available','claimed','submitted','pending_review',
    'adopted','disputed','refunded'
  )),
  surface text CHECK (surface IN ('mobile','desktop','api')),
  worker_location point,
  environment text NOT NULL DEFAULT 'test',

  -- External mapping — links to the backend's submission ID
  external_submission_id text,     -- cfp submission_id or v2 equivalent
  external_status text,            -- raw status from backend before mapping

  created_at timestamptz NOT NULL DEFAULT now(),
  reviewed_at timestamptz
);

-- Indexes
CREATE INDEX idx_task_campaigns_org ON task_campaigns(org_id, status);
CREATE INDEX idx_task_campaigns_adapter ON task_campaigns(adapter) WHERE adapter IS NOT NULL;
CREATE INDEX idx_task_instances_campaign ON task_instances(campaign_id, status);
CREATE INDEX idx_task_instances_org ON task_instances(org_id, environment, status);
CREATE INDEX idx_task_instances_external ON task_instances(external_submission_id)
  WHERE external_submission_id IS NOT NULL;
```

### Identity tables (extend existing)

```sql
-- Extend existing api_keys table to support agent identity
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS
  actor_type text NOT NULL DEFAULT 'human' CHECK (actor_type IN ('human', 'agent'));
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS
  agent_name text;               -- e.g. "Claude MCP Agent", "CI/CD Pipeline"
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS
  agent_metadata jsonb;          -- model info, SDK version, capabilities

-- Audit: track who performed each action (human user or agent key)
-- Already exists: all API endpoints log user_id or api_key_id
-- No schema change needed — actor_type is derivable from the auth context
```

---

## CLI Extensions

```bash
# Templates
hb tasks templates list
hb tasks templates create --type collection --name "Storefront Photos"
hb tasks templates get <template-id>

# Campaigns
hb tasks campaigns list --status active
hb tasks campaigns create --template <id> --name "Q2 Shibuya" --budget 1500 --price 0.50
hb tasks campaigns launch <campaign-id>
hb tasks campaigns pause <campaign-id>
hb tasks campaigns cancel <campaign-id>

# Results
hb tasks results list <campaign-id> --status pending_review
hb tasks results adopt <campaign-id> <item-id>
hb tasks results dispute <campaign-id> <item-id>
hb tasks results export <campaign-id> --format csv --output results.csv

# Seed (bulk input)
hb tasks seed <campaign-id> --file addresses.json
```

---

## Implementation Phases

### Phase T1 — Templates, Campaign CRUD & Adapter Port

**Goal:** Developer can create templates, configure campaigns, save drafts. Adapter interface defined but not yet connected.

- DB migrations: `task_templates`, `task_campaigns`, `task_instances`
- `TaskDistributionPort` abstract class + `MockAdapter` for testing
- API: template CRUD, campaign CRUD (without launch)
- Frontend: Tasks nav item, landing page, 4-step creation flow
- Agent identity: `actor_type` column on `api_keys`
- Tests: unit + integration for all endpoints

### Phase T2 — CfpAdapter + Campaign Launch

**Goal:** Launching a campaign actually pushes to cfp-metacore via the CfpAdapter. Budget reservation. Simulated fallback for testing.

- `CfpAdapter` implementation:
  - Service-to-service auth with cfp-gateway (shared secret or internal token)
  - `launch_campaign()` → creates Frontier + publishes Tasks + creates Activity
  - `pause_campaign()` → calls `/activity/status/stop`
  - `cancel_campaign()` → stop activity + remove unclaimed tasks
  - `map_status()` → PENDING→pending_review, ADOPT→adopted, REFUSED→disputed
- Config: `TASK_DISTRIBUTION_ADAPTER=cfp` (or `mock` for test mode)
- Billing: `campaign_reserve` and `campaign_release` transactions
- `external_ref` stored on `task_campaigns` for tracking
- Frontend: campaign detail page with stats, progress bars
- Tests: budget reservation, adapter mock, campaign state machine

### Phase T3 — Results Sync & Monitoring

**Goal:** Poll cfp-metacore for completed submissions, map to our task_instances, update billing.

- `CfpAdapter.sync_results()` → polls `/submission/list`, maps to `TaskResult`
- Background job: runs every 30s, pulls new results per active campaign
- Result mapping: cfp `SubmissionRecord` → our `task_instances` row
  - `external_submission_id` links to cfp's `submission_id`
  - `quality_score` mapped from S/A/B/C/D grades (S=0.97, A=0.85, B=0.70, C=0.50, D=0.30)
  - `worker_actor_type` set based on cfp user metadata (if available)
- Auto-approve/reject based on template thresholds
- Frontend: campaign detail with LiveStream (reuse V1), quality distribution chart
- Export: CSV and JSON download
- Tests: sync flow, status mapping, auto-approve logic

### Phase T4 — Seed & Bulk Input

**Goal:** Developer can upload batch input data to populate task instances on the worker platform.

- `CfpAdapter.seed_tasks()` → batch creates task instances in cfp
- API: seed endpoint (accepts JSON array or CSV)
- Frontend: file upload in campaign detail, drag-and-drop
- Validation: input_data against template's input_schema
- Tests: bulk insert, schema validation, size limits

### Phase T5 — V2 Adapter (when new system is ready)

**Goal:** Drop-in replacement for CfpAdapter. Zero changes to portal code.

- `V2Adapter` implementation matching same `TaskDistributionPort` interface
- Config change: `TASK_DISTRIBUTION_ADAPTER=v2`
- Migration script: active campaigns with `adapter='cfp'` continue on cfp; new campaigns use v2
- Dual-adapter period: both adapters active, campaigns use whichever they launched with
- Tests: same test suite runs against both adapters (adapter-agnostic tests)

**Dual-adapter coexistence:**
```python
# Campaign keeps its adapter forever — no mid-flight switches
def get_adapter(campaign: TaskCampaign) -> TaskDistributionPort:
    if campaign.adapter == "cfp":
        return CfpAdapter()
    elif campaign.adapter == "v2":
        return V2Adapter()
    else:
        # New campaigns use the configured default
        return get_default_adapter()  # from config
```

### Phase T6 — Geo Features & Advanced Distribution

**Goal:** Map-based targeting, location proof, heatmap visualization, distribution strategies.

- Frontend: geo-fence picker (map component)
- API: geo-fence validation, location proof verification
- Frontend: completion heatmap on campaign detail
- Distribution strategies: broadcast/sequential/round_robin in adapter
- Worker platform coordination for geo-fencing (requires worker app changes)

---

## Open Questions

### Resolved

1. ~~**Worker platform integration**~~ → **Resolved:** cfp-metacore has full task CRUD + submission pipeline. We integrate via CfpAdapter. Frontier SDK on worker surfaces means tasks auto-appear.

2. ~~**Auth bridge**~~ → **Resolved:** Independent identity. Developer Portal uses Supabase Auth. Worker platform uses cfp-user + DID. No coupling. Adapter uses service-to-service auth (internal token) for cross-system calls.

### Open

3. **CfpAdapter s2s auth** — What auth mechanism does cfp-gateway accept for service-to-service calls? Options: (a) internal API key, (b) mTLS, (c) shared secret header. Need to coordinate with platform team.

4. **Validator pipeline integration** — The existing task-audit system (Qwen Vision + blockchain) handles specific task types (OTC, CEX). For developer-defined tasks with custom schemas, who validates? Options: (a) extend task-audit with generic validators, (b) developer defines validation rules in template, (c) community validators via the existing reputation system.

5. **Dynamic pricing** — For the `dynamic` price model, what algorithm determines price? Surge pricing based on demand/supply ratio? Developer sets a price range and the platform optimizes? Defer to V2.

6. **Input data ownership** — When a developer seeds input data (e.g., 50K wallet addresses to classify), is that data visible to workers? Privacy implications? Should input data be encrypted at rest with per-worker decryption?

7. **AI agent workers — quality parity** — Should AI-completed tasks go through the same multi-validator pipeline as human tasks? Or a separate automated QA track? If an AI agent completes 10K annotation tasks, the quality pipeline must handle the volume.

8. **AI agent workers — credential gating** — Human workers have verified_identity, food_safety_cert, etc. What credentials do AI agents present? Model capability attestation? Benchmark scores? Who issues AI agent credentials?

9. **Partial results & campaign continuation** — If a campaign is cancelled at 60%, developer has 600 adopted items. Support "continue campaign" with new budget for remaining 400?

10. **Template marketplace** — Should templates be shareable across organizations? Defer to V2+.

11. **cfp-metacore multi-tenancy** — Current system has no `org_id` on frontiers/tasks. For CfpAdapter, options: (a) prefix frontier names with org slug, (b) add org_id to metacore (requires their team), (c) use a dedicated "Humanbased Developer" frontier that multiplexes via task metadata.
