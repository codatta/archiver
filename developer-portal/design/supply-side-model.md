# Supply-Side Model — User, Credentials, Reputation & Task Infrastructure

> Source: Deep analysis of `cfp-user` and `cfp-metacore` codebases (2026-03-27)
> Purpose: Understand the existing supply-side model to inform Developer Portal integration

---

## User Model (cfp-user)

### Core Identity

```
CfpCustomerUser
├── user_id (PK)
├── status: NORMAL | CANCEL
├── user_name, avatar
├── did: Decentralized Identity (nullable)
├── referee_code: 12-char invite code (unique, auto-generated)
├── inviter_code: who referred this user
├── source: JSON (registration metadata)
├── related_info: JSON (extended profile)
├── app_msg_switch, app_device_id (mobile push)
```

### Linked Accounts (multi-wallet, multi-email)

```
CfpCustomerUserAccount
├── user_id FK
├── account_type: "block_chain" | "email"
├── account: wallet address or email
├── connector: MetaMask | WalletConnect | etc.
├── chain: eth | bsc | tron | ton | etc.
├── wallet_name, public_identifier
```

**Auth flow:** Wallet signature verification (EIP-191, TON Connect) or email OTP → session JWT + legacy token.

### Roles

```
CfpRole
├── user_id
├── role: CUSTOMER (worker) | BUSINESS (frontier creator)
```

**Note:** There is NO "developer/consumer" role. The BUSINESS role is for frontier creators (supply-side admins), not demand-side developers. This confirms the identity systems should remain independent.

---

## Credential / Qualification System

### User Qualifications (self-declared, partially audited)

Stored in `CfpUserQualification.content` as structured JSON:

```json
{
  "basic_info": {
    "birth_place_country": "US",
    "birth_place_state": "CA",
    "birth_place_city": "San Francisco",
    "current_residence_country": "JP",
    "current_residence_state": "Tokyo",
    "current_residence_city": "Shibuya",
    "birth_year": 1990,
    "gender": "male"
  },
  "language_skills": {
    "native_language": ["English"],
    "other_language": ["Japanese", "Mandarin"],
    "level": ["fluent", "conversational"]
  },
  "education_background": {
    "audit_status": "VERIFIED | PENDING | REJECTED",
    "audit_reason": "...",
    "highest_degree": "bachelor | master | doctorate | postdoctoral | pre_bachelor",
    "university": "Stanford University",
    "major": ["Computer Science", "Data Science"],
    "status": "enrolled | graduated"
  },
  "professional_role": {
    "occupation_area": [
      "web3_blockchain",
      "internet_it_technology",
      "medical_healthcare",
      "legal",
      "finance_accounting",
      "education_research_academic",
      "design_arts_media",
      "engineering_manufacturing",
      "business_sales_administration",
      "serviceIndustry_freelance",
      "student",
      "other"
    ]
  }
}
```

**Audit status:** Only `education_background` requires manual verification (PENDING → VERIFIED/REJECTED). All other fields are self-declared.

### Qualification Templates (gating rules)

Stored in `cfp_qualification_template`:

```json
{
  "rules": [
    { "field": "country", "operator": "in", "value": ["JP", "US"] },
    { "field": "language", "operator": "in", "value": ["Japanese"] },
    { "field": "highest_degree", "operator": "in", "value": ["bachelor", "master", "doctorate"] },
    { "field": "occupation_area", "operator": "in", "value": ["web3_blockchain"] }
  ]
}
```

**Applied at two levels:**
1. **Frontier-level** — `cfp_frontier.ext_info.qualification` → blocks all tasks in frontier
2. **Task-level** — `cfp_frontier_task.data_display.qualification_config` → blocks specific task

---

## Reputation System

### Reputation Formula

```
reputation = 0.1 * r_identify
           + 0.2 * r_login
           + 0.3 * r_staking
           + 0.4 * r_contribution
           - r_malicious_behavior
```

| Component | Weight | What it measures |
|-----------|--------|-----------------|
| `r_identify` | 10% | Identity verification completeness |
| `r_login` | 20% | Login frequency / engagement |
| `r_staking` | 30% | XNY tokens staked: `100 * min(1, staking_amount / 50000)` |
| `r_contribution` | 40% | Quality/quantity of task completions |
| `r_malicious_behavior` | penalty | Spam reports, rejected submissions |

### Reputation → Task Access

- Each task has a `reputation` threshold (stored in `data_display.reputation`)
- If user reputation < threshold:
  - System calculates additional staking needed
  - User can stake XNY to temporarily boost `r_staking` component
  - `can_start_task`: 1 = eligible, 2 = impossible even with max staking

### Badge System (achievement-based)

```
Badge Category Tree:
  Root
  ├── Category A (e.g., "Community")
  │   ├── Badge A1
  │   │   ├── Level 1 (bronze)
  │   │   ├── Level 2 (silver)
  │   │   └── Level 3 (gold)
  │   └── Badge A2
  └── Category B (e.g., "Contribution")
```

Badges are **unlocked by achievements** (points thresholds, task counts, qualification completion, referral counts). They contribute to the user's public profile and leaderboard ranking but are **separate from the numeric reputation score**.

---

## Task Infrastructure (cfp-metacore)

### Entity Hierarchy

