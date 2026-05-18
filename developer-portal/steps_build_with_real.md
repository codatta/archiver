# Production System Investigation Runbook

> Use this runbook whenever you need to locate production data, credentials, services, or
> infrastructure that lives outside the current repository. Follow the steps in order — each
> step narrows the search space before you commit time to deep reading.

---

## Context: Why This Exists

During development of the Humanbased developer portal we needed to connect it to *real*
annotation data. The data lives in a completely separate backend (`omnitagServer`) managed by a
different team. This document captures the exact reasoning chain used to find it, so the same
methodology can be applied for:

- Connecting new services to existing production data
- Security audits (credential exposure, access surface mapping)
- Pre-refactor architecture snapshots (before migrating Python → Rust, etc.)

---

## Step 0 — Define Your Target

Before searching, write down in one sentence what you are looking for:

> "I need to find where [data type X] is stored so that [service Y] can [action Z]."

Example:
> "I need to find where validated crypto-account annotations are stored so that the developer
> portal can stream them to subscribers."

---

## Step 1 — List All Repositories in the Organisation

Start at the GitHub organisation level. Do not assume the data lives in the current repo.

```bash
gh repo list <org-name> --limit 100 --json name,description,updatedAt \
  | jq '.[] | [.name, .description] | @tsv' -r | sort
```

Scan descriptions for words related to your target:
- annotation, label, tag, submission, validation, review
- pipeline, ingestion, stream, queue, broker
- data, ml, model, training

For Codatta the winner was **`omnitagServer`** — the name and description matched
"annotation", "submission", "validation".

---

## Step 2 — Identify the Entry Points (Routes / Jobs)

Clone or browse the candidate repo. Look for route/controller files first — they reveal the
domain model fastest.

```bash
# Find route files
find . -type f -name "*route*" -o -name "*controller*" -o -name "*endpoint*" | head -30

# Or grep for FastAPI / Flask decorators
grep -r "@app.route\|@router\." --include="*.py" -l
```

Look for verbs that match your target flow:
- `submit`, `create`, `ingest` → write path
- `validate`, `review`, `adopt`, `dispute` → review/QA path
- `deliver`, `stream`, `export`, `publish` → read/consumer path

For `omnitagServer`: found `submission_route.py` and `validation_route.py` — confirmed this
handles the S1/S2/S3 validation pipeline for annotations.

---

## Step 3 — Read the Settings / Config File

Every backend has a single file that aggregates all connection strings. Common names:

| Framework | Config file |
|-----------|-------------|
| FastAPI / Flask | `settings.py`, `config.py`, `core/config.py` |
| Django | `settings.py` |
| Rails | `config/database.yml`, `config/credentials.yml.enc` |
| Go | `config.yaml`, `config.go`, `internal/config/` |
| Node | `.env`, `config/default.json` |

Read this file. Extract:
- Database URL (host, port, db name, user)
- Message broker URL (RabbitMQ, RocketMQ, Kafka, SQS)
- Storage bucket names (S3, GCS, OSS)
- External API endpoints

For `omnitagServer / setting.py`:
```
DB: mysql://codatta:***@codatta-test.rwlb.singapore.rds.aliyuncs.com:3306/omnitags_db_orm
Broker: RocketMQ on Alibaba Cloud
Storage: GCS bucket `ominitags-image`, Alibaba OSS
```

**Security note:** If credentials appear in plaintext in a committed file, log this as a
finding for the security audit. Do not copy raw credentials into this document — use
masked form (`***`) or reference the file path only.

---

## Step 4 — Map the Data Model

Once you have the DB connection, identify the tables that hold the data you care about.

```sql
-- MySQL / Postgres
SHOW TABLES;                      -- MySQL
\dt                               -- Postgres

-- Find tables related to your domain
SELECT table_name FROM information_schema.tables
WHERE table_name LIKE '%annotation%'
   OR table_name LIKE '%submission%'
   OR table_name LIKE '%delivery%';

-- Spot the write path
DESCRIBE ot_meta_submission;
SELECT * FROM ot_meta_submission LIMIT 3;
```

