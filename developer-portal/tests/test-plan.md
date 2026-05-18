# Test Plan — Codatta Developer Portal

> This document records test logic and cases in a **tech-stack agnostic** format.
> If the tech stack changes, these cases should be re-implemented in the new stack.
> All tests contribute to the CI/CD pipeline when the product graduates.

---

## Test Structure

```
tests/
├── test-plan.md          # This file — logic & cases (portable)
├── unit/                 # Unit tests (fast, isolated, mocked deps)
│   ├── api/              # Python API unit tests (pytest)
│   └── webapp/           # Frontend unit tests (bun test)
└── integration/          # Integration tests (real DB, real services)
    ├── api/              # API integration tests (real Supabase)
    └── e2e/              # End-to-end browser tests (future)
```

Current implementations:
- **API unit tests**: `packages/api/tests/` (pytest, mocked Supabase)
- **Frontend unit tests**: `packages/webapp/src/__tests__/` (bun test, no browser)

---

## 1. Auth

### Unit Tests

| ID | Case | Input | Expected | Status |
|---|---|---|---|---|
| AUTH-U01 | Signup success | valid email + password + name | 200, user object returned, `users` record created | ✅ |
| AUTH-U02 | Signup invalid email | "not-an-email" | 422 validation error | ✅ |
| AUTH-U03 | Signup missing fields | email only, no password/name | 422 validation error | ✅ |
| AUTH-U04 | Signup failure (null user) | Supabase returns null user | 400 "Sign up failed" | ✅ |
| AUTH-U05 | Signup duplicate email | Supabase throws "already registered" | 400 with error message | ✅ |
| AUTH-U06 | Signin success | valid email + password | 200, user + session (access_token, refresh_token) | ✅ |
| AUTH-U07 | Signin invalid creds | wrong password | 401 "Invalid login credentials" | ✅ |
| AUTH-U08 | Signin invalid email format | "bad-email" | 422 validation error | ✅ |

### Middleware Tests

| ID | Case | Input | Expected | Status |
|---|---|---|---|---|
| AUTH-M01 | GET /me with valid token | Bearer valid-token | 200, user object with profile | ✅ |
| AUTH-M02 | GET /me missing auth header | no Authorization header | 401 "Missing or invalid Authorization header" | ✅ |
| AUTH-M03 | GET /me invalid token | Bearer bad-token | 401 | ✅ |
| AUTH-M04 | GET /me malformed bearer | "Basic abc" | 401 | ✅ |

### Frontend Tests

| ID | Case | Logic | Status |
|---|---|---|---|
| AUTH-F01 | Route / maps to landing | getRoute("/") === "landing" | ✅ |
| AUTH-F02 | Route /auth/signin maps to signin | getRoute("/auth/signin") === "signin" | ✅ |
| AUTH-F03 | Route /auth/signup maps to signup | getRoute("/auth/signup") === "signup" | ✅ |
| AUTH-F04 | Route /dashboard maps to dashboard | getRoute("/dashboard") === "dashboard" | ✅ |
| AUTH-F05 | API client adds auth header when token exists | fetch called with Authorization: Bearer token | ✅ |
| AUTH-F06 | API client omits auth header when no token | fetch called without Authorization | ✅ |
| AUTH-F07 | API client throws on non-ok response | 401 response → Error with detail message | ✅ |

### Integration Tests (TODO)

| ID | Case | Expected |
|---|---|---|
| AUTH-I01 | Full signup → signin → /me flow | User created in auth + public.users, session valid |
| AUTH-I02 | Signup with existing email | Error returned, no duplicate |
| AUTH-I03 | Session persists across page reload | onAuthStateChange restores session |
| AUTH-I04 | Sign out clears session | localStorage cleared, redirects to / |

---

## 2. Onboarding

### Unit Tests

