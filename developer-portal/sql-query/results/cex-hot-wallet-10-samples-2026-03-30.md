# CEX Hot Wallet — 10 Complete Samples (Submission + Audit + Reward)

> Source: AliCloud RDS Prod (`cfp_metacore`)
> Frontier: **CEX Hot Wallet** (`frontier_id: 8114254168500106625`)
> Date pulled: 2026-03-30
> Filter: `status = ADOPT` with audit record present, ordered by `gmt_create DESC`

---

## Frontier Summary

- **877,001 total submissions** across 30 tasks
- Task types: deposit address collection, withdraw address collection, label deposits/withdrawals
- Two template versions observed:
  - **V2 ("Label" tasks)** — rich structured: tx_hash, sender/receiver addresses, amounts, network fees, exchange UI + explorer screenshots
  - **V1 ("Collect" tasks)** — simpler: screenshot image + network/currency/exchange metadata

---

## Sample 1 — Withdrawal Label (Binance, BSC-USDT)

| Field | Value |
|-------|-------|
| **submission_id** | `2026021815500000101834` |
| **user_id** | `159041695535104` |
| **task** | Label Withdrawals: Binance, IndoEx, Tokocrypto, CoinW, CEX.IO, Ju.com, Bitso, Upbit, P2B, CoinUp.io |
| **template** | `AIRDROP_CEX_HOT_WALLET_WITHDRAW` |
| **device** | web |
| **submitted_at** | 2026-02-18 15:50:01 |

### Submission Data
```json
{
  "coin": "BSC-USDT",
  "type": "withdrawal",
  "amount": "9.99",
  "network": "BNB",
  "network_fee": "0.01",
  "exchange_name": "Binance",
  "transaction_date": "2026-02-15",
  "tx_hash": "0x210b86f1ddfdd86551cbcd5dc19488656429bf4ada9bec9b63551c9c14d3ba49",
  "sender_address": "0xa180Fe01B906A1bE37BE6c534a3300785b20d947",
  "receiver_address": "0x8f4d466606f280C7402153f1f0101928c1819DAC",
  "explorer_screenshot_url": "https://file.b18a.io/159041695535104_187194_.jpg",
  "explorer_screenshot_hash": "09cca4cce14cce31b174222f9f7846bb802e06d4093ad5a04951d7e7f6b12d55",
  "exchange_ui_screenshot_url": "https://file.b18a.io/159041695535104_422166_.jpg",
  "exchange_ui_screenshot_hash": "04706e6ffe73bf79603f638de7feadf3fb03588fef1da6bb6035a2f76c7f492d"
}
```

### Audit
| Field | Value |
|-------|-------|
| **audit_result** | ADOPT |
| **rating** | A (grade 4) |
| **reason** | Hot wallet address duplicate |
| **audited_at** | 2026-02-25 07:50:13 |

### Reward
| Field | Value |
|-------|-------|
| **reward_type** | POINTS |
| **reward_value** | 300 |
| **rewarded_at** | 2026-02-25 07:50:34 |

---

## Sample 2 — Deposit Label (Binance, SOL)

| Field | Value |
|-------|-------|
| **submission_id** | `2026021206270700101743` |
| **user_id** | `7953426800300103587` |
| **task** | Label Deposits: Binance, IndoEx, Tokocrypto, CoinW, CEX.IO, Ju.com, Bitso, Upbit, P2B, CoinUp.io |
| **template** | `AIRDROP_CEX_HOT_WALLET_DEPOSIT` |
| **device** | mobile |
| **submitted_at** | 2026-02-12 06:27:07 |

### Submission Data
```json
{
  "type": "deposit",
  "token": "SOL",
  "amount": "0.022",
  "network": "SOL",
  "date": "2026-02-05",
  "exchange_name": "Binance",
  "tx_hash": "4kRVvxNcewE7U5Tgrbz1kjc8ubwjJj2b8TCBC5AL7nUU8tdXyKmJtkbNjPa5QuYtRGg2dPhMBuWtycR67uQH5M1z",
  "from_address": "BrKAnHHohZtZLDoCfEdjapmt1MEucxvMXgHJN5na95ok",
  "to_address": "2L9vyfHHrpNUDPpR2pc4mLtft9dR5eXdzqERBvKMCstt",
  "exchange_address": "2L9vyfHHrpNUDPpR2pc4mLtft9dR5eXdzqERBvKMCstt",
  "has_outgoing_transaction": true,
  "outgoing_tx_from_address": "2L9vyfHHrpNUDPpR2pc4mLtft9dR5eXdzqERBvKMCstt",
  "outgoing_tx_to_address": "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9",
  "outgoing_transaction_hash": "n3L92uqfGGt21HXrRgzygJPxRX5TgtzTzY8eyCjHNPc8kMRVMTrdkJVeFbHBnJBFNe9LHkspLiws5od75TBqpY4",
  "explorer_screenshot_url": "https://file.b18a.io/7953426800300103587_712762_.jpg",
  "exchange_ui_screenshot_url": "https://file.b18a.io/7953426800300103587_785829_.jpg",
  "outgoing_tx_screenshot_url": "https://file.b18a.io/7953426800300103587_401361_.jpg"
}
```

