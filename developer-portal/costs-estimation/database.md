# Database Migration Cost Estimation: AliCloud RDS -> Supabase

> Updated: 2026-03-29
> Scope: Consolidate supply-side data (AliCloud RDS MySQL, Singapore) into existing Supabase project, estimate ongoing Supabase cost based on **actual data and access patterns**.

---

## 1. What's Being Migrated

### AliCloud RDS MySQL Tables (cfp_user + cfp_metacore databases)

| Table | Rows | Est. Row Size | Est. Storage | Write Freq | Read Freq |
|-------|-----:|------:|------:|------|------|
| `cfp_customer_user` | 19.5M | ~0.5 KB | ~9.8 GB | Near-zero (growth stopped) | Low — profile lookups |
| `cfp_customer_user_account` | 19.4M | ~0.4 KB | ~7.8 GB | Near-zero | Low — wallet lookups |
| `cfp_login_log` | ~20M | ~0.2 KB | ~4.0 GB | ~300/day (8.4K login/7d) | Rare — analytics only |
| `cfp_user_qualification` | ~175K | ~1.0 KB | ~0.2 GB | Near-zero | Rare — qualification checks |
| `cfp_qualification_template` | < 1K | ~2.0 KB | < 1 MB | Rare | Rare |
| `cfp_frontier` | ~12 | ~1.0 KB | < 1 MB | Rare (admin) | Moderate — listing |
| `cfp_frontier_task` | ~100s | ~1.0 KB | < 1 MB | Low | Moderate |
| `cfp_submission` | 4.04M | ~1.0 KB | ~4.0 GB | ~1/day (33 submitters/7d) | Moderate — status checks |
| `cfp_activity` (rewards pool) | ~100s | ~0.5 KB | < 1 MB | Low | Low |
| Reward transactions | 5.76M | ~0.3 KB | ~1.7 GB | Near-zero | Low — history |
| `cfp_task_chain_record` | 3.27M | ~0.3 KB | ~1.0 GB | Near-zero | Rare |
| Audit/QA records | 2.72M | ~0.3 KB | ~0.8 GB | Near-zero | Rare |
| Social bindings, quiz, misc | ~1M | ~0.3 KB | ~0.3 GB | Near-zero | Rare |
| **Indexes & overhead (+30%)** | — | — | **~8.9 GB** | | |
| **Subtotal (AliCloud)** | | | **~38.5 GB** | | |

### Existing Supabase (Demand-Side Portal)

| Dataset | Rows | Storage |
|---------|-----:|-------:|
| 13 portal tables | < 50K | < 100 MB |
| Auth users (portal) | < 1K | < 10 MB |
| File storage (logos) | — | < 50 MB |
| **Subtotal** | | **< 200 MB** |

### Post-Migration Total: **~40 GB database**

---

## 2. Actual Access Patterns (from production data, 2026-03-27)

This is the critical input the previous estimate was missing. The platform has **19.5M registered users but minuscule actual activity**:

| Metric | Value | Implication |
|--------|------:|-------------|
| **Registered users** | 19,466,103 | Storage cost, not compute cost |
| **Login 7d** | 8,410 | ~1,200/day peak |
| **Login 30d (MAU)** | 9,899 | **Actual MAU ≈ 10K** |
| **Login 90d** | 147,857 | Seasonal/campaign spikes |
| **Active submitters 30d** | 84 | Almost no write traffic |
| **Active submitters 7d** | 33 | ~5 submissions/day |
| **New user registration** | Near-zero | Growth campaign ended |
| **Concurrent users (est.)** | ~200–500 peak | Based on 1.2K logins/day |

### Query Load Profile

| Query Type | Frequency | Pattern |
|------------|-----------|---------|
| Auth (login/session) | ~1,200/day | Read-heavy, indexed lookups |
| Profile/wallet reads | ~2,000/day | Point queries by user_id |
| Submission writes | ~5–10/day | Single row inserts |
| Submission status reads | ~500/day | Filtered list queries |
| Reward history reads | ~200/day | Paginated range scans |
| Analytics (admin) | ~10/day | Heavy aggregations (can be async) |
| Frontier/task listing | ~1,000/day | Small table, fully cacheable |

