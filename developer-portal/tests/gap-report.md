# Test & Functionality Gap Report

> Generated: 2025-03-25
> Total tests: 99 (47 API + 52 Frontend) — all passing

---

## 1. Functionality Gaps (Built but incomplete)

### HIGH PRIORITY

| Gap | Description | Impact |
|---|---|---|
| **Hardcoded ORG_ID** | All frontend components use `ORG_ID = "demo-org"` | No real org context — nothing works with real data |
| **No auth guard on API routes** | API routes (keys, members, billing, subscriptions) don't verify org membership | Anyone with a token can access any org's data |
| **Org email detection missing** | Signup doesn't check domain allowlist or auto-set org/backup email | Email logic from prd.md not implemented |
| **Domain allowlist not persisted** | OrgSettings shows allowlist UI but no API endpoint to save/read | Domains reset on page reload |
| **Static asset serving fragile** | Logo served via hardcoded route in server.ts | Adding more assets requires code changes |

### MEDIUM PRIORITY

| Gap | Description | Impact |
|---|---|---|
| **No logo upload** | Onboarding + Settings show upload placeholder but no Supabase Storage integration | Logo feature is visual-only |
| **Settings doesn't fetch real data** | OrgSettings starts with empty state, doesn't call `GET /v1/orgs/{id}` on mount | Settings form is empty on load |
| **Account Settings doesn't save** | `handleSave` uses `setTimeout` stub, not `supabase.auth.updateUser` | Name changes don't persist |
| **Subscriptions use hardcoded verticals** | 6 verticals hardcoded in frontend, not from `GET /v1/verticals` | New verticals require code change |
| **Subscribe button no-op** | Clicking "Subscribe" on vertical cards does nothing | Can't create subscriptions from cards |
| **Members invite for non-existing users** | Returns `pending_signup` status but no mechanism to track or complete | Invited users who sign up later aren't auto-added |

### LOW PRIORITY

| Gap | Description | Impact |
|---|---|---|
| **No pagination** | Transaction history, member list, key list — all unbounded | Performance issue at scale |
| **No error toasts** | API errors silently caught with empty `catch {}` blocks | Users don't know when operations fail |
| **Waffle chart mock data only** | Simulator generates random data, not connected to real Supabase Realtime | Chart shows fake data |
| **No responsive design** | Fixed max-w-6xl layout, no mobile breakpoints | Unusable on mobile |
| **Footer not on auth pages** | SignIn/SignUp don't show the "Codatta PTE LTD" footer | Inconsistent branding |

---

## 2. Test Coverage Gaps

### API — Missing tests

| Area | Missing | Planned IDs |
|---|---|---|
| Auth | Signup creates `users` record | AUTH-I01 |
| Auth | Session persistence flow | AUTH-I03 |
| Onboarding | `onboarding_completed` flag set | ONB-I03 |
| Members | Cannot change owner role | MEM-I03 |
| Members | Cannot remove last owner | MEM-I04 |
| Members | Resend email actually called | MEM-I01 |
| Billing | Stripe webhook updates balance | BIL-I01 |
| Billing | Checkout redirect URL valid | BIL-I02 |
| Orgs | Slug uniqueness on update | ORG-I04 |
| Orgs | Delete cascades correctly | ORG-I05 |
| Verticals | List verticals endpoint | VRT-U01 |
| Verticals | List topics by vertical | VRT-U02 |
| Domain allowlist | CRUD operations | DOM-U01-U06 |

### Frontend — Missing tests

| Area | Missing |
|---|---|
| WaffleChart | Canvas rendering (can't easily unit test) |
| Members | Confirmation dialog flow |
| Settings | Form submission + save |
| Subscriptions | Subscribe button click |
| Dashboard | Avatar dropdown open/close |
| Auth | Redirect guards (authenticated → dashboard, unauthenticated → signin) |
| Onboarding | Step navigation flow |

---

## 3. API Endpoints — Coverage Matrix

| Endpoint | Route | Unit Test | Integration Test |
|---|---|---|---|
| `GET /healthz` | health | ✅ | — |
| `POST /v1/auth/signup` | auth | ✅ | — |
| `POST /v1/auth/signin` | auth | ✅ | — |
| `GET /v1/auth/me` | auth | ✅ | — |
| `POST /v1/onboarding/org` | onboarding | ✅ | — |
| `POST /v1/onboarding/invite` | onboarding | ✅ | — |
| `POST /v1/onboarding/api-key` | onboarding | ✅ | — |
| `POST /v1/orgs` | orgs | — | — |
| `GET /v1/orgs/{id}` | orgs | ✅ | — |
| `PATCH /v1/orgs/{id}` | orgs | ✅ | — |
| `DELETE /v1/orgs/{id}` | orgs | — | — |
| `POST /v1/orgs/{id}/keys` | keys | ✅ | — |
| `GET /v1/orgs/{id}/keys` | keys | ✅ | — |
| `POST /v1/orgs/{id}/keys/{kid}/revoke` | keys | ✅ | — |
| `GET /v1/orgs/{id}/members` | members | ✅ | — |
| `POST /v1/orgs/{id}/members/invite` | members | ✅ | — |
| `PATCH /v1/orgs/{id}/members/{mid}/role` | members | ✅ | — |
| `DELETE /v1/orgs/{id}/members/{mid}` | members | ✅ | — |
| `GET /v1/orgs/{id}/subscriptions` | subscriptions | ✅ | — |
| `POST /v1/orgs/{id}/subscriptions` | subscriptions | ✅ | — |
| `PATCH /v1/orgs/{id}/subscriptions/{sid}` | subscriptions | ✅ | — |
| `POST /v1/orgs/{id}/subscriptions/{sid}/cancel` | subscriptions | ✅ | — |
| `GET /v1/orgs/{id}/billing/balance` | billing | ✅ | — |
| `POST /v1/orgs/{id}/billing/checkout` | billing | ✅ | — |
| `POST /v1/orgs/{id}/billing/webhook` | billing | ✅ | — |
| `GET /v1/orgs/{id}/billing/transactions` | billing | ✅ | — |
| `GET /v1/verticals` | verticals | — | — |
| `GET /v1/verticals/{id}/topics` | verticals | — | — |

**Coverage**: 24/28 endpoints have unit tests (86%). 0 integration tests.

---

## 4. Recommended Next Actions (Priority Order)

1. **Org context from auth** — Replace `ORG_ID = "demo-org"` everywhere. Without this, nothing works with real users.
2. **Auth guards on API** — Add `require_org_member` dependency to all org-scoped routes.
3. **Domain allowlist API** — `GET/PUT /v1/orgs/{id}/allowlist` + email detection on signup.
4. **Account Settings save** — Wire up `supabase.auth.updateUser` + backup email field.
5. **Verticals endpoint tests** — Add unit tests for the 2 missing endpoints.
6. **Subscribe action** — Wire vertical card buttons to `POST /v1/orgs/{id}/subscriptions`.
7. **Error handling** — Replace empty `catch {}` with user-visible error toasts.
8. **Integration tests** — Start with auth flow (signup → signin → /me → org membership).