### Audit
| Field | Value |
|-------|-------|
| **audit_result** | ADOPT |
| **rating** | S (grade 5) |
| **reason** | — |
| **audited_at** | 2026-02-12 07:05:41 |

### Reward
| Field | Value |
|-------|-------|
| **reward_type** | POINTS |
| **reward_value** | 300 |
| **rewarded_at** | 2026-02-12 07:10:32 |

---

## Sample 3 — Deposit Image Collection (Binance, BNB/BSC)

| Field | Value |
|-------|-------|
| **submission_id** | `2026011203441600108479` |
| **user_id** | `389237510328320` |
| **task** | Collect deposit address images from exchanges. |
| **template** | `CRYPTO_TPL_DEPOSIT` |
| **device** | codatta (app) |
| **submitted_at** | 2026-01-12 03:44:16 |

### Submission Data
```json
{
  "type": "deposit",
  "exchange": "binance",
  "network": "bsc",
  "currency": "bnb",
  "source": "codatta",
  "images": [
    {
      "url": "https://file.b18a.io/389237510328320_613032_.png",
      "hash": "89884af6105e06ebab99edb6185e1d96b43fea46323978fa369ccb57f75516d1"
    }
  ]
}
```

### Audit
| Field | Value |
|-------|-------|
| **audit_result** | ADOPT |
| **rating** | — (auto-audit, grade 3 = B) |
| **reason** | — |
| **audited_at** | 2026-01-12 04:23:19 |

### Reward
| Field | Value |
|-------|-------|
| **reward_type** | POINTS |
| **reward_value** | 60 |
| **rewarded_at** | 2026-01-12 04:23:19 |

---

## Sample 4 — Deposit Image Collection (Binance, BNB/BSC)

| Field | Value |
|-------|-------|
| **submission_id** | `2026011203440300108478` |
| **user_id** | `389237510328320` |
| **task** | Collect deposit address images from exchanges. |
| **template** | `CRYPTO_TPL_DEPOSIT` |
| **device** | codatta (app) |
| **submitted_at** | 2026-01-12 03:44:03 |

### Submission Data
```json
{
  "type": "deposit",
  "exchange": "binance",
  "network": "bsc",
  "currency": "bnb",
  "images": [
    {
      "url": "https://file.b18a.io/389237510328320_120841_.png",
      "hash": "54c8ace64ead8cecdedef180d9f4e0dc67dce1ff53f57cede5ec2fddc0d59cd4"
    }
  ]
}
```

### Audit & Reward
| Field | Value |
|-------|-------|
| **audit_result** | ADOPT |
| **grade** | B (3) |
| **reward** | 60 POINTS |
| **audited_at** | 2026-01-12 04:23:17 |

---

## Sample 5 — Deposit Image Collection (Binance, BNB/BSC)

| Field | Value |
|-------|-------|
| **submission_id** | `2026011203434900108477` |
| **user_id** | `389237510328320` |
| **task** | Collect deposit address images from exchanges. |
| **template** | `CRYPTO_TPL_DEPOSIT` |
| **submitted_at** | 2026-01-12 03:43:50 |

### Submission Data
```json
{
  "type": "deposit",
  "exchange": "binance",
  "network": "bsc",
  "currency": "bnb",
  "images": [
    {
      "url": "https://file.b18a.io/389237510328320_549784_.png",
      "hash": "7d45d7a97c97f6d34abbf0120bc5f7aaf8e3023b61e04ffd208932bde07f2937"
    }
  ]
}
```

### Audit & Reward
| Field | Value |
|-------|-------|
| **audit_result** | ADOPT |
| **grade** | B (3) |
| **reward** | 60 POINTS |
| **audited_at** | 2026-01-12 04:23:19 |

---

## Sample 6 — Deposit Image Collection (Binance, BNB/BSC)

| Field | Value |
|-------|-------|
| **submission_id** | `2026011203433400108476` |
| **user_id** | `389237510328320` |
| **submitted_at** | 2026-01-12 03:43:34 |

### Submission Data
```json
{
  "type": "deposit",
  "exchange": "binance",
  "network": "bsc",
  "currency": "bnb",
  "images": [
    {
      "url": "https://file.b18a.io/389237510328320_590605_.png",
      "hash": "7d45d7a97c97f6d34abbf0120bc5f7aaf8e3023b61e04ffd208932bde07f2937"
    }
  ]
}
```

