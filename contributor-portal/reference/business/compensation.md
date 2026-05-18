# Compensation Models

> How contributors get paid. The compensation model is set per-campaign by the campaign creator and constrained by their org trust tier.

---

## Four Models

### Fixed

Pay a fixed amount per accepted submission.

| Property | Value |
|---|---|
| Trigger | Instance passes the task's quality gate |
| Timing | Within 48 hours of acceptance |
| Risk to contributor | Low — payment is guaranteed on acceptance |
| Escrow | Full campaign budget escrowed at launch |

```
Submit ──▶ Accepted ──▶ $2.50 credited
```

### Bounty

Pay on campaign-level milestone completion.

| Property | Value |
|---|---|
| Trigger | Campaign reaches a defined milestone (e.g., 1,000 instances completed) |
| Timing | On milestone completion |
| Risk to contributor | Medium — milestone may not be reached |
| Escrow | Bounty amount escrowed at launch |

```
Submit ──▶ ... ──▶ Campaign hits 1,000 ──▶ $500 distributed among contributors
```

### Hybrid

Fixed base per-instance + royalty on downstream usage.

| Property | Value |
|---|---|
| Trigger | Base: on acceptance. Royalty: on downstream usage |
| Timing | Base: within 48 hours. Royalty: ongoing |
| Risk to contributor | Mixed — base is guaranteed, royalty is speculative |
| Escrow | Base amount escrowed. Royalty comes from downstream revenue |

```
Submit ──▶ Accepted ──▶ $1.00 credited (base)
                    ──▶ ... ──▶ Data used by buyer ──▶ $0.80 royalty credited
```

### Royalty

Revenue share on downstream data usage. No upfront payment.

| Property | Value |
|---|---|
| Trigger | Instance completes all pipeline stages AND is consumed downstream |
| Timing | Ongoing — each downstream usage generates a royalty event |
| Risk to contributor | High — no payment unless pipeline completes and data is used |
| Escrow | None upfront; royalties come from marketplace revenue |

```
Submit ──▶ Accepted ──▶ Pipeline completes ──▶ Data purchased ──▶ $1.80 royalty
```

---

## Trust Tier Gating

The campaign creator's org trust tier constrains which models they can offer:

| Org trust tier | Available models |
|---|---|
| New | Fixed only |
| Verified | Fixed, Bounty |
| Established | Fixed, Bounty, Hybrid |
| Trusted | Fixed, Bounty, Hybrid, Royalty |

---

## Per-Task-Type Pay Rates

A campaign can set different pay rates for different task types within the same pipeline:

```json
{
  "compensation": {
    "model": "fixed",
    "rates": {
      "supply": { "amount": 2.50, "currency": "USD" },
      "labeling": { "amount": 1.50, "currency": "USD" },
      "validation": { "amount": 0.75, "currency": "USD" }
    }
  }
}
```

The campaign card and detail page show the per-task-type breakdown so specialists can assess fit.

---

## Royalty Pipeline States

For royalty and hybrid models, each instance has a royalty state:

| State | Meaning | Contributor sees |
|---|---|---|
| `not_started` | Instance hasn't completed pipeline | "In progress" |
| `pipeline_complete` | All stages passed | "Royalty-eligible" |
| `consumed` | Data purchased/used downstream | "$X.XX earned" |
| `expired` | Campaign ended, data not consumed | "No royalty" |

---

## Payout Mechanics

| Property | Value |
|---|---|
| Minimum payout threshold | $10.00 |
| Payout methods | Bank transfer, crypto wallet, platform credits |
| Payout frequency | Weekly (automatic) or on-demand above threshold |
| Currency | USD (displayed); crypto option for on-chain settlements |

---

## Campaign Cancellation Rules

| Scenario | Fixed pay | Royalty |
|---|---|---|
| Campaign cancelled before any work | Full escrow returned to org | N/A |
| Campaign cancelled mid-flight | Accepted submissions already paid | Instances that completed pipeline retain royalty eligibility; incomplete pipeline instances get no royalty |
| Campaign completed normally | All accepted work paid | Royalties accrue as data is consumed |

---

## Display in UI

### Campaign Card — Compensation Pill

```
Fixed:    ┌ 💵  $2.50 / instance  ·  Fixed pay        ┐
Royalty:  ┌ 📈  Revenue share  ·  est. $1.80/instance  ┐
Hybrid:   ┌ 🔀  $1.00 + royalty                        ┐
Bounty:   ┌ 🎯  $500 milestone                         ┐
```

### Campaign Detail — Earnings Estimate

Show projected earnings based on platform averages:

```
Estimated earnings:
  • 10 instances/day → $25/day → $175/week
  • Top contributors average 15 inst/day → $262/week
```

### Earnings Screen — Pipeline Breakdown (royalty)

```
50 instances submitted
  30 ◆ royalty-eligible ($54.00 earned)
  12   in labeling
   5   in label-validate
   3   rejected at supply-validate
```