**Total estimated queries: ~5,000–8,000/day ≈ 0.1 QPS average, ~1 QPS peak**

This is trivially small. A Supabase Micro instance (2 vCPU, 1 GB RAM) can handle 100+ QPS on indexed Postgres queries.

---

## 3. Supabase Cost: Current Reality (~10K MAU)

| Resource | Actual Usage | Included (Pro $25/mo) | Excess | Monthly Cost |
|----------|-------------|----------------------:|-------:|-------------:|
| **Base plan** | Pro | — | — | **$25.00** |
| **Compute** | Micro (included) | 2 vCPU / 1 GB | — | **$0** |
| **Database storage** | ~40 GB | 8 GB | 32 GB | **$4.00** |
| **Auth MAU** | ~10K | 100K | 0 | **$0** |
| **Bandwidth** | ~5 GB/mo | 250 GB | 0 | **$0** |
| **Realtime connections** | ~50 peak (portal only) | 500 | 0 | **$0** |
| **File storage** | < 1 GB | 100 GB | 0 | **$0** |
| | | | **Total** | **~$29/mo** |

**That's it. $29/month** to serve 19.5M stored user records with 10K MAU.

### Why so cheap?

1. **Auth MAU bills on logins, not stored users.** 19.5M rows in the users table cost $4/mo in storage, not $63K in auth fees. Only the ~10K who actually authenticate each month count as MAU.
2. **Query volume is negligible.** ~5K queries/day is nothing for Postgres. The Micro instance (included free with Pro) handles this easily.
3. **No realtime needed for supply-side.** The portal's realtime subscriptions (delivery_items) serve demand-side orgs, not supply-side workers. Supply-side access is request-response only.
4. **Data is cold.** 95.9% of users came from a single referral campaign, logged in once, and never returned. Their rows sit on disk, costing $0.125/GB — that's it.

---

## 4. Growth Scenarios (Based on Realistic Trajectories)

Unlike the previous estimate that assumed hypothetical MAU, these scenarios are grounded in what would actually change from current state.

### Scenario A: Steady State (no growth campaigns) — Current

| | Value |
|---|---:|
| MAU | ~10K |
| Database | ~40 GB |
| Monthly cost | **$29/mo** |
| Annual cost | **$348/yr** |
| vs AliCloud RDS est. | Saves ~$270–520/mo |

### Scenario B: Moderate Reactivation Campaign — 100K MAU

*What changes:* Marketing reactivates dormant users. 100K of the existing 19.5M log back in monthly. Some new task submissions.

| Resource | Usage | Included | Excess | Cost |
|----------|-------|------:|------:|-----:|
| Base plan (Pro) | — | — | — | $25 |
| Compute | Small (2 GB) | — | — | $25 |
| Database storage | ~42 GB | 8 GB | 34 GB | $4.25 |
| Auth MAU | 100K | 100K | 0 | $0 |
| Bandwidth | ~50 GB | 250 GB | 0 | $0 |
| Realtime | ~200 peak | 500 | 0 | $0 |
| **Total** | | | | **~$54/mo** |

**Why Small compute:** 100K MAU = ~3.3K logins/day = ~15K queries/day. Still light, but bumping to 2 GB RAM keeps the 40 GB dataset's hot pages cached better.

### Scenario C: Major Growth — 1M MAU

*What changes:* New acquisition campaign brings 1M monthly active. Active submitters grow from 84 to ~5,000. Daily query volume hits ~150K.

| Resource | Usage | Included | Excess | Cost |
|----------|-------|------:|------:|-----:|
| Base plan (Pro) | — | — | — | $25 |
| Compute | Medium (4 GB) | — | — | $50 |
| Database storage | ~55 GB | 8 GB | 47 GB | $5.88 |
| Auth MAU | 1M | 100K | 900K | $2,925 |
| Bandwidth | ~500 GB | 250 GB | 250 GB | $22.50 |
| Realtime | ~1,000 peak | 500 | 500 | $5 |
| **Total** | | | | **~$3,033/mo** |