### Audit & Reward
| audit_result | grade | reward | audited_at |
|---|---|---|---|
| ADOPT | B (3) | 60 POINTS | 2026-01-12 04:23:17 |

---

## Sample 7 — Deposit Image Collection (Binance, BNB/BSC)

| Field | Value |
|-------|-------|
| **submission_id** | `2026011203431900108475` |
| **user_id** | `389237510328320` |
| **submitted_at** | 2026-01-12 03:43:20 |

### Submission Data
```json
{
  "type": "deposit",
  "exchange": "binance",
  "network": "bsc",
  "currency": "bnb",
  "images": [
    {
      "url": "https://file.b18a.io/389237510328320_785859_.png",
      "hash": "f5f763cd9c84a52bc0c76484d243bdc78d068c2856b6152737bb0143e304dbbb"
    }
  ]
}
```

### Audit & Reward
| audit_result | grade | reward | audited_at |
|---|---|---|---|
| ADOPT | B (3) | 60 POINTS | 2026-01-12 04:23:19 |

---

## Sample 8 — Deposit Image Collection (Binance, BNB/BSC)

| Field | Value |
|-------|-------|
| **submission_id** | `2026011203430400108474` |
| **user_id** | `389237510328320` |
| **submitted_at** | 2026-01-12 03:43:04 |

### Submission Data
```json
{
  "type": "deposit",
  "exchange": "binance",
  "network": "bsc",
  "currency": "bnb",
  "images": [
    {
      "url": "https://file.b18a.io/389237510328320_826051_.png",
      "hash": "88d66040c2aad6453a2608b2ee1854617e915904c5187a9e74036bdc56a5ad24"
    }
  ]
}
```

### Audit & Reward
| audit_result | grade | reward | audited_at |
|---|---|---|---|
| ADOPT | B (3) | 60 POINTS | 2026-01-12 04:13:51 |

---

## Sample 9 — Deposit Image Collection (Binance, BNB/BSC)

| Field | Value |
|-------|-------|
| **submission_id** | `2026011203425100108473` |
| **user_id** | `389237510328320` |
| **submitted_at** | 2026-01-12 03:42:51 |

### Submission Data
```json
{
  "type": "deposit",
  "exchange": "binance",
  "network": "bsc",
  "currency": "bnb",
  "images": [
    {
      "url": "https://file.b18a.io/389237510328320_845004_.png",
      "hash": "1b5b4b36fa4207dbf0bd99f9aa31415f98cbeaf35279c59916df4e51a5237cb2"
    }
  ]
}
```

### Audit & Reward
| audit_result | grade | reward | audited_at |
|---|---|---|---|
| ADOPT | B (3) | 60 POINTS | 2026-01-12 04:13:28 |

---

## Sample 10 — Deposit Image Collection (Binance, BNB/BSC)

| Field | Value |
|-------|-------|
| **submission_id** | `2026011203423900108472` |
| **user_id** | `389237510328320` |
| **submitted_at** | 2026-01-12 03:42:39 |

### Submission Data
```json
{
  "type": "deposit",
  "exchange": "binance",
  "network": "bsc",
  "currency": "bnb",
  "images": [
    {
      "url": "https://file.b18a.io/389237510328320_537651_.png",
      "hash": "d7a92d2f8e2fa1d8c1ed3c4c95282a5424bc4fa48ab59691a47777484776f886"
    }
  ]
}
```

### Audit & Reward
| audit_result | grade | reward | audited_at |
|---|---|---|---|
| ADOPT | B (3) | 60 POINTS | 2026-01-12 04:13:51 |

---

## Key Observations

### Two Data Template Versions

**V2 — "Label" tasks (Samples 1-2):**
- Rich structured data: tx_hash, sender/receiver addresses, amounts, fees
- Multiple screenshots: exchange UI, block explorer, outgoing tx
- Content hashing for dedup/integrity
- Higher rewards (300 POINTS)
- Human-rated: S/A grades

**V1 — "Collect" tasks (Samples 3-10):**
- Minimal structure: screenshot image + exchange/network/currency
- Single image per submission
- Auto-audited (no human rating)
- Lower rewards (60 POINTS)
- Grade B assigned uniformly

### No Validation Tasks

The CEX Hot Wallet frontier has **zero validation-type tasks** (`task_type = 'validation'`). All 30 tasks are `submission` type. Quality control is done via:
1. **Auto-audit** (duplicate hash check, schema validation) — V1 tasks
2. **Manual audit** (human review + rating) — V2 "Label" tasks

### Data Pipeline

```
Contributor submits → cfp_task_submission (PENDING)
  → Auto-audit (cfp_task_audit_record) → ADOPT/REFUSE
  → If ADOPT → cfp_task_reward (POINTS issued)
  → Grade assigned: S(5)/A(4)/B(3)/C(2)/D(1)
```