For Codatta: `ot_meta_submission` is the source table. Fields map to
`delivery_items` in Supabase.

---

## Step 5 — Trace the Data Flow End-to-End

Draw (or write) the full path data takes from creation to consumption:

```
[Annotator UI]
      ↓  POST /submission
[omnitagServer — FastAPI]
      ↓  INSERT ot_meta_submission
[MySQL — Alibaba RDS Singapore]
      ↓  S1/S2/S3 validation stages
      ↓  status = 'validated'
      ↓  ← GAP: no bridge service exists →
[delivery_items — Supabase Postgres Tokyo]   ← developer portal reads here
      ↓  Supabase Realtime
[developer.humanbased.ai — LiveStream UI]
```

Explicitly mark any **gaps** (missing services, manual steps, async delays). These are
action items for architecture work.

---

## Step 6 — Document Findings

For each system found, record:

| Field | Value |
|-------|-------|
| Service name | `omnitagServer` |
| Repo | `github.com/codatta/omnitagServer` |
| Language / framework | Python / FastAPI |
| DB type | MySQL 8 |
| DB host | `codatta-test.rwlb.singapore.rds.aliyuncs.com:3306` |
| DB name | `omnitags_db_orm` |
| Region | Alibaba Cloud Singapore |
| Key tables | `ot_meta_submission`, validation stage tables |
| Message broker | RocketMQ (Alibaba Cloud) |
| Storage | GCS `ominitags-image`, Alibaba OSS |
| Auth surface | DB user `codatta`, plaintext in `setting.py` |

**Security audit findings (from this investigation):**
- DB credentials committed in plaintext to `setting.py` → should be moved to env/secrets
  manager
- No TLS verification flag observed in DB connection string → verify SSL enforcement on RDS
- `codatta` DB user: unknown privilege scope → audit `SHOW GRANTS FOR 'codatta'@'%'`

---

## Step 7 — Decide the Integration Approach

After mapping the flow, choose one of:

| Approach | When to use |
|----------|------------|
| **Direct DB read** (MySQL connector) | Quick PoC, same VPC/region, low volume |
| **Bridge microservice** (poll + push) | Different clouds/regions, need transformation |
| **Event-driven** (broker subscription) | High volume, existing RocketMQ/Kafka already |
| **API wrapper** (call existing endpoints) | omnitagServer exposes a clean REST API |

For Codatta → recommended: **bridge microservice** that polls
`ot_meta_submission WHERE status = 'validated'` every N seconds and inserts into
`delivery_items` via the Humanbased API.

---

## Checklist (Copy for Each Investigation)

```
[ ] Step 0: Target defined in one sentence
[ ] Step 1: All org repos listed and scanned
[ ] Step 2: Entry point files found, domain model understood
[ ] Step 3: Config/settings file read, connection strings extracted (masked)
[ ] Step 4: Relevant DB tables identified, schema reviewed
[ ] Step 5: End-to-end data flow drawn, gaps marked
[ ] Step 6: Findings table filled in, security issues logged
[ ] Step 7: Integration approach decided and added to prd.md
```

---

## Security Audit Outputs

After any investigation, produce a security findings list:

```markdown
## Security Findings — <service name> — <date>

### CRIT: Plaintext credentials in source control
- File: setting.py:12
- Action: Rotate credentials, move to secrets manager, add to .gitignore

### HIGH: DB user privilege scope unknown
- Command to audit: SHOW GRANTS FOR 'codatta'@'%';
- Action: Apply least-privilege — grant only SELECT on required tables

### MED: TLS enforcement not confirmed for RDS connection
- Action: Verify `ssl_ca` param in DB URL or enforce TLS in RDS parameter group
```