**Auth dominates at 96% of cost.** Everything else is cheap. At this scale, self-hosting GoTrue (Supabase's auth service) on a $50/mo Cloud Run instance would drop the bill to ~$108/mo.

### Scenario D: Full Scale — 10M MAU

*What changes:* All 19.5M dormant users reactivated + new signups. 10M authenticate monthly. ~50K active submitters.

| Resource | Usage | Included | Excess | Cost |
|----------|-------|------:|------:|-----:|
| Base plan (Team) | — | — | — | $599 |
| Compute | Large (8 GB) | — | — | $100 |
| Database storage | ~100 GB | 8 GB | 92 GB | $11.50 |
| Auth MAU | 10M | 100K | 9.9M | $32,175 |
| Bandwidth | ~5 TB | 250 GB | ~4.75 TB | $427.50 |
| Realtime | ~10,000 peak | 500 | 9,500 | $95 |
| **Total (list)** | | | | **~$33,408/mo** |
| **Enterprise (est. 30-40% off)** | | | | **~$20,000–23,400/mo** |

---

## 5. Cost Summary Table

| Scenario | MAU | Database Size | Queries/Day | Supabase Cost | Auth % of Bill |
|----------|----:|------:|------:|------:|------:|
| **Current** | 10K | 40 GB | ~5K | **$29/mo** | 0% |
| **Reactivation** | 100K | 42 GB | ~15K | **$54/mo** | 0% |
| **Growth** | 1M | 55 GB | ~150K | **$3,033/mo** | 96% |
| **Full scale** | 10M | 100 GB | ~1.5M | **$33,408/mo** | 96% |

---

## 6. Auth Cost Mitigation (Only Relevant at 1M+ MAU)

Below 100K MAU, **do nothing** — it's free within the Pro plan.

Above 1M MAU, auth is 96% of the bill. Options:

| Strategy | Saves | Effort | Tradeoff |
|----------|------:|--------|----------|
| Self-host GoTrue on Cloud Run | ~$2.9K/mo at 1M | 1–2 weeks | You own uptime and upgrades |
| Use external auth (Auth0 free tier, Clerk, or custom JWT) | ~$2.9K/mo at 1M | 2–3 weeks | Lose Supabase RLS integration |
| Negotiate Enterprise pricing | ~30–40% | 0 effort | Minimum spend commitment |
| Hybrid: Supabase Auth for portal, custom JWT for supply-side | ~$2.9K/mo at 1M | 1 week | Two auth systems to maintain |

**Recommendation:** Cross this bridge when MAU actually approaches 100K. Today, the answer is Pro plan at $29/mo.

---

## 7. AliCloud RDS Shutdown Savings

| AliCloud Component | Estimated Current Cost | Post-Migration |
|--------------------|----------------------:|---------------:|
| RDS MySQL (test instance) | ~$50–100/mo | $0 |
| RDS MySQL (prod instance) | ~$150–300/mo | $0 |
| RDS storage (38 GB) | ~$30–50/mo | $0 |
| RDS backup | ~$10–20/mo | $0 |
| **Total saved** | **~$240–470/mo** | |

**Net savings at current usage: ~$210–440/mo** (save $240–470 on AliCloud, add $29 on Supabase).

---

## 8. One-Time Migration Cost

| Item | Cost | Notes |
|------|-----:|-------|
| AliCloud egress | ~$4 | 40 GB × $0.10/GB |
| Supabase import (temp scale-up) | ~$10 | Scale to Small for bulk load, revert to Micro after |
| Engineering time | 2–5 days | Schema conversion (MySQL → Postgres), pgloader, data validation |
| **Total infra** | **~$14** | |

---

## 9. Bottom Line

| | Current (AliCloud + Supabase) | Post-Migration (Supabase only) |
|---|---:|---:|
| Monthly cost | ~$270–520 | **~$29** |
| Annual cost | ~$3,200–6,200 | **~$348** |
| Services managed | 2 (RDS + Supabase) | 1 |
| Databases to monitor | 2 | 1 |
| Auth systems | Separate per platform | Unified |

**The migration pays for itself in the first month.** At current usage (~10K MAU, ~5K queries/day), the entire consolidated database runs on Supabase Pro for $29/mo — including 40 GB of storage for 19.5M user records that are overwhelmingly cold data.

Auth pricing only becomes a concern if MAU grows 100× from current levels to 1M+. That's a good problem to have, and the mitigation path (self-host GoTrue) is well-understood.