| ID | Case | Input | Expected | Status |
|---|---|---|---|---|
| ONB-U01 | Create org success | name + slug | 200, org created, owner membership + account created | ✅ |
| ONB-U02 | Create org missing name | name="" | 400 "Organization name is required" | ✅ |
| ONB-U03 | Create org missing slug | slug="  " | 400 "Organization slug is required" | ✅ |
| ONB-U04 | Create org duplicate slug | existing slug | 409 "Slug already taken" | ✅ |
| ONB-U05 | Create org unauthenticated | no token | 401 | ✅ |
| ONB-U06 | Create org with optional fields | name + slug + website + industry | 200, all fields saved | ✅ |
| ONB-U07 | Invite members success | 2 valid invites | 200, 2 results | ✅ |
| ONB-U08 | Invite with invalid role skipped | role="owner" | Only valid roles processed | ✅ |
| ONB-U09 | Invite empty list | [] | 200, empty results | ✅ |
| ONB-U10 | Generate first API key | org_id | 200, raw_key starts with hb_live_sk_ | ✅ |
| ONB-U11 | API key unauthenticated | no token | 401 | ✅ |

### Frontend Tests

| ID | Case | Logic | Status |
|---|---|---|---|
| ONB-F01 | Route /onboarding maps correctly | getRoute("/onboarding") === "onboarding" | ✅ |
| ONB-F02 | slugify "Acme AI Labs" | "acme-ai-labs" | ✅ |
| ONB-F03 | slugify special characters | "Hello World! @#$%" → "hello-world" | ✅ |
| ONB-F04 | slugify empty string | "" → "" | ✅ |
| ONB-F05 | slugify strips hyphens | "--hello--" → "hello" | ✅ |
| ONB-F06 | slugify numbers | "Web3 Company 123" → "web3-company-123" | ✅ |
| ONB-F07 | API key prefix format | starts with "hb_live_" | ✅ |

### Integration Tests (TODO)

| ID | Case | Expected |
|---|---|---|
| ONB-I01 | Full onboarding flow | Org + membership + account + API key created in DB |
| ONB-I02 | Org slug uniqueness | Second create with same slug fails |
| ONB-I03 | Onboarding sets onboarding_completed | Flag set to true after step 3 |

---

## 3. API Keys

### Unit Tests

| ID | Case | Input | Expected | Status |
|---|---|---|---|---|
| KEY-U01 | Create key with expiry | name + 90 days | 200, raw_key returned, starts with hb_live_sk_ | ✅ |
| KEY-U02 | Create key no expiry | expires_in_days=null | 200, expires_at is null | ✅ |
| KEY-U03 | List keys | org_id | 200, array of keys | ✅ |
| KEY-U04 | Revoke key | key_id | 200, status="revoked" | ✅ |
| KEY-U05 | Revoke nonexistent key | fake_id | 404 | ✅ |

### Frontend Tests

| ID | Case | Logic | Status |
|---|---|---|---|
| KEY-F01 | daysUntil null returns "Never" | daysUntil(null) === "Never" | ✅ |
| KEY-F02 | daysUntil future date | "30d left" format | ✅ |
| KEY-F03 | daysUntil past date | "Expired" | ✅ |
| KEY-F04 | maskKey hides when not revealed | contains bullet chars | ✅ |
| KEY-F05 | maskKey shows when revealed | full prefix | ✅ |
| KEY-F06 | All statuses have badges | active, expired, revoked mapped | ✅ |

---

## 4. Members

### Unit Tests

| ID | Case | Input | Expected | Status |
|---|---|---|---|---|
| MEM-U01 | List members | org_id | 200, array with user joins | ✅ |
| MEM-U02 | Invite existing user | valid email + role | 200, membership created, email_sent=true | ✅ |
| MEM-U03 | Invite invalid role | role="superadmin" | 400 | ✅ |
| MEM-U04 | Invite unknown user (pending) | non-existing email | 200, status=pending_signup, email_sent=true | ✅ |
| MEM-U05 | Update role | member_id + role | 200, role updated | ✅ |
| MEM-U06 | Remove member | member_id | 200, ok=true | ✅ |

### Integration Tests (TODO)

| ID | Case | Expected |
|---|---|---|
| MEM-I01 | Invite sends actual email | Resend API called with correct template |
| MEM-I02 | Invite existing user auto-joins | Membership active immediately |
| MEM-I03 | Cannot change owner role | 403 or ignored |
| MEM-I04 | Cannot remove last owner | Error returned |

---

## 5. Subscriptions