```
Frontier (business domain / vertical)
├── frontier_id, title, description, logo
├── status: PREPARING → ONLINE → PAUSED → OFFLINE
├── qualification: template_id (gates all tasks)
├── reputation_permission: min reputation
├── supported_devices: ["pc", "app"]
│
├── Task (unit of work within frontier)
│   ├── task_id, name, task_type: submission | validation
│   ├── template_id → cfp_task_templates (data schema)
│   ├── status: PREPARING → COLLECTING → FINISHED/PAUSE/STOP
│   ├── data_display: { qualification_config, reputation, multi_validated_flag }
│   ├── reward_info: [{ reward_mode: REGULAR|DYNAMIC|AIRDROP, reward_type, reward_value }]
│   ├── max_count: submission limit
│   ├── duplicate_permission: bool
│   ├── start_time, end_time
│   │
│   └── Submission (completed work)
│       ├── submission_id, user_id, task_id
│       ├── data_submission: JSON (worker output + metadata)
│       ├── status: PENDING → SUBMITTED → ADOPT | REFUSED | REPORT_SPAM
│       ├── result: 1-5 (maps to D/C/B/A/S grade)
│       ├── reward_info: [{ transaction_id, reward_type, reward_value, operate }]
│       ├── source: MOBILE | PC
│       └── chain_status: 0 → 1 → 2 → 3 (on-chain confirmation)
│
└── Activity (campaign / reward pool)
    ├── activity_id, frontier_id
    ├── reward_mode: FIRST_COME_FIRST_SERVE | EQUAL_SPLIT_ON_END
    ├── total_asset_amount, reward_asset_type: USDT | POINT | XNY
    ├── max_reward_count (for FCFS)
    ├── start_time, end_time
    ├── is_reward_settled: bool
    └── task_reward_config: { task_id: { reward_mode, min_ranking_grade, max_reward_count } }
```

### Task Types

| Type | Purpose | Duplicate allowed? | Multi-validator? |
|------|---------|-------------------|-----------------|
| `submission` | Original data contribution | Configurable | No |
| `validation` | Review/validate others' submissions | Never | Yes (configurable count) |

### Quality Pipeline

1. **Submit** → auto-audit via `cfp_task_audit_templates` rules (duplicate checks, schema validation)
2. **Audit result** → ADOPT / REJECT / REPORT_SPAM
3. **Rating** → 1-5 numeric → S/A/B/C/D grade
4. **On-chain** → fingerprint stored via `cfp_task_chain_record`

### Reward Modes

| Mode | When paid | Amount |
|------|-----------|--------|
| REGULAR | On submit | Fixed per submission |
| DYNAMIC | On ADOPT (audit pass) | Variable based on grade |
| AIRDROP | Season-based bonus | Pool split among eligible |

---

## Mapping to Developer Portal Task Launching

### What developers can target (worker_requirements)

Based on the existing qualification system, developers can gate tasks by:

| Requirement | Field in cfp-user | How it works |
|------------|------------------|-------------|
| **Country** | `basic_info.current_residence_country` | ISO code match |
| **Language** | `language_skills.native_language` + `other_language` | Array intersection |
| **Language proficiency** | `language_skills.level` | Min level check |
| **Education level** | `education_background.highest_degree` | Enum comparison |
| **Education verified** | `education_background.audit_status` | Must be VERIFIED |
| **Field of study** | `education_background.major` | Array intersection |
| **Occupation** | `professional_role.occupation_area` | Array intersection |
| **Gender** | `basic_info.gender` | Exact match |
| **Min reputation** | Computed score | Numeric threshold |
| **Custom qualification** | Via qualification_template | Rule-based check |

### CfpAdapter qualification mapping

When a developer sets `worker_requirements` in our portal:

```python
# Our format (developer-facing)
worker_requirements = {
    "actor_types": ["human"],
    "credentials": ["verified_education"],
    "countries": ["JP", "US"],
    "languages": ["ja"],
    "skills": ["web3_blockchain"],
    "min_reputation": 60.0
}

# CfpAdapter translates to qualification_template:
{
    "rules": [
        {"field": "country", "operator": "in", "value": ["JP", "US"]},
        {"field": "language", "operator": "in", "value": ["Japanese"]},
        {"field": "occupation_area", "operator": "in", "value": ["web3_blockchain"]},
        {"field": "education_background_status", "operator": "equals", "value": "VERIFIED"}
    ]
}
# + sets reputation threshold on task data_display
```

### Status mapping

| cfp-metacore | Our status | Notes |
|-------------|-----------|-------|
| PENDING | pending_review | Awaiting audit |
| SUBMITTED | pending_review | On-chain submitted, not yet reviewed |
| ADOPT | adopted | Accepted, rewards issued |
| REFUSED | disputed | Rejected by audit/creator |
| REPORT_SPAM | disputed | Flagged as malicious |

### Grade → quality_score mapping

| Grade | Numeric (result) | Our quality_score |
|-------|-----------------|-------------------|
| S | 5 | 0.97 |
| A | 4 | 0.85 |
| B | 3 | 0.70 |
| C | 2 | 0.50 |
| D | 1 | 0.30 |

---

## Key Takeaways for Integration

1. **Qualification system is rich and reusable** — demographics, education, occupation, language, reputation. CfpAdapter can map developer requirements to qualification templates.

2. **No KYC in the traditional sense** — "verified" only applies to education background (manual audit). Identity verification (`r_identify` in reputation) is basic. No government ID, no biometrics.

3. **Reputation is stakeable** — users can boost reputation by staking XNY tokens. This means a "min_reputation: 80" requirement doesn't purely measure quality — it also measures financial commitment.

4. **Two task types map to our model** — `submission` = collection/annotation/survey/errand. `validation` = quality review. Our task types are more granular but the underlying mechanics are the same.

5. **Activity ≈ our Campaign** — but admin-only. CfpAdapter needs to create Activities programmatically on behalf of developers.

6. **Reward system is token-based** — POINTS, USDT, XNY with on-chain settlement. Developer pays USD via Stripe → we need a USD→token bridge for worker rewards.

7. **No AI agent worker concept yet** — `actor_type` doesn't exist in cfp-user. When AI agent workers are introduced, the qualification and reputation systems will need extension.
