# Integration: API Surface

> API endpoints the contributor portal needs. Grouped by screen. All endpoints are relative to the platform API base URL.

---

## Authentication

| Endpoint | Method | Description |
|---|---|---|
| `POST /auth/login` | POST | Login (Google OAuth via NextAuth) |
| `GET /auth/me` | GET | Current user profile + role (contributor/developer) |
| `POST /auth/switch-role` | POST | Switch between contributor and developer role |

---

## Campaign Browse

| Endpoint | Method | Description |
|---|---|---|
| `GET /v1/campaigns` | GET | List active campaigns with filters |
| `GET /v1/campaigns?frontier=robotics&task_type=labeling&sort=highest_pay` | GET | Filtered listing |

**Response shape:**

```typescript
interface CampaignListResponse {
  campaigns: CampaignCard[];
  total: number;
  page: number;
  per_page: number;
}

interface CampaignCard {
  id: string;
  name: string;
  description: string;                  // May be AI-masked per privacy
  org: OrgSummary;                      // Privacy-adapted
  frontier: string;
  modality: string;
  tags: string[];
  tasks: TaskSummary[];                 // Per-task-type breakdown
  compensation: CompensationSummary;
  remaining_instances: number;
  estimated_time_left: string;
  qualification_status: QualificationStatus;
}
```

---

## Campaign Detail

| Endpoint | Method | Description |
|---|---|---|
| `GET /v1/campaigns/[id]` | GET | Full campaign detail |
| `GET /v1/campaigns/[id]/qualification` | GET | Per-task-type qualification check for current user |
| `POST /v1/campaigns/[id]/enroll` | POST | Accept/enroll in campaign |
| `DELETE /v1/campaigns/[id]/enroll` | DELETE | Unenroll from campaign |

**Qualification response:**

```typescript
interface QualificationResponse {
  tasks: {
    task_id: string;
    task_type: 'supply' | 'labeling' | 'validation';
    qualified: boolean;
    requirements: {
      name: string;
      met: boolean;
      current_value?: string;
      required_value: string;
      how_to_qualify_url?: string;
    }[];
  }[];
}
```

---

## Task Workspace

| Endpoint | Method | Description |
|---|---|---|
| `GET /v1/campaigns/[id]/tasks/[taskId]/next` | GET | Fetch next available instance for this task |
| `GET /v1/instances/[instanceId]` | GET | Full instance data with upstream metadata |
| `POST /v1/instances/[instanceId]/submit` | POST | Submit annotations |
| `POST /v1/instances/[instanceId]/skip` | POST | Skip instance |
| `PUT /v1/instances/[instanceId]/draft` | PUT | Save draft annotations |
| `POST /v1/instances/[instanceId]/verdict` | POST | Validation verdict (accept/reject/flag) |

**Instance response (for annotation canvas):**

```typescript
interface InstanceResponse {
  id: string;
  campaign_id: string;
  task_id: string;
  task_type: 'supply' | 'labeling' | 'validation';
  pipeline_config: PipelineBarConfig;   // For rendering the context bar
  pipeline_state: PipelineState;        // Current instance state
  instance_data: Record<string, any>;   // Content to annotate
  annotation_config: string;            // XML config for the runtime
  suggestions?: Annotation[];           // Agent pre-labeling
  previous_annotations?: Annotation[];  // For validation
  upstream: UpstreamContext[];           // For context header
  session: SessionProgress;             // Instances completed this session
}

interface UpstreamContext {
  stage_id: string;
  stage_label: string;
  contributor_handle: string;
  timestamp: string;
  quality_score?: number;
}

interface SessionProgress {
  completed: number;
  available: number;
  earnings_today: number;
  session_quota?: number;               // Daily cap, if any
}
```

**Submit request:**

```typescript
interface SubmitRequest {
  annotations: Annotation[];            // From the annotation runtime
  time_spent_ms: number;                // Time on this instance
}
```

**Verdict request (validation only):**

```typescript
interface VerdictRequest {
  verdict: 'accept' | 'reject' | 'flag';
  rejection_reason?: string;            // From rubric
  rejection_note?: string;              // Free text
  amended_annotations?: Annotation[];   // If validator corrected
}
```

---

## My Tasks

| Endpoint | Method | Description |
|---|---|---|
| `GET /v1/contributor/enrollments` | GET | All enrolled campaigns with summary stats |
| `GET /v1/contributor/submissions` | GET | Paginated list of submitted instances with pipeline state |
| `GET /v1/contributor/submissions?campaign_id=X&status=rejected` | GET | Filtered submissions |

**Submissions response:**

```typescript
interface SubmissionListResponse {
  submissions: {
    instance_id: string;
    campaign_name: string;
    task_type: 'supply' | 'labeling' | 'validation';
    pipeline_state: PipelineState;      // For compact bar rendering
    submitted_at: string;
    current_stage: string;
    earnings?: number;
    rejection_reason?: string;
  }[];
  total: number;
}
```

---

## Earnings

| Endpoint | Method | Description |
|---|---|---|
| `GET /v1/contributor/earnings/summary` | GET | Total earned, pending, royalties |
| `GET /v1/contributor/earnings/by-campaign` | GET | Pipeline breakdown per campaign |
| `GET /v1/contributor/earnings/transactions` | GET | Paginated transaction history |

**Pipeline breakdown:**

```typescript
interface CampaignEarningsBreakdown {
  campaign_id: string;
  campaign_name: string;
  compensation_model: 'fixed' | 'bounty' | 'hybrid' | 'royalty';
  total_submitted: number;
  states: {
    state: string;                      // e.g., "royalty_eligible", "in_labeling"
    count: number;
    earnings: number;
  }[];
  pipeline_velocity?: string;           // e.g., "~4 hrs supply → labeled"
  stalled: boolean;
  stalled_since?: string;
}
```

---

## Notifications

| Endpoint | Method | Description |
|---|---|---|
| `GET /v1/contributor/notifications` | GET | Unread notifications |
| `PUT /v1/contributor/notifications/[id]/read` | PUT | Mark as read |
| `POST /v1/contributor/notifications/subscribe` | POST | Subscribe to queue refill, rejection alerts, etc. |

**Notification types:**

| Type | Trigger |
|---|---|
| `submission_accepted` | Instance accepted by quality gate |
| `submission_rejected` | Instance rejected (with reason) |
| `queue_refilled` | Subscribed queue has 10+ instances again |
| `royalty_unlocked` | Instances reached royalty-eligible |
| `campaign_stalled` | No pipeline movement in 5+ days |
| `campaign_ending` | Campaign closes in 48 hours |