### Unit Tests

| ID | Case | Input | Expected | Status |
|---|---|---|---|---|
| SUB-U01 | Create subscription | vertical_id + topic_ids + mode | 200, status=active | ✅ |
| SUB-U02 | List subscriptions | org_id | 200, array with vertical joins | ✅ |
| SUB-U03 | Update filters | sub_id + auto_accept | 200, updated | ✅ |
| SUB-U04 | Cancel subscription | sub_id | 200, status=cancelled | ✅ |
| SUB-U05 | Cancel nonexistent | fake_id | 404 | ✅ |

### Frontend Tests

| ID | Case | Logic | Status |
|---|---|---|---|
| SUB-F01 | All verticals have topics | each vertical has topics.length > 0 | ✅ |
| SUB-F02 | Topic toggle add/remove | Set operations work | ✅ |
| SUB-F03 | Mode options are pull/push | exactly 2 options | ✅ |
| SUB-F04 | All statuses have badges | active, paused, cancelled | ✅ |

---

## 6. Billing

### Unit Tests

| ID | Case | Input | Expected | Status |
|---|---|---|---|---|
| BIL-U01 | Get balance | org_id | 200, balance_available_usd, balance_frozen_usd | ✅ |
| BIL-U02 | Balance not found | fake org_id | 404 | ✅ |
| BIL-U03 | Create Stripe checkout | amount_cents | 200, checkout_url contains stripe.com | ✅ |
| BIL-U04 | List transactions | org_id | 200, array via account_id join | ✅ |
| BIL-U05 | Webhook invalid signature | bad sig header | 400 | ✅ |

### Frontend Tests

| ID | Case | Logic | Status |
|---|---|---|---|
| BIL-F01 | formatMoney positive | 8420 → "$8,420.00" | ✅ |
| BIL-F02 | formatMoney zero | 0 → "$0.00" | ✅ |
| BIL-F03 | formatMoney decimal | 17.35 → "$17.35" | ✅ |
| BIL-F04 | formatMoney negative | -15 → "-$15.00" | ✅ |
| BIL-F05 | Quick amounts valid | all > 0 | ✅ |
| BIL-F06 | Transaction types mapped | 4 types | ✅ |

---

## 7. Orgs / Settings

### Unit Tests

| ID | Case | Input | Expected | Status |
|---|---|---|---|---|
| ORG-U01 | Get org | org_id | 200, org data | ✅ |
| ORG-U02 | Get org not found | fake_id | 404 | ✅ |
| ORG-U03 | Update org | org_id + fields | 200, updated | ✅ |

### Integration Tests (TODO)

| ID | Case | Expected |
|---|---|---|
| ORG-I01 | Domain allowlist CRUD | Add/remove domains persisted |
| ORG-I02 | Auto-join on signup with matching domain | User auto-added to org |
| ORG-I03 | Non-matching signup email → backup email | Backup email auto-set |
| ORG-I04 | Slug uniqueness on update | Cannot update to existing slug |
| ORG-I05 | Delete org cascades | Keys, memberships, subscriptions, account deleted |

---

## 8. Dashboard — Waffle Chart

### Frontend Tests

| ID | Case | Logic | Status |
|---|---|---|---|
| WFL-F01 | timeAgo seconds | 5s ago → "5s ago" | ✅ |
| WFL-F02 | timeAgo minutes | 5m ago → "5m ago" | ✅ |
| WFL-F03 | timeAgo hours | 2h ago → "2h ago" | ✅ |
| WFL-F04 | Chart data aggregation same bucket | count increments | ✅ |
| WFL-F05 | Chart data aggregation new bucket | new entry appended | ✅ |
| WFL-F06 | Stream capped at max | 200+ items → 200 | ✅ |
| WFL-F07 | Adopt changes status | "pending" → "adopted" | ✅ |
| WFL-F08 | Dispute changes status | "pending" → "disputed" | ✅ |
| WFL-F09 | Status change on unknown ID | no change | ✅ |
| WFL-F10 | All data types have colors | 5 types mapped | ✅ |

### Visual Logic (manual verification)

| ID | Case | Expected |
|---|---|---|
| WFL-V01 | Block fill reflects vertical | 3 shades: #1B1034, #5C5470, #B0A8C0 |
| WFL-V02 | Status never changes fill | Adopted/disputed blocks keep vertical color |
| WFL-V03 | Adopted = green border | 2px #22C55E stroke on block |
| WFL-V04 | Disputed = red border | 2px #EF4444 stroke on block |
| WFL-V05 | Time flows right-to-left | Newest column at right edge |
| WFL-V06 | 5-min tick marks | Paired vertical sticks at boundaries |
| WFL-V07 | Legend at bottom-right | Verticals + status indicators |

---

## 9. Email & Domain Logic (TODO)

### Unit Tests (planned)

| ID | Case | Expected |
|---|---|---|
| DOM-U01 | Add domain to allowlist | Domain persisted |
| DOM-U02 | Remove domain from allowlist | Domain removed |
| DOM-U03 | Signup email matches allowlist | Auto-join org, org email set |
| DOM-U04 | Signup email doesn't match | Prompt to configure, set as backup |
| DOM-U05 | Org email must match allowlist | Reject if domain not in list |
| DOM-U06 | Backup email exempt from allowlist | Any domain accepted |

### Integration Tests (planned)

| ID | Case | Expected |
|---|---|---|
| DOM-I01 | Signup + auto-join full flow | User registered → domain matched → membership created |
| DOM-I02 | Non-matching email → backup email set | backup_email populated in users table |
| DOM-I03 | Admin adds domain → existing users auto-join | Batch membership creation |

---

## 10. Health

### Unit Tests

| ID | Case | Expected | Status |
|---|---|---|---|
| HLT-U01 | GET /healthz | 200, {"status": "ok"} | ✅ |

---

## 8. Data Review UX (Phase 3A)

### 8.1 Auto-adopt after 48 h

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| ARV-U01 | Item older than 48h is auto-adopted | `delivery_items` row: `status='pending'`, `created_at = NOW() - INTERVAL '49 hours'` | pg_cron job fires | `status='adopted'`, `reviewed_at` is set | integration |
| ARV-U02 | Item younger than 48h is not touched | `delivery_items` row: `status='pending'`, `created_at = NOW() - INTERVAL '47 hours'` | pg_cron job fires | row unchanged | integration |
| ARV-U03 | Already-disputed item is not auto-adopted | `delivery_items` row: `status='disputed'`, `created_at = NOW() - INTERVAL '72 hours'` | pg_cron job fires | row unchanged | integration |
| ARV-U04 | Adopt endpoint sets item status | valid item_id, API key auth | `POST /v1/data/items/{id}/adopt` | `delivery_items.status = 'adopted'`, `reviewed_at` set | unit |
| ARV-U05 | Dispute endpoint sets item status | valid item_id, API key auth | `POST /v1/data/items/{id}/dispute` | `delivery_items.status = 'disputed'`, `reviewed_at` set | unit |

### 8.2 Confirm modal

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| MOD-U01 | Adopt button opens confirm modal | item in pending state | user clicks Adopt | ConfirmModal renders with "Adopt this item?" title and charge amount | unit |
| MOD-U02 | Dispute button opens confirm modal | item in pending state | user clicks Dispute | ConfirmModal renders with "Dispute this item?" and "No charge" copy | unit |
| MOD-U03 | Cancel closes modal, item unchanged | modal open | user clicks Cancel | modal closes, item remains pending in LiveStream | unit |
| MOD-U04 | Backdrop click cancels modal | modal open | user clicks outside modal | modal closes | unit |
| MOD-U05 | Confirm adopt removes item from stream | modal open for adopt | user clicks Confirm | item no longer appears in LiveStream after 300ms | unit |
| MOD-U06 | Confirm dispute moves item to DisputePool | modal open for dispute | user clicks Confirm | item appears at top of DisputePool after animation completes | unit |

### 8.3 Dispute Pool section

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| DSP-U01 | DisputePool hidden when no disputes | zero disputed items | render | DisputePool returns null (no DOM output) | unit |
| DSP-U02 | DisputePool visible when items exist | at least 1 disputed item | render | DisputePool renders with red border + "Dispute Pool" header | unit |
| DSP-U03 | Items sorted newest-first | two disputes at t=1 and t=2 | render | t=2 item appears above t=1 item | unit |
| DSP-U04 | DisputePool row has no action buttons | disputed item | render | no "Adopt" or "Dispute" buttons present; "disputed" badge shown | unit |
| DSP-U05 | Expandable rows work in DisputePool | item in DisputePool | click row | payload JSON expands below row | unit |

### 8.4 Row transition animation

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| ANI-U01 | Fading row gets opacity:0 | transitioningId set to item.id | render | `<tr>` has `opacity: 0` via inline style | unit |
| ANI-U02 | Non-fading rows unaffected | transitioningId set to different id | render | other rows have `opacity: 1` | unit |
| ANI-U03 | Newest dispute row gets slide-in class | item just moved to DisputePool | render | first DisputePool row has `row-slide-in` CSS class | unit |
| ANI-U04 | Slide-in class removed after 400ms | newestDisputeId set | after 400ms timeout | newestDisputeId is null, class no longer applied | unit |

---

## 9. Social OAuth Sign-In (GitHub + HuggingFace)

### 9.1 GitHub OAuth (Supabase native)

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| OAUTH-GH01 | Click GitHub button starts OAuth | user on /auth/signin | clicks "Continue with GitHub" | supabase.auth.signInWithOAuth called with provider='github' and redirectTo=`{origin}/auth/callback` | unit |
| OAUTH-GH02 | New GitHub user lands on onboarding | fresh user returns from GitHub consent | sync-profile creates users row, no org match | navigates to /onboarding | e2e |
| OAUTH-GH03 | Returning GitHub user lands on dashboard | user with existing org membership returns | sync-profile finds org_id | navigates to /dashboard | e2e |
| OAUTH-GH04 | ~~Removed~~ — domain allowlist feature removed in PR #77 | — | — | — | — |
| OAUTH-GH05 | Provider error surfaces | GitHub OAuth returns error | signInWithOAuth rejects | error message shown below button, user stays on signin page | unit |

### 9.2 HuggingFace OAuth (custom backend flow)

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| OAUTH-HF01 | Click HF button navigates to start endpoint | user on /auth/signin | clicks "Continue with HuggingFace" | browser navigates to `{API_URL}/v1/auth/huggingface/start?return_to=/auth/callback` | unit |
| OAUTH-HF02 | /start builds authorize URL with PKCE | GET /v1/auth/huggingface/start | handler executes | 302 to huggingface.co/oauth/authorize with client_id, code_challenge, S256, state, scope=openid profile email | integration |
| OAUTH-HF03 | /start sets signed state cookie | GET /v1/auth/huggingface/start | handler executes | `hf_oauth_state` cookie set, httponly, lax, scoped to /v1/auth/huggingface | integration |
| OAUTH-HF04 | /start returns 503 when not configured | hf_client_id empty | GET /start | 503 response | integration |
| OAUTH-HF05 | /callback creates new Supabase user | valid code+state, no existing user by email | token exchange returns valid id_token | supabase.auth.admin.create_user called with email_confirm=True and provider='huggingface' metadata, then magiclink generated, browser 302'd to action_link | integration |
| OAUTH-HF06 | /callback reuses existing Supabase user (email match) | user already signed up via password with same email | token exchange succeeds | create_user NOT called, generate_link called, browser 302'd to action_link | integration |
| OAUTH-HF07 | /callback rejects tampered state | state signature invalid | GET /callback | 400 response | integration |
| OAUTH-HF08 | /callback rejects state cookie mismatch | state param and cookie differ | GET /callback | 400 response | integration |
| OAUTH-HF09 | /callback rejects missing code | only state provided | GET /callback | 400 response | integration |
| OAUTH-HF10 | /callback handles token exchange failure | HF token endpoint returns 400 | POST to token endpoint | 502 returned from our API | integration |
| OAUTH-HF11 | /callback rejects expired id_token | id_token.exp in past | decode runs | ValueError, 400 response | unit |
| OAUTH-HF12 | /callback rejects wrong issuer | id_token.iss != huggingface.co | decode runs | ValueError, 400 response | unit |
| OAUTH-HF13 | /callback rejects wrong audience | id_token.aud != our client_id | decode runs | ValueError, 400 response | unit |
| OAUTH-HF14 | /callback rejects unverified email | id_token.email_verified=false | decode runs | ValueError, 400 response | unit |
| OAUTH-HF15 | State expiry enforced | state older than 10 min | verify_state called | ValueError raised | unit |
| OAUTH-HF16 | return_to restricted to relative paths | start called with return_to=https://evil.com | handler executes | safe_return_to defaults to /auth/callback | unit |

### 9.3 Account linking by email

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| OAUTH-LINK01 | Password user signs in with GitHub (same email) | user alice@acme.com exists via password signup | GitHub OAuth returns alice@acme.com | Supabase links identity to existing user (setting: link identities with same email) — sync-profile returns existing users row, lands on dashboard | e2e |
| OAUTH-LINK02 | GitHub user signs in with HuggingFace (same email) | alice@acme.com was created via GitHub OAuth | HF callback looks up by email | existing Supabase user reused, no duplicate users row created | integration |

---

## 11. Codatta Onboarding E2E (Screenshot Capture)

> Automated via `scripts/capture-codatta-onboarding.mjs` (Puppeteer).
> Target: staging.developer.humanbased.ai

### 11.1 Unauthenticated Pages

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| COD-E01 | Landing page renders | browser at staging URL | page loads | "Get Started" button visible, Codatta branding present | e2e |
| COD-E02 | Signup page renders | navigate to /auth/signup | page loads | email input + "Send verification code" button visible | e2e |
| COD-E03 | Signin page renders | navigate to /auth/signin | page loads | email + password inputs visible, OAuth buttons present | e2e |

### 11.2 Onboarding Wizard (fresh user)

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| COD-E04 | Fresh user redirects to onboarding | new user session injected | page reloads | navigates to /onboarding | e2e |
| COD-E05 | Org setup step renders | on /onboarding step 1 | page loads | org name, slug, industry, size inputs visible | e2e |
| COD-E06 | Org creation advances to invite step | valid org name + slug entered | click Continue | invite team step renders with email input + role selector | e2e |
| COD-E07 | Invite step can be skipped | on invite team step | click "Do this later" | advances to API key step | e2e |
| COD-E08 | API key displayed on final step | onboarding step 3 | page renders | API key starting with hb_live_sk_ visible, copy button present | e2e |
| COD-E09 | Dashboard accessible after onboarding | click "Go to Dashboard" | navigation completes | /dashboard loads with sidebar nav | e2e |

### 11.3 Subscription Flow

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| COD-E10 | Subscriptions page lists data sources | navigate to /dashboard/subscriptions | page loads | at least one data source card visible with "Explore" button | e2e |
| COD-E11 | Production mode toggle works | on subscriptions page | click Production toggle | data sources refresh, "Production" indicator active | e2e |
| COD-E12 | Explore shows data table | click "Explore" on a data source | table loads | data rows visible, "Subscribe to All" button present | e2e |
| COD-E13 | Subscribe modal shows terms | click "Subscribe to All" | modal opens | data usage agreement + checkbox + Subscribe button visible | e2e |
| COD-E14 | Subscription activates | accept terms + click Subscribe | modal closes | subscription card shows "active" status + "Pull Data" button | e2e |

### 11.4 Pull Data

| ID | Case | Given | When | Then | Type |
|----|------|-------|------|------|------|
| COD-E15 | Pull Data panel shows curl command | click "Pull Data" on active subscription | panel opens | curl command with subscription_id + Authorization header visible | e2e |
| COD-E16 | Submissions table renders | Pull Data panel open | panel loads | data rows with DATE, GRADE, PRICE, SOURCE columns visible | e2e |

---

## Test Totals

| Layer | Current | Status |
|---|---|---|
| API unit tests (pytest) | 47 | All passing |
| Frontend unit tests (bun) | 52 | All passing |
| Integration tests | 0 | Planned |
| Semantic test cases (test-plan.md) | 135 | Specified |
| E2E screenshot cases (Codatta onboarding) | 16 | Specified |
| **Total implemented** | **99** | **99 passing** |
