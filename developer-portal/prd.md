# PRD — Humanbased Developer Portal

> Product: Humanbased Developer Portal (prev. Codatta)
> Production domains: **developer.humanbased.ai** (portal) · **api.humanbased.ai** (API) · **docs.humanbased.ai** (docs)
> **Brand name:** Currently **Codatta** — all user-facing copy, emails, and UI use "Codatta". The product domain `humanbased.ai` is a future brand migration target; do not surface "Humanbased" in any UI or email until the rebrand is approved.
> Repo: consume_api (monorepo: webapp + api + cli + mcp + docs)
> Product context: **[prod_overview.md](./prod_overview.md)** — business model, platform architecture, roadmap
> Campaign launch roadmap: **[campaign-launch-roadmap.md](./campaign-launch-roadmap.md)** — phased plan for the demand-push campaign flow (robotics, video annotation, lineage → on-chain)
> Release process: **[release-workflow.md](./release-workflow.md)** — versioning, branching, changelog

---

## Vision

The demand-side portal for the Humanbased two-sided marketplace. Developers and organizations use this portal to launch human-executed tasks, manage data assets and licenses, control data access, and manage payments — all via a fast, minimal web UI, REST API, CLI, or MCP server.

---

## Tech Stack

- **Frontend**: Bun.serve() with HTML imports, React, Tailwind CSS
- **Backend API**: Python (FastAPI + uvicorn), managed with `uv`
- **Database**: Supabase (existing project `uxafdddzhgdhsabkwmgw` — Postgres + Auth + Storage + Realtime)
- **Auth**: Supabase Auth with org-level email domain allowlist
- **Email**: Resend for transactional emails (invites, verification)
- **Live data**: Supabase Realtime (frontend subscribes directly via supabase-js)
- **Payments**: Stripe Checkout in test mode for V1
- **Architecture**: Separate origins — frontend and API on different domains/ports, CORS enabled
- **Deployment**: API → Google Cloud Run (`api.humanbased.ai`), Frontend → Vercel (`developer.humanbased.ai`), Docs → Vercel (`docs.humanbased.ai`). All production deploys from `main` only.
- **Design**: Quantus Palette 2025 — Blue Chalk bg (#E8E0F0), Haiti text (#1B1034), Electric Violet accent (#834DFB), DM Sans font

---

## Repo Structure (Monorepo)

```
consume_api/
├── packages/
│   ├── webapp/        # Frontend (Bun + React + Tailwind)
│   ├── api/           # Backend API (Python — FastAPI + uv)
│   ├── cli/           # CLI tool (@humanbased/cli)
│   ├── mcp/           # MCP server
│   └── docs/          # Documentation site
├── shared/            # Shared TypeScript types (frontend only)
├── tests/
│   ├── test-plan.md   # Test logic & cases (tech-stack agnostic)
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── prd.md
├── CLAUDE.md
└── package.json
```

---

## V1 Scope

### Auth
- **Sign Up**: Email + password registration via Supabase Auth
- **Sign In**: Email + password login
- On signup, a `users` record is created in public schema linked via `auth_id`

### Email & Domain Logic

**Domain Allowlist (Organization Settings)**
- Org admins manage a list of allowed email domains (e.g., `codatta.com`, `acme.ai`)
- Users signing up with a matching domain auto-join the org
- If no domain allowlist is configured, prompt admin to add one + verify

**Organization Email**
- Auto-detected from the user's signup email if it matches a domain in the allowlist
- If signup email doesn't match any allowlist domain → org email must be set manually

**Backup Email (Account Settings)**
- Lives in Account Settings (per-user, not per-org)
- If the user's original signup email does NOT match the org's domain allowlist, it is automatically set as the backup email (optional, user can change)
- Backup email is not subject to domain allowlist constraints (can be @gmail, etc.)
- Used for account recovery and notifications when org email is unavailable

**Organization Settings — Slug**
- Production slug format: `humanbased.ai/{org-slug}`
- Slug is unique, lowercase, alphanumeric + hyphens

### Onboarding (post-signup)
1. **Organization Details** — name, slug (humanbased.ai/slug), logo upload, industry, size, country
2. **Invite Members** — email + role (Owner/Admin/Member), confirmation dialog before sending, actual email via Resend, skip option
3. **API Key** — auto-generate first key, show once, copy button, quick-start snippet
4. Mark `onboarding_completed = true` on org after step 3

### Dashboard — Overview
- Stat cards: Balance, Active API Keys, Active Subscriptions
- **Waffle chart** — block-based data arrival visualization:
  - Each block = 1 data unit, filled with vertical color (3-shade black gradient)
  - Status shown by outline only: green border = adopted, red border = disputed
  - Time flows right-to-left (newest on right)
  - 5-min interval tick marks (paired vertical sticks)
  - Legend at bottom-right, description at bottom-left
  - Organization-wide scope (solo dev = independent org)
- **Live data stream table**:
  - Expandable rows showing raw payload
  - Adopt / Dispute actions per row (updates waffle chart in real-time)
  - Auto-scroll with pause-on-hover

### API Key Management
- List keys with name, masked key, status, expiration, last used
- Create: name + expiration presets (7d/30d/90d/1y/never)
- Actions: reveal, copy, revoke (with confirmation)
- New key banner shown once after creation

### Members
- Invite by email + role, with confirmation dialog ("Send invitation?")
- Actual email sent via Resend
- If user exists → add membership immediately + email
- If user doesn't exist → email invite with pending_signup status
- Member list: name, email, role (dropdown for non-owner), permissions, join date
- Actions: change role, remove (with confirmation)
- Roles: Owner (immutable), Admin, Member

### Subscriptions
- Browse available data verticals (hardcoded cards for V1, live data in V2)
- Each vertical card shows: icon, name, description, topic count, base price
- Subscribe button per card
- Active subscriptions: left accent border, pull data / edit / cancel actions

### Billing / Balance

**Balance model:**
- **Available** — funds ready to pay for incoming data
- **Frozen** — reserved for received-but-not-yet-settled data items
- **Total** = Available + Frozen (money still owned by the org)
- **Spent** — cumulative amount paid to Codatta/Humanbased for adopted data (not displayed as a balance card, tracked via transactions)

**Data charge lifecycle:**

| Event | Available | Frozen | Spent | Transaction type |
|-------|-----------|--------|-------|-----------------|
| 1. **Data received** | −price | +price | — | `freeze` |
| 2a. **Data adopted** (manual or auto) | — | −price | +price | `settle` |
| 2b. **Dispute confirmed valid** | +price | −price | — | `refund` |
| 2c. **Dispute rejected** (invalid) | — | −price | +price | `settle` |

**Rules:**
- On receive: balance is frozen immediately at `unit_price_usd`. If available balance < price, item is still delivered but flagged as `underfunded`.
- **Auto-adopt**: items in `pending` status are auto-adopted after a configurable period. Default 48 hours. Configurable per organization and per vertical (annotation type). The more specific setting wins (vertical > org > global default).
- **Auto-dispute-valid**: disputed items are auto-resolved as valid (refund) after a configurable period if no admin action. Default: no auto-resolve (admin must act). Configurable per org.
- Disputed data that is confirmed valid: org loses access to the data, must not retain copies. Violation is subject to legal action per ToS.
- Disputed data that is rejected: treated as adopted, org is charged.

**UI:**
- Balance cards: Available, Frozen, Total
- Add funds: quick amount chips ($100/$500/$1K/$5K) + Stripe Checkout
- Transaction history table with type badges (topup, freeze, settle, refund)
- Spent total shown in transaction summary

### Account Settings (avatar dropdown → Account Settings)
- Edit full name
- Email (read-only — is the auth email)
- Backup email (editable, not subject to domain allowlist)

### Organization Settings (avatar dropdown → Organization Settings, admin only)
- **General**: org name, slug (humanbased.ai/slug), org email, backup email
- **Domain Allowlist**: add/remove domains, auto-join logic
  - Org email must match an allowed domain
  - Backup email is exempt
- **Data & Billing Configurables** (editable by org admin, subject to approval):
  - Auto-adopt period (hours) — default 48h. How long before pending items are auto-adopted.
  - Auto-dispute-valid period (hours) — default NULL (manual). How long before disputed items auto-resolve as valid (refund).
  - Per-vertical overrides — table of vertical-specific auto-adopt hours (overrides org default).
  - **Save & approval flow:**
    - Save button appears only when values differ from current effective settings.
    - On save: creates a `setting_change_request` (pending). Email sent to the org's account manager (Codatta/Humanbased associate) for review.
    - Pending changes are displayed with a "Pending approval" badge and do NOT take effect until approved.
    - Account manager may approve, reject, or adjust values (may trigger ToS/agreement amendment).
    - Once approved, changes take effect immediately. Rejected changes show reason.
    - If org has no assigned account manager, changes queue for any superadmin.
- **Danger Zone**: delete org with type-to-confirm

---

## Build Queue

### 🐛 Bug Fixes — Reported 2026-03-31

#### ~~Fix A: Domain Allowlist Auto-Join on Signup~~ ✅ RESOLVED

- **Status:** Already fixed in code. Backend `_auto_join_pending_invitations()` (`auth.py:93-120`) queries `organizations.allowed_domains` and auto-joins. Frontend `AuthCallback.tsx:79-88` checks `org_id`/`auto_joined`, shows welcome modal, navigates to dashboard.

#### Fix B: Logo Upload — Backend Drops `logo_url` During Onboarding ✅ FIXED (2026-04-01)

- **Status:** Frontend upload UI was already implemented. Backend `CreateOrgRequest` was missing `logo_url` field — added `logo_url: str | None = None` to the model in `onboarding.py`.

### 🐛 Bug Fixes — Found 2026-04-01 (code review: signup, org settings, backup email)

#### Fix D: Onboarding Slug Prefix Shows Wrong Domain ✅ FIXED (2026-04-01)

- **Symptom:** `StepOrgDetails.tsx:94` displayed `codatta.ai/` instead of `humanbased.ai/`.
- **Fix:** Changed to `humanbased.ai/`. Verified in screenshot `04-onboarding.png`.

#### Fix E: Org Settings PATCH Allows Any Member to Modify ✅ FIXED (2026-04-01)

- **Severity:** Security — privilege escalation
- **Symptom:** `PATCH /v1/orgs/{org_id}` used `require_org_member` — any member could modify org name, slug, domains, billing email.
- **Fix:** Changed to `require_org_admin` in `orgs.py:52`.

#### Fix F: Cannot Clear Backup Email Once Set ✅ FIXED (2026-04-01)

- **Symptom:** Clearing backup email in Account Settings did not persist — field reappeared on reload.
- **Fix (frontend):** `AccountSettings.tsx` — send `backup_email: null` instead of `undefined` for empty value.
- **Fix (backend):** `auth.py` — use `model_fields_set` to detect explicit `null` and set DB column to `None`.

#### Fix G: Screenshots Mislabeled in Docs ✅ FIXED (2026-04-01)

- **Fix:** Re-captured all screenshots via Puppeteer script (`scripts/capture-screenshots.mjs`). Added new screenshots: `09-org-settings.png`, `10-account-settings.png`, `11-team-members.png`. Fixed `04-onboarding.png` (was showing sign-in page, now shows onboarding flow).

---

### 🔜 Next Up

- [ ] **Skippable Org Creation + Real-Time Availability Check (IN-40)** — Make team creation optional during onboarding; add debounced name+slug availability checks as user types
  - **User:** New developer who just signed up — may not have an org name ready, or is solo; forced org creation is onboarding friction
  - **Acceptance Criteria:**
    - Step 1 of onboarding ("Organization") shows a "Skip for now" link below the Continue button
    - Clicking Skip calls `POST /v1/onboarding/skip` (records `users.onboarding_skipped_at`), then navigates to `/dashboard`
    - As the user types in the Organization name field: after 400ms debounce, UI calls `GET /v1/onboarding/org/check?name=<value>&slug=<slug>` and shows inline status under each field:
      - `checking` → spinner "Checking..."
      - `available` → "✓ Available" in emerald
      - `name_taken` → "Name already in use" in red (under name field)
      - `slug_taken` → "Slug already taken" in red (under slug field)
    - Continue button is disabled while check is in-flight or name/slug is taken
    - Rapid typing uses AbortController to cancel in-flight requests (race-safe)
    - Fields with length < 2 show no indicator (idle state — avoid checking on every keystroke start)
  - **Solution Design:**
    - **Backend** (`packages/api/app/routes/onboarding.py`):
      - `GET /v1/onboarding/org/check?name=&slug=` — query organizations for case-insensitive name match (`ILIKE`) and exact slug match; return `{"name_available": bool, "slug_available": bool}`
      - `POST /v1/onboarding/skip` — set `users.onboarding_skipped_at = now()` for the current user; return `{"ok": true}`
    - **DB migration** (`add_onboarding_skip_and_org_name_index`):
      - `ALTER TABLE users ADD COLUMN onboarding_skipped_at TIMESTAMPTZ`
      - `CREATE UNIQUE INDEX organizations_name_ci_unique ON organizations (LOWER(name))` (case-insensitive name uniqueness, prevents "Acme" and "acme" coexisting)
    - **Frontend**:
      - `packages/webapp/src/lib/useOrgAvailability.ts` — custom hook wrapping debounce + AbortController + fetch; returns `{ nameStatus, slugStatus }` where each is `"idle"|"checking"|"available"|"taken"`
      - `StepOrgDetails.tsx` — wire hook, render inline status badges under name and slug fields; add Skip button; disable Continue while checking or taken
      - `Onboarding.tsx` — add `onSkipped` prop to `StepOrgDetails`; wire `() => navigate("/dashboard")`
  - **Technical Notes:**
    - Slug auto-fill from name still works (and triggers availability check for both)
    - On skip: no org is created, so `orgId` stays null; user lands on dashboard in "no-org" mode (already handled by Dashboard)
    - The `LOWER(name)` index enforces uniqueness at the DB level; the `GET /check` endpoint reads it via ILIKE for UX feedback before submit
    - The existing slug unique constraint (`organizations_slug_unique`) already covers slug — no new constraint needed for slug, just the endpoint query
  - **Tests Required:**
    - Pure logic: `buildCheckUrl(name, slug)` produces correct query string
    - Hook state machine: idle when inputs < 2 chars; transitions to checking on valid input; resolves to available/taken from mocked fetch
    - Backend: `GET /check` returns `name_available=false` when name exists (case-insensitive); `slug_available=false` when slug taken; both true when neither exists
    - Backend: `POST /skip` sets `onboarding_skipped_at` and returns 200
    - UI: Skip button present in StepOrgDetails; Continue button disabled when `nameStatus === "taken"` or `slugStatus === "taken"`

- [ ] **Password Strength Module — Real-Time Rule Feedback + Match Indicator** — Build a reusable password rules module that validates password requirements live as the user types, and shows whether the confirmation password matches the first one
  - **User:** Any user setting or changing a password — today this is only SignUp step 3, but the module must be drop-in reusable for future flows (password reset, account settings change password)
  - **Problem:** `SignUp.tsx:161-167` only enforces `password !== confirmPassword` and `password.length < 8`, and only at submit time. Users type a full password, click Continue, and then get told it's too weak or doesn't match — bad UX and a floor-level security bar. There is no visual indication of which rules have been satisfied, and no feedback that confirm-password matches until submit.
  - **Acceptance Criteria:**
    - **Reusable module:** A standalone module exports (a) a pure `validatePassword(value)` function that returns a per-rule pass/fail result + overall strength score, (b) a `usePasswordRules(value)` hook wrapping it with memoization, and (c) a `<PasswordRules />` presentational component that renders the rule checklist. All three live under `packages/webapp/src/lib/password/` and have zero dependencies on `SignUp.tsx` so they can be imported by any future screen (password reset, change password, admin create-user).
    - **Rules (v1):**
      - Length: at least 10 characters
      - Contains at least one **uppercase** letter (`A–Z`)
      - Contains at least one **lowercase** letter (`a–z`)
      - Contains at least one **digit** (`0–9`)
      - Contains at least one **special character** from `!@#$%^&*()_+-=[]{};':"\\|,.<>/?` \`~
      - Does not contain whitespace
    - **Real-time feedback:** As the user types into the password field, each rule's status updates **immediately** (no debounce needed — this is a local pure function). Each rule renders as a row with:
      - Idle (empty input) → muted circle + muted text
      - Passing → green checkmark + green text
      - Failing → red x + red text
      - No rule flashes green then red on paste — all rules settle on the first paint after input change
    - **Overall strength meter:** A 4-segment bar above the rules list shows weak → fair → good → strong, colored by how many rules pass: 0–2 red, 3 amber, 4 blue, 5–6 green. Include an accessible `aria-label` describing the current score.
    - **Match indicator:** The confirm-password field shows inline status under the input:
      - Empty → nothing
      - Typing but does not match yet → muted "Passwords do not match" (do NOT show red until the field has lost focus OR length ≥ password length, to avoid flashing red on every keystroke)
      - Matches → green "Passwords match"
    - **Submit gating:** The Continue/Submit button is disabled unless ALL rules pass AND confirm matches. Existing submit-time validation in `handleSetPassword` (`SignUp.tsx:158`) is kept as a defensive server-side-adjacent check.
    - **Show/hide toggle:** Both password fields get an eye icon to toggle `type="password"` ↔ `type="text"` so users can verify what they typed. Independent toggles per field.
    - **Accessibility:**
      - Rule list is a `<ul>` with `aria-live="polite"` so screen readers announce rule changes as the user types
      - Each rule row has `role="listitem"` with an `aria-label` like "Password must contain an uppercase letter — not met" / "met"
      - Strength bar has `role="progressbar"` with `aria-valuemin/max/now`
      - Show/hide toggle is a `<button type="button">` with an `aria-pressed` state
    - **No module changes to unrelated forms:** Scope is limited to password-setting UIs. `SignIn.tsx` (login) does NOT get the rules checklist — login only validates against existing hash.
  - **Solution Design:**
    - **Module layout (`packages/webapp/src/lib/password/`):**
      ```
      packages/webapp/src/lib/password/
        rules.ts              # pure rule definitions + validate() function
        usePasswordRules.ts   # memoized hook wrapping validate()
        PasswordRules.tsx     # checklist UI (reads from hook result via prop)
        StrengthMeter.tsx     # 4-segment bar (reads score via prop)
        PasswordField.tsx     # input + eye toggle + optional rules/meter slots
        index.ts              # barrel (direct imports only — no re-export of deep paths to keep tree-shaking clean)
      ```
    - **`rules.ts`** — pure TS, no React:
      ```ts
      export type RuleId = "length" | "uppercase" | "lowercase" | "digit" | "special" | "no-whitespace";
      export interface Rule {
        id: RuleId;
        label: string;
        test: (value: string) => boolean;
      }
      export const DEFAULT_RULES: Rule[] = [ /* 6 rules */ ];
      export interface PasswordValidation {
        rules: { id: RuleId; label: string; passed: boolean }[];
        passedCount: number;
        totalCount: number;
        score: 0 | 1 | 2 | 3 | 4; // mapped from passedCount
        valid: boolean; // all passed
      }
      export function validatePassword(value: string, rules?: Rule[]): PasswordValidation;
      ```
    - **`usePasswordRules.ts`** — thin memo wrapper:
      ```ts
      export function usePasswordRules(value: string, rules?: Rule[]): PasswordValidation {
        return useMemo(() => validatePassword(value, rules), [value, rules]);
      }
      ```
      - `rules` prop defaults to `DEFAULT_RULES`. Pass a custom array for tests or future stricter policies.
    - **`PasswordRules.tsx`** — presentational:
      ```tsx
      export function PasswordRules({ validation, isDirty }: { validation: PasswordValidation; isDirty: boolean }) { ... }
      ```
      - `isDirty` = false suppresses red — rules show in muted state until the field is touched. This avoids a full-red UI on empty initial render.
    - **`StrengthMeter.tsx`** — 4-segment bar; color from `validation.score`.
    - **`PasswordField.tsx`** — optional convenience component wrapping `<input type="password/text">` + eye toggle button + children slot for rules/meter. `SignUp.tsx` can either use it directly or wire the hook to its existing inputs.
    - **Wire into `SignUp.tsx`:**
      - Import `usePasswordRules` + `PasswordRules` + `StrengthMeter`.
      - Call `const validation = usePasswordRules(password)`.
      - Under the password field, render `<StrengthMeter score={validation.score} />` and `<PasswordRules validation={validation} isDirty={passwordTouched} />`.
      - Under confirm field, render a small `<MatchIndicator password={password} confirm={confirmPassword} focused={...} />` component — co-located in `SignUp.tsx` for now (promote to module if reused later).
      - Change submit button: `disabled={!validation.valid || password !== confirmPassword || loading}`.
      - Add `passwordVisible` / `confirmVisible` state for eye toggles.
      - Remove the now-duplicate `password.length < 8` + `!== confirmPassword` checks at submit — validation state is authoritative; keep them only as a final assertion with a generic error message if somehow bypassed.
    - **Server-side parity:** This is a client-side UX feature. Supabase Auth enforces its own minimum (default 6). Do NOT try to push these rules to the backend in v1 — Supabase manages password hashing and doesn't expose a custom validator hook we control. Document this in the module README: "Client-side only; treat as UX, not as security."
    - **No new dependencies.** Do not pull in `zxcvbn` or similar — it adds ~400KB and we only need rule-based feedback, not entropy estimation. If product later wants entropy scoring, we can add it behind a dynamic import per `bundle-dynamic-imports` best practice.
  - **Technical Notes:**
    - Follow React best practices loaded from `vercel:react-best-practices`: derive `validation` during render via `useMemo` (not `useEffect` — `rerender-derived-state-no-effect`), use primitive deps in memo (`rerender-dependencies`), avoid inline component definitions inside `SignUp.tsx` (`rerender-no-inline-components`).
    - `PasswordRules` and `StrengthMeter` are pure — no state, no effects. They render from props.
    - The module is tree-shakeable: import `{ usePasswordRules, PasswordRules }` directly from `@/lib/password` (barrel) or from the deep paths. Prefer deep paths in call sites to satisfy `bundle-barrel-imports`.
    - `SignUp.tsx:12` has `type Step = "email" | "otp" | "password"` — the module only affects the `"password"` step (lines 339–410).
    - Future reuse plan (not in this ticket, but validating the abstraction):
      - Password reset page (when we add one)
      - Account settings → Change password (when we add it)
      - Admin create-user (internal tool, if ever needed)
    - Keep the "password visible" default = `false`. Show/hide toggle resets to hidden on step change.
    - Do not block on whitespace-in-middle rule — reject only leading/trailing whitespace OR any whitespace? Pick "no whitespace anywhere" for v1 — simplest rule that covers accidental paste with trailing newline. Revisit if users complain.
  - **Tests Required:**
    - **Unit (webapp — pure functions):**
      - `validatePassword("")` → all rules fail, `score: 0`, `valid: false`
      - `validatePassword("Abcdef1!X0")` → all 6 rules pass, `score: 4`, `valid: true`
      - `validatePassword("short1!")` → length fails, others pass; `valid: false`
      - `validatePassword("alllowercase123!")` → uppercase fails
      - `validatePassword("ALLUPPERCASE123!")` → lowercase fails
      - `validatePassword("NoDigits!!abc")` → digit fails
      - `validatePassword("NoSpecial123ABC")` → special fails
      - `validatePassword("Has space123!A")` → whitespace fails
      - Custom rules array: pass a 2-rule subset, assert only those are checked
    - **Unit (webapp — hook):**
      - `usePasswordRules("Abc123!@#")` returns memoized result; re-rendering with same input returns same object reference
    - **Unit (webapp — component):**
      - `PasswordRules` renders 6 rule rows
      - When `isDirty=false` and validation fails, rows render in muted style (no red)
      - When `isDirty=true` and rule fails, row has red styling + `aria-label` containing "not met"
      - Passing rule has green styling + `aria-label` containing "met"
      - `StrengthMeter` with `score=0` renders 0 active segments; `score=4` renders 4 active
    - **Unit (webapp — SignUp integration):**
      - Submit button is disabled when validation fails
      - Submit button enabled when all 6 rules pass AND confirmPassword matches
      - Eye toggle flips input `type` between password/text
      - Match indicator shows green "Passwords match" when both fields equal
    - **Semantic (append to `tests/test-plan.md`):**
      - Given a new user on the SignUp password step, When they type "abc", Then all rules show as muted until the field is blurred or enough characters are entered, Then failing rules turn red in real-time as the user keeps typing.
      - Given all 6 rules are met, When the confirm password matches, Then the Continue button becomes enabled.
      - Given all rules are met but confirm does not match, Then the Continue button stays disabled and an inline "Passwords do not match" hint is visible.
      - Given a user toggles the eye icon, Then the password field becomes readable text and the icon state flips. Toggling the confirm field's eye is independent.

- [x] **Environment-Aware API Keys** — API keys tab respects the environment toggle: sandbox mode always shows sandbox keys, production mode always shows production keys
  - **User:** Any developer using the portal (with or without an org)
  - **Problem:** Users with an org in sandbox mode still saw production API keys. The environment toggle had no effect on the API keys tab for org users.
  - **Solution:** Changed `Dashboard.tsx` condition from `mode === "simulation" && !orgId` to `mode === "simulation"`.

- [x] **Social Sign-In — GitHub + HuggingFace OAuth** — Add one-click sign-in/sign-up with GitHub and HuggingFace alongside existing email+password
  - **User:** Any developer signing up or signing in — especially OSS contributors (GitHub) and ML/data practitioners (HF), our two core audience segments
  - **Why:** Reduces signup friction (no password, no email verification step), and credentialises the portal as the data-side companion to GitHub (code) and HuggingFace (models). Every ICP already has at least one of these accounts.
  - **Acceptance Criteria:**
    - `SignIn.tsx` and `SignUp.tsx` show two new buttons above the email field: "Continue with GitHub" and "Continue with HuggingFace" with provider icons, separated from email form by an "or" divider
    - GitHub button → Supabase native OAuth redirect → back to `/auth/callback` → existing `sync-profile` path (onboarding or dashboard)
    - HuggingFace button → `/v1/auth/huggingface/start` → HF authorize → `/v1/auth/huggingface/callback` → browser receives Supabase session tokens → `/auth/callback` → existing `sync-profile` path
    - First-time OAuth user: Supabase user created, `users` row created via existing `sync-profile`, display name prefilled from provider (GitHub login / HF username), avatar url stored if provided
    - Returning OAuth user: signs in, lands on dashboard (or onboarding if incomplete)
    - **Email collision / account linking:** If OAuth email matches an existing Supabase user (from password signup or other provider), link to the same user rather than create a duplicate. Org auto-join from email-domain allowlist still works identically
    - Error states: provider denial, network failure, state/PKCE mismatch → redirect back to sign-in with readable error toast
    - Works in both staging and production (separate OAuth apps per environment)
  - **Solution Design:**
    - **GitHub (Supabase-native):**
      - Create two GitHub OAuth Apps (staging + prod) with callbacks `https://uxafdddzhgdhsabkwmgw.supabase.co/auth/v1/callback`
      - Enable GitHub provider in Supabase dashboard, paste client_id/secret
      - Frontend: `supabase.auth.signInWithOAuth({ provider: 'github', options: { redirectTo: '${origin}/auth/callback' } })`
    - **HuggingFace (custom OAuth 2.0 + OIDC via backend):**
      - Register HF OAuth app at `huggingface.co/settings/connected-applications` (scope: `openid profile email`), get client_id + client_secret, set redirect URI to API domain `/v1/auth/huggingface/callback`
      - Backend new module `packages/api/app/auth_oauth_hf.py`:
        - `GET /v1/auth/huggingface/start` — builds authorize URL, generates PKCE verifier + state, stores in short-lived signed cookie, 302s to `https://huggingface.co/oauth/authorize`
        - `GET /v1/auth/huggingface/callback?code&state` — validates state, POSTs to `https://huggingface.co/oauth/token` with code+verifier, receives id_token + access_token, verifies id_token (JWKS at `https://huggingface.co/oauth/jwks`), extracts `email`, `preferred_username`, `name`, `picture`
        - User upsert: `supabase.auth.admin.list_users` by email → if exists, generate magiclink via `supabase.auth.admin.generate_link({type: 'magiclink', email})`; if not, `supabase.auth.admin.create_user({email, email_confirm: True, user_metadata: {full_name, avatar_url, hf_username, provider: 'huggingface'}})` then generate_link
        - 302 browser to the magiclink `action_link` → Supabase verifies → redirects to `/auth/callback` → existing flow
      - Env vars (`packages/api/.env`): `HF_CLIENT_ID`, `HF_CLIENT_SECRET`, `HF_REDIRECT_URI`, `HF_OAUTH_STATE_SECRET`
    - **Frontend UI (`SignIn.tsx`, `SignUp.tsx`):** Extract shared `<OAuthButtons />` component rendering both providers. GitHub icon inline SVG, HF icon (the smiley or official logo SVG). Consistent with existing form styling.
    - **account linking on email collision:** `sync-profile` backend already looks up `users` by `auth_id`. Add: if Supabase user is new but email matches an existing `users.email`, relink the row's `auth_id` to the new Supabase user (rare — Supabase itself collides emails by default unless multiple-identities enabled). Preferred: enable "Link identities with same email" in Supabase Auth settings so Supabase handles it natively.
  - **Technical Notes:**
    - HF OAuth docs: `https://huggingface.co/docs/hub/oauth`
    - PKCE is required by HF (public client pattern) — even though we're a confidential client, using PKCE is recommended
    - Keep provider creds in API `.env` + Vercel env vars (staging/prod separation)
    - Don't expose HF client_secret to frontend — all HF OAuth logic lives in the backend
    - Rate-limit `/huggingface/start` and `/callback` to prevent open-redirect abuse
    - Existing password flow untouched; this is purely additive
  - **Tests Required:**
    - Unit (api): `auth_oauth_hf.py` — state/PKCE generation, id_token verification (mock JWKS), email extraction
    - Unit (api): user upsert logic — new user, existing user by email, metadata merge
    - Integration: `/v1/auth/huggingface/start` returns 302 with correct authorize URL + state cookie
    - Integration: `/v1/auth/huggingface/callback` with mocked HF token endpoint → returns 302 to magiclink
    - Unit (webapp): `OAuthButtons` renders both providers, clicks invoke correct handlers
    - Semantic: New user clicks "Continue with GitHub" → GitHub consent → lands on onboarding; New user clicks "Continue with HuggingFace" → HF consent → lands on onboarding; Returning GitHub user → lands on dashboard; User who signed up with password then signs in with GitHub (same email) → lands on their existing account, not a duplicate

- [ ] **Production Subscription Actions — Pull Data, Edit, Unsubscribe** — Production mode active subscriptions only show name/status, missing the action buttons that sandbox mode has
  - **User:** Any org member viewing subscriptions in production mode
  - **Acceptance Criteria:**
    - Active subscriptions in DomainBrowse show Pull Data, Edit, Unsubscribe buttons (same as sandbox)
    - Pull Data opens a drawer that calls `/v1/orgs/{org_id}/live/pull` (real AliCloud data), with cursor-based pagination
    - Unsubscribe cancels the subscription via existing API
  - **Solution Design:**
    - `DomainBrowse.tsx`: Add action buttons to active subscription cards, add LivePullDrawer and UnsubscribeModal
    - LivePullDrawer calls dashboard `/live/pull` endpoint, displays real submission data with quality grades
  - **Tests Required:**
    - Manual: verify buttons appear in production mode, Pull Data shows real data, Unsubscribe works

- [ ] **Sandbox-First UX — Instant Dashboard Without Org** — Default all users to sandbox mode so they see a working dashboard immediately, can subscribe to simulated frontiers, and create sandbox API keys — no org required
  - **User:** Any developer who just signed up (especially those without an org yet)
  - **Problem:** New users land on an empty production dashboard and hit "Create your organization" walls everywhere. They can't see what the product does until they complete onboarding. This kills activation.
  - **Acceptance Criteria:**
    - Default mode is **sandbox** (not production) for all users — `localStorage.app_mode` defaults to `"simulation"`
    - Dashboard Overview works **without orgId** in sandbox mode: pre-selects all simulated verticals, runs local mock data stream, shows demo stat cards (`$50.00` balance, `1` key, `3` subs)
    - Subscriptions page works **without orgId** in sandbox mode: browse simulated verticals, "subscribe" stores in localStorage, verticals list loads from API (public, no auth needed)
    - API Keys page works **without orgId** in sandbox mode: user can create sandbox keys named `"{name}-sandbox"` stored in localStorage. Keys have format `hb_sandbox_...` (generated client-side). These keys are display-only — they do not authenticate against the real API
    - **Shared simulator source:** Dashboard Overview and API pull endpoint (`/v1/data/pull`) must use the same simulator when in sandbox mode. The backend simulator endpoint (`/v1/sandbox/simulate`) generates items for a given vertical and returns them; the dashboard calls this same endpoint for its live stream. This ensures what the user sees in the UI matches what they'd get via API
    - Production mode **still requires org** — toggling to production shows "Create your organization" CTA if no orgId
    - Subtle banner in sandbox mode (top of content area): "You're in sandbox mode — data is simulated. [Create organization] to access production data."
    - Switching from sandbox → production prompts org creation if no org exists
  - **Solution Design:**
    - **Dashboard.tsx:** Change default mode from `"production"` to `"simulation"`. Add `SandboxBanner` component shown when `mode === "simulation"`. Conditionally wrap pages: `OrgRequired` only applies when `mode === "production"` for Subscriptions; always applies for Members, Billing, OrgSettings. API Keys gets a new `SandboxApiKeys` fallback when no org.
    - **Overview.tsx:** When `!orgId && mode === "simulation"`: skip all API calls, use hardcoded demo verticals (crypto, fashion, food), run client-side mock generator (existing `mockItemForVertical`), show static stat cards. No `simulate-receive` API call needed — pure client-side.
    - **Subscriptions.tsx:** When `!orgId && mode === "simulation"`: load verticals from `/v1/verticals` (public endpoint), store subscriptions in `localStorage("sandbox_subscriptions")`. Subscribe/unsubscribe updates localStorage. Active sub state drives Overview's vertical list.
    - **ApiKeys.tsx:** New `SandboxApiKeys` component: create key → generates `hb_sandbox_{random}`, stores in `localStorage("sandbox_api_keys")` with name `"{input}-sandbox"`. Shows key list with copy, revoke (delete from localStorage). Banner: "Sandbox keys are for testing only."
    - **Backend:** New public endpoint `GET /v1/sandbox/simulate?vertical_slug={slug}&limit=5` — returns mock items using the same generators as `simulate-receive` but without auth/org/DB writes. Dashboard and CLI/API docs both reference this endpoint for sandbox testing.
    - **Shared state:** Sandbox subscriptions stored in localStorage are read by both Subscriptions page and Overview page. A custom hook `useSandboxSubscriptions()` provides `{ subs, subscribe, unsubscribe }` backed by localStorage with a `storage` event listener for cross-tab sync.
  - **Technical Notes:**
    - No DB writes in sandbox mode (no org, no real subscriptions, no real keys)
    - localStorage keys: `sandbox_subscriptions` (JSON array of vertical IDs), `sandbox_api_keys` (JSON array of `{id, name, key, created_at}`)
    - The existing `simulate-receive` endpoint (org-scoped, writes to DB) remains for org users in sandbox mode — this new work adds an **unauthenticated** sandbox path for users without orgs
    - Production mode behavior is completely unchanged
  - **Tests Required:**
    - Unit: `useSandboxSubscriptions` hook — subscribe/unsubscribe/persist/cross-tab sync
    - Unit: `SandboxApiKeys` — create/copy/revoke keys in localStorage
    - Unit: Overview renders mock stream without orgId in sandbox mode
    - Unit: Subscriptions loads verticals and manages localStorage subs without orgId
    - Integration: `GET /v1/sandbox/simulate` returns valid mock items without auth
    - Semantic: New user signs up → sees sandbox dashboard immediately → subscribes to vertical → sees data flowing → creates sandbox API key → copies curl snippet → toggles to production → sees "Create org" prompt

- [ ] **Signup Overhaul — Email-First with OTP Verification** — Replace password-first signup with a 3-step email-verified flow
  - **User:** Any new user signing up for the developer portal
  - **Problem:** Users can sign up without verified email ownership. Password collected before email is proven.
  - **Acceptance Criteria:**
    - Step 1: Email only → "Send verification code" → 6-digit OTP sent via Supabase
    - Step 2: Enter OTP → verified server-side → proceed
    - Step 3: Full name + password + confirm password → account created
    - Password fields only appear AFTER email is verified
    - 60-second resend cooldown, "Wrong email?" goes back to step 1
    - After account creation: sync-profile → auto-join check → onboarding or dashboard
  - **Solution Design:** Rewrite `SignUp.tsx` as multi-step form using `signInWithOtp` → `verifyOtp` → `updateUser`
  - **Technical Notes:** Supabase email confirmations must be ENABLED. `VerifyEmail.tsx` kept for link-based flows (password reset).
  - **Tests Required:** OTP send/verify, password mismatch validation, sync-profile auto-join

- [x] **Subscriptions — equal card height** — All domain cards in the grid should share the same row height when collapsed (not in expanded detail view).
  - **User:** Developer browsing data domains to subscribe to
  - **Acceptance Criteria:**
    - Cards within the same grid row are the same height regardless of content length
    - Expanded card still takes full width and grows to fit its content
    - No visual regression on collapse/expand transitions
  - **Solution Design:** Add `h-full` to `DomainCard` root div so it stretches to fill the CSS grid cell (grid already makes all cells in a row equal height by default via `align-items: stretch`). Also add `h-full` to the wrapper div in `DomainGrid`.
  - **Technical Notes:** `DomainBrowse.tsx` — `DomainCard` and `DomainGrid` components
  - **Tests Required:** Visual — cards at same height; expand/collapse works

#### Phase 6 — Live Data Subscription (AliCloud RDS → Portal)

> **Goal:** Connect the developer portal to the production AliCloud RDS MySQL database so data consumers can browse real frontiers, subscribe, and pull actual contributor submissions via API. Consumer feedback (adopt/dispute) is logged for future supply-side integration.
> **Data source:** AliCloud RDS MySQL (`codatta-prod.rwlb.singapore.rds.aliyuncs.com:3306`, database `cfp_metacore`)
> **Architecture:** Direct read from MySQL (proxy pattern, no replication). Consumer state in Supabase.
> **Pricing:** Free for now; usage metered via `usage_meter` table for future billing.

##### Phase 6A — MySQL Connection + Frontier Browse API

- [ ] **MySQL connection pool** — `aiomysql` async pool in `packages/api/app/mysql_db.py`. Config in `config.py` + `.env`.
- [ ] **New Supabase tables** — `consumer_feedback`, `webhook_endpoints`, `usage_meter`. Alter `subscriptions` to add `frontier_id`, `task_ids`, `cursor_position`, `webhook_url`.
- [ ] **`GET /v1/frontiers`** — Browse all frontiers from MySQL, segmented by status (ONLINE = ongoing, OFFLINE/PAUSED = expired). Includes task count and total submission count.
- [ ] **`GET /v1/frontiers/{id}/tasks`** — List tasks under a frontier with submission counts.
- [ ] **`GET /v1/frontiers/{id}/tasks/{task_id}/preview`** — Sample adopted submissions with quality scores. JWT auth.

##### Phase 6B — Subscription + Cursor-Based Data Pull

- [ ] **Extended subscription creation** — `POST /v1/orgs/{org_id}/subscriptions` accepts `frontier_id` + optional `task_ids` (in addition to existing `vertical_id`).
- [ ] **`GET /v1/live/pull`** — Cursor-based pull from MySQL. API key auth. Supports historical backfill (cursor=0) and incremental (cursor=last_submission_id). Returns submissions with quality scores and consumer feedback state.
- [ ] **`POST /v1/live/items/{submission_id}/adopt`** — Record adopt feedback in Supabase `consumer_feedback`.
- [ ] **`POST /v1/live/items/{submission_id}/dispute`** — Record dispute feedback with optional reason.
- [ ] **Dashboard variants** — Same pull/adopt/dispute under `/v1/orgs/{org_id}/live/...` with JWT auth.

##### Phase 6C — Frontend: Frontier Browse + Subscribe

- [x] **FrontierBrowse component** — New component showing live frontiers from MySQL, segmented by status. Expand to see tasks, preview samples, subscribe.
- [x] **Update Subscriptions.tsx** — Add "Live Data Sources" section. Detect frontier-based subs and use cursor-based pull in the Pull Data drawer.
- [x] **Shared types** — `FrontierSummary`, `TaskSummary`, `LiveSubmission` in `shared/index.ts`.

- [ ] **Polish frontier cards** — Apply the same card style as simulated verticals (icon, name, description, tags, price hint). Create descriptions and category tags for each frontier. Grid layout (2-col).
- [ ] **Filter & sort controls** — Sort by: recency (newest first), total submissions (most data), alphabetical. Filter by: category tag, status (live/expired).
- [ ] **Expired frontier accessibility** — Indicate that expired/paused frontiers still have accessible historical data. Show "Historical data available" badge instead of greying out.
- [ ] **Subscription agreement modal** — On first subscribe, show a modal with: high-level pricing formula overview (placeholder text), data usage terms (placeholder), "I agree" checkbox + confirm button. Only shown once per org (track in org_settings or localStorage).
- [x] **Production / Sandbox toggle** — App-wide toggle in top bar switches between production (live AliCloud data) and sandbox (simulated verticals). Persisted in localStorage. Subscriptions and Overview pages show only relevant content per mode.
- [x] **Side navbar layout** — Dashboard uses a collapsible side navbar with grouped menu items: Data (Dashboard, Subscriptions, API Keys, Billing), Tasks (Launch Task, Task Manager, Task Analytics — coming soon), Settings (Team, Organization, Account).
- [x] **MySQL pool resilience** — `pool_recycle=300`, increased connect timeout (30s), auto-retry on stale SSL connections.
- [ ] **API key scope & daily limit** — Each API key can be scoped to specific subscription IDs (or all). Optional daily burn limit in USD. New Supabase columns: `api_keys.subscription_ids` (UUID[]), `api_keys.daily_limit_usd` (numeric). New table: `api_key_daily_usage` tracks per-key per-day usage.
  - **Acceptance Criteria:**
    - Key creation accepts `subscription_ids` (array or null=all) and `daily_limit_usd` (number or null=unlimited)
    - Data pull endpoints enforce scope: reject pulls for subscriptions not in the key's scope
    - Daily limit enforcement: reject pulls when `api_key_daily_usage.amount_usd >= daily_limit_usd`
    - Key list endpoint returns scope and limit info
  - **Technical Notes:** Scope enforcement in `apikey_auth.py` or `live_data.py`. Daily usage tracked per pull request.
  - **Tests Required:** Create scoped key → pull from allowed sub → success. Pull from disallowed sub → 403. Exceed daily limit → 429.

##### Phase 6C.1.5 — Subscription Filters: Quality Grade + Task-level Live/Historical ✅

- [x] **Quality grade multi-select filter (S/A/B/C/D + All)** — Adds a grade filter button group to the frontier browse UI. Supports multi-select; selecting All deselects individual grades; selecting any grade deselects All; deselecting all grades reverts to All.
  - **User:** Data consumers who need data above a minimum quality threshold (e.g., only S+A grades for model training).
  - **Acceptance Criteria:**
    - Filter bar shows "All Grades / S / A / B / C / D" toggle buttons with active highlighting
    - Multi-select: user can select any combination of S, A, B, C, D
    - Selecting "All Grades" clears individual selections; selecting any grade clears "All Grades"
    - Deselecting all grades automatically reverts to "All Grades"
    - On subscribe, selected grades are stored in `subscriptions.filters.quality_grades` (null when All)
    - `GET /v1/live/pull` reads `filters.quality_grades` and adds `AND s.result IN (...)` to MySQL query
    - Grade B filter also includes `OR s.result IS NULL` (NULL result rows default to B)
  - **Solution Design:**
    - Frontend: `qualityFilter: Set<QualityGrade | "all">` state + `toggleGrade()` in `DomainBrowse`; grade buttons added to filter bar; `filters` field included in `POST /v1/orgs/{org_id}/subscriptions` body
    - Backend: `GRADE_RESULT = {"S":5,"A":4,"B":3,"C":2,"D":1}`; `_resolve_subscription` now selects `filters`; `_do_pull` builds dynamic `grade_filter` SQL clause from `sub.filters.quality_grades`
  - **Files changed:** `packages/webapp/src/components/dashboard/DomainBrowse.tsx`, `packages/api/app/routes/live_data.py`

- [x] **Task-level Live/Historical filtering** — The existing Live/Historical toggle now filters tasks within each frontier's expanded view, not just frontier-level cards. "Subscribe to All" subscribes only to the currently visible (filtered) tasks.
  - **User:** Data consumers who want only actively-collecting (live) task data, or only completed (historical) task data, without mixing both.
  - **Acceptance Criteria:**
    - Selecting "Live" in the status filter: expanded frontier task list shows only ONLINE/COLLECTING/PREPARING tasks
    - Selecting "Historical": shows only non-live-status tasks
    - Task count shows "3 of 8" format when filtered
    - "Subscribe to All" passes only the visible task IDs when a status filter is active; passes no task_ids (full frontier) when "All" is selected
    - Subscribed task_ids are persisted in `subscriptions.task_ids` and respected by `_get_task_ids()` at pull time
  - **Solution Design:**
    - `LIVE_TASK_STATUSES = Set(["ONLINE","COLLECTING","PREPARING"])` constant
    - `statusFilter` prop propagated: `DomainBrowse` → `DomainGrid` → `DomainCard` → `TaskList`
    - `TaskList` derives `visibleTasks` from `statusFilter`; "Subscribe to All" passes `visibleTasks.map(t => t.task_id)` when filtered
    - Backend unchanged: `_get_task_ids` already respects `sub.task_ids` when set
  - **Files changed:** `packages/webapp/src/components/dashboard/DomainBrowse.tsx`

##### Phase 6C.2 — Frontier Card Expand/Collapse Animation ✅

- [x] **Grid reflow algorithm** — `ReflowGrid` splits cards into three segments: before (2-col grid), expanded card (full-width row), after (2-col grid). Row-mate displaced to adjacent segment based on column position.
- [x] **Expand/collapse animation** — `ResizeObserver` tracks actual content height continuously so the animated container adjusts as tasks load asynchronously. CSS transitions on `height` (0 → measured) and `opacity` with 300ms ease. No clipping, no layout jump.
- [x] **Close button** — `✕` button top-right of expanded card, flat design (1.5px border), keyboard accessible via `aria-label`.
- [x] **TaskList error resilience** — Graceful `.catch()` fallback when frontier task API is unreachable.

##### Phase 6C.3 — Frontier Card Enhancements (Future)

- [ ] **Banner image** — Each frontier card (aka Vertical Card) displays a hero/banner image that visually illustrates the data vertical's key concept, similar to an ad creative. Collapsed card shows a cropped thumbnail; expanded card shows a larger version.
  - **User:** Data consumers browsing and evaluating frontiers
  - **Acceptance Criteria:**
    - Banner renders at the top of each card, fixed aspect ratio (16:9 or 3:1)
    - Fallback gradient or category-themed placeholder when no image URL is set
    - Expanded card shows full banner; collapsed shows thumbnail crop
  - **Technical Notes:** Add `banner_url` to `FrontierMeta`. Lazy-load images. Storage: Supabase Storage or CDN. Placeholder generated from category tags.

- [ ] **Launched-by info (developer & org)** — Card footer shows who launched the task: developer name/avatar and organization name/logo. Clickable to view the org/developer profile for trustworthiness assessment.
  - **User:** Data consumers evaluating task trustworthiness before subscribing
  - **Acceptance Criteria:**
    - Card footer: "Launched by [Org Name]" with org logo thumbnail
    - Click org name → popover or page showing: org name, logo, verified badge, active frontier count, total submissions, description
    - If developer info available, show developer name alongside org
    - Trust indicators: verified status, data volume, frontier history
  - **Technical Notes:** Requires `GET /v1/orgs/{id}/public-profile` endpoint joining frontier data with org records. Lightweight popover first; full profile page in later iteration. Supply-side org data may need cross-DB join (MySQL frontiers → Supabase orgs).

##### Phase 7 — Access Logging, Metering & Variable Pricing

> **Goal:** Record every data access (pulls, previews, feedback) with per-record pricing so orgs can be charged by contract. Each data unit is priced differently based on frontier, task type, and quality tier. Prices are stamped at access time so retroactive price changes don't affect past billing.

###### Phase 7A — Database Schema & Access Logging Middleware

- [ ] **`pricing_schedule` table** — Per-frontier, per-task, per-quality-tier pricing with time ranges.
  ```
  pricing_schedule (id, frontier_id, task_id nullable, quality_tier nullable,
    unit_price_usd numeric, effective_from timestamptz, effective_until timestamptz nullable,
    created_by text)
  ```
  - Lookup priority: frontier+task+tier → frontier+task → frontier → default
  - **Why:** Each data-unit is priced differently. A CEX Hot Wallet record may be $0.50 while a food photo is $0.01.

- [ ] **`access_log` table** — Append-only, every API request that touches data.
  ```
  access_log (id uuid, timestamp timestamptz default now(),
    org_id uuid, api_key_id uuid nullable, user_id uuid nullable,
    endpoint text, method text, subscription_id uuid nullable,
    frontier_id text nullable, record_count int default 0,
    item_costs jsonb nullable, total_cost_usd numeric default 0,
    response_status int, latency_ms int, ip_address inet)
  ```
  - `item_costs`: array of `{submission_id, task_id, unit_price_usd}` — price at point of sale
  - `total_cost_usd`: sum of per-item prices for this request
  - **Why:** Contract audits require proof of what was accessed, when, and at what price.

- [ ] **`usage_daily` table** — Aggregated daily rollups for billing dashboards and invoicing.
  ```
  usage_daily (org_id uuid, subscription_id uuid, date date,
    pull_count int, record_count int, adopt_count int, dispute_count int,
    preview_count int, total_cost_usd numeric,
    unique (org_id, subscription_id, date))
  ```

- [ ] **Access logging middleware** — FastAPI middleware that logs every data-touching request to `access_log` asynchronously (fire-and-forget Supabase insert, non-blocking). Captures: org, key, endpoint, record count, latency, status code.
  - **Technical Notes:** Use `BackgroundTasks` or `asyncio.create_task()` to avoid adding latency. Log after response is sent. Include request timing via middleware start/end.
  - **Tests Required:** Pull data → verify `access_log` row created with correct fields. Preview data → verify logged with `record_count` and zero cost.

###### Phase 7B — Price Resolution & Metered Pulls

- [ ] **Price resolver** — `resolve_price(frontier_id, task_id, quality_tier) → Decimal` function in `packages/api/app/pricing.py`.
  - Queries `pricing_schedule` with cascading fallback: exact match → frontier+task → frontier-only → system default ($0.00 for free tier)
  - Caches schedule in memory (refresh every 5 min) to avoid per-record DB lookups
  - Returns the price effective at `now()`
  - **Tests Required:** Set price for frontier A task 1 = $0.10. Pull from A/1 → price is $0.10. Pull from A/2 (no task price) → falls back to frontier price.

- [ ] **Stamp price on live data pull** — Extend `GET /v1/live/pull` to:
  1. For each returned submission, call `resolve_price(frontier_id, task_id, quality_tier)`
  2. Include `unit_price_usd` in each item of the response
  3. Write `item_costs` array and `total_cost_usd` to `access_log`
  4. Update `usage_meter` with cost (not just record count)
  - **Why:** The live data path currently meters `record_count` but not monetary value. Contracts bill on cost, not volume.

- [ ] **Meter preview/sample access** — Extend `GET /v1/frontiers/{id}/tasks/{id}/preview` to:
  1. Log to `access_log` with `endpoint="/v1/frontiers/.../preview"`, record_count, total_cost_usd=0 (previews are free but tracked)
  2. Enforce a preview rate limit (e.g., 100 previews/day per org) once contracts define free-tier allowances
  - **Why:** Currently preview reads production data from AliCloud with no logging. Under contracts, even free access must be auditable.

###### Phase 7C — Daily Aggregation & Enforcement

- [ ] **Daily rollup job** — Cron or scheduled task that aggregates `access_log` into `usage_daily` for each (org, subscription, date). Runs at midnight UTC.
  - **Technical Notes:** SQL: `INSERT INTO usage_daily ... SELECT org_id, subscription_id, date(timestamp), count(*) filter (where endpoint like '%pull%'), sum(record_count), ... FROM access_log WHERE date(timestamp) = yesterday GROUP BY 1,2,3 ON CONFLICT (org_id, subscription_id, date) DO UPDATE SET ...`

- [ ] **API key scope enforcement** — Pull endpoints check `api_keys.subscription_ids`; reject with 403 if key tries to pull from a subscription not in its scope.

- [ ] **Daily spend limit enforcement** — Pull endpoints check `api_keys.daily_limit_usd` against today's `usage_daily.total_cost_usd` for the key's org; reject with 429 if exceeded.

- [ ] **Rate limiting middleware** — Enforce documented limits (100 req/min pull, 200 req/min feedback, 60 req/min public) using in-memory counter or Redis.

###### Phase 7D — Contracts & Invoicing (Future)

- [ ] **`contracts` table** — Org-level billing agreements.
  ```
  contracts (id uuid, org_id uuid, plan_type text,
    pricing_schedule_ids uuid[], discount_pct numeric nullable,
    monthly_credit_usd numeric nullable, free_preview_limit int nullable,
    starts_at timestamptz, ends_at timestamptz nullable,
    status text, terms_version text)
  ```
  - Plan types: `free_tier` (limited previews, no pulls), `pay_per_record` (variable pricing), `monthly_flat` (included volume + overage), `enterprise` (custom)

- [ ] **Invoice generation** — Monthly job: sum `usage_daily.total_cost_usd` for the billing period, apply contract discount/credits, generate invoice record. Ties into Stripe for payment collection.

- [ ] **Billing dashboard** — Frontend: usage charts, daily cost breakdown by frontier, downloadable CSV/PDF statements.

##### Phase 7 — Access Logging, Metering & Variable Pricing

> **Goal:** Record every data access (pulls, previews, feedback) with per-record pricing so orgs can be charged by contract. Each data unit is priced differently based on frontier, task type, and quality tier. Prices are stamped at access time so retroactive price changes don't affect past billing.

###### Phase 7A — Database Schema & Access Logging Middleware

- [ ] **`pricing_schedule` table** — Per-frontier, per-task, per-quality-tier pricing with time ranges.
  ```
  pricing_schedule (id, frontier_id, task_id nullable, quality_tier nullable,
    unit_price_usd numeric, effective_from timestamptz, effective_until timestamptz nullable,
    created_by text)
  ```
  - Lookup priority: frontier+task+tier → frontier+task → frontier → default
  - **Why:** Each data-unit is priced differently. A CEX Hot Wallet record may be $0.50 while a food photo is $0.01.

- [ ] **`access_log` table** — Append-only, every API request that touches data.
  ```
  access_log (id uuid, timestamp timestamptz default now(),
    org_id uuid, api_key_id uuid nullable, user_id uuid nullable,
    endpoint text, method text, subscription_id uuid nullable,
    frontier_id text nullable, record_count int default 0,
    item_costs jsonb nullable, total_cost_usd numeric default 0,
    response_status int, latency_ms int, ip_address inet)
  ```
  - `item_costs`: array of `{submission_id, task_id, unit_price_usd}` — price at point of sale
  - `total_cost_usd`: sum of per-item prices for this request
  - **Why:** Contract audits require proof of what was accessed, when, and at what price.

- [ ] **`usage_daily` table** — Aggregated daily rollups for billing dashboards and invoicing.
  ```
  usage_daily (org_id uuid, subscription_id uuid, date date,
    pull_count int, record_count int, adopt_count int, dispute_count int,
    preview_count int, total_cost_usd numeric,
    unique (org_id, subscription_id, date))
  ```

- [ ] **Access logging middleware** — FastAPI middleware that logs every data-touching request to `access_log` asynchronously (fire-and-forget Supabase insert, non-blocking). Captures: org, key, endpoint, record count, latency, status code.
  - **Technical Notes:** Use `BackgroundTasks` or `asyncio.create_task()` to avoid adding latency. Log after response is sent. Include request timing via middleware start/end.
  - **Tests Required:** Pull data → verify `access_log` row created with correct fields. Preview data → verify logged with `record_count` and zero cost.

###### Phase 7B — Price Resolution & Metered Pulls

- [ ] **Price resolver** — `resolve_price(frontier_id, task_id, quality_tier) → Decimal` function in `packages/api/app/pricing.py`.
  - Queries `pricing_schedule` with cascading fallback: exact match → frontier+task → frontier-only → system default ($0.00 for free tier)
  - Caches schedule in memory (refresh every 5 min) to avoid per-record DB lookups
  - Returns the price effective at `now()`
  - **Tests Required:** Set price for frontier A task 1 = $0.10. Pull from A/1 → price is $0.10. Pull from A/2 (no task price) → falls back to frontier price.

- [ ] **Stamp price on live data pull** — Extend `GET /v1/live/pull` to:
  1. For each returned submission, call `resolve_price(frontier_id, task_id, quality_tier)`
  2. Include `unit_price_usd` in each item of the response
  3. Write `item_costs` array and `total_cost_usd` to `access_log`
  4. Update `usage_meter` with cost (not just record count)
  - **Why:** The live data path currently meters `record_count` but not monetary value. Contracts bill on cost, not volume.

- [ ] **Meter preview/sample access** — Extend `GET /v1/frontiers/{id}/tasks/{id}/preview` to:
  1. Log to `access_log` with `endpoint="/v1/frontiers/.../preview"`, record_count, total_cost_usd=0 (previews are free but tracked)
  2. Enforce a preview rate limit (e.g., 100 previews/day per org) once contracts define free-tier allowances
  - **Why:** Currently preview reads production data from AliCloud with no logging. Under contracts, even free access must be auditable.

###### Phase 7C — Daily Aggregation & Enforcement

- [ ] **Daily rollup job** — Cron or scheduled task that aggregates `access_log` into `usage_daily` for each (org, subscription, date). Runs at midnight UTC.
  - **Technical Notes:** SQL: `INSERT INTO usage_daily ... SELECT org_id, subscription_id, date(timestamp), count(*) filter (where endpoint like '%pull%'), sum(record_count), ... FROM access_log WHERE date(timestamp) = yesterday GROUP BY 1,2,3 ON CONFLICT (org_id, subscription_id, date) DO UPDATE SET ...`

- [ ] **API key scope enforcement** — Pull endpoints check `api_keys.subscription_ids`; reject with 403 if key tries to pull from a subscription not in its scope.

- [ ] **Daily spend limit enforcement** — Pull endpoints check `api_keys.daily_limit_usd` against today's `usage_daily.total_cost_usd` for the key's org; reject with 429 if exceeded.

- [ ] **Rate limiting middleware** — Enforce documented limits (100 req/min pull, 200 req/min feedback, 60 req/min public) using in-memory counter or Redis.

###### Phase 7D — Contracts & Invoicing (Future)

- [ ] **`contracts` table** — Org-level billing agreements.
  ```
  contracts (id uuid, org_id uuid, plan_type text,
    pricing_schedule_ids uuid[], discount_pct numeric nullable,
    monthly_credit_usd numeric nullable, free_preview_limit int nullable,
    starts_at timestamptz, ends_at timestamptz nullable,
    status text, terms_version text)
  ```
  - Plan types: `free_tier` (limited previews, no pulls), `pay_per_record` (variable pricing), `monthly_flat` (included volume + overage), `enterprise` (custom)

- [ ] **Invoice generation** — Monthly job: sum `usage_daily.total_cost_usd` for the billing period, apply contract discount/credits, generate invoice record. Ties into Stripe for payment collection.

- [ ] **Billing dashboard** — Frontend: usage charts, daily cost breakdown by frontier, downloadable CSV/PDF statements.

##### Phase 7 — Access Logging, Metering & Variable Pricing

> **Goal:** Record every data access (pulls, previews, feedback) with per-record pricing so orgs can be charged by contract. Each data unit is priced differently based on frontier, task type, and quality tier. Prices are stamped at access time so retroactive price changes don't affect past billing.

###### Phase 7A — Database Schema & Access Logging Middleware

- [ ] **`pricing_schedule` table** — Per-frontier, per-task, per-quality-tier pricing with time ranges.
  ```
  pricing_schedule (id, frontier_id, task_id nullable, quality_tier nullable,
    unit_price_usd numeric, effective_from timestamptz, effective_until timestamptz nullable,
    created_by text)
  ```
  - Lookup priority: frontier+task+tier → frontier+task → frontier → default
  - **Why:** Each data-unit is priced differently. A CEX Hot Wallet record may be $0.50 while a food photo is $0.01.

- [ ] **`access_log` table** — Append-only, every API request that touches data.
  ```
  access_log (id uuid, timestamp timestamptz default now(),
    org_id uuid, api_key_id uuid nullable, user_id uuid nullable,
    endpoint text, method text, subscription_id uuid nullable,
    frontier_id text nullable, record_count int default 0,
    item_costs jsonb nullable, total_cost_usd numeric default 0,
    response_status int, latency_ms int, ip_address inet)
  ```
  - `item_costs`: array of `{submission_id, task_id, unit_price_usd}` — price at point of sale
  - `total_cost_usd`: sum of per-item prices for this request
  - **Why:** Contract audits require proof of what was accessed, when, and at what price.

- [ ] **`usage_daily` table** — Aggregated daily rollups for billing dashboards and invoicing.
  ```
  usage_daily (org_id uuid, subscription_id uuid, date date,
    pull_count int, record_count int, adopt_count int, dispute_count int,
    preview_count int, total_cost_usd numeric,
    unique (org_id, subscription_id, date))
  ```

- [ ] **Access logging middleware** — FastAPI middleware that logs every data-touching request to `access_log` asynchronously (fire-and-forget Supabase insert, non-blocking). Captures: org, key, endpoint, record count, latency, status code.
  - **Technical Notes:** Use `BackgroundTasks` or `asyncio.create_task()` to avoid adding latency. Log after response is sent. Include request timing via middleware start/end.
  - **Tests Required:** Pull data → verify `access_log` row created with correct fields. Preview data → verify logged with `record_count` and zero cost.

###### Phase 7B — Price Resolution & Metered Pulls

- [ ] **Price resolver** — `resolve_price(frontier_id, task_id, quality_tier) → Decimal` function in `packages/api/app/pricing.py`.
  - Queries `pricing_schedule` with cascading fallback: exact match → frontier+task → frontier-only → system default ($0.00 for free tier)
  - Caches schedule in memory (refresh every 5 min) to avoid per-record DB lookups
  - Returns the price effective at `now()`
  - **Tests Required:** Set price for frontier A task 1 = $0.10. Pull from A/1 → price is $0.10. Pull from A/2 (no task price) → falls back to frontier price.

- [ ] **Stamp price on live data pull** — Extend `GET /v1/live/pull` to:
  1. For each returned submission, call `resolve_price(frontier_id, task_id, quality_tier)`
  2. Include `unit_price_usd` in each item of the response
  3. Write `item_costs` array and `total_cost_usd` to `access_log`
  4. Update `usage_meter` with cost (not just record count)
  - **Why:** The live data path currently meters `record_count` but not monetary value. Contracts bill on cost, not volume.

- [ ] **Meter preview/sample access** — Extend `GET /v1/frontiers/{id}/tasks/{id}/preview` to:
  1. Log to `access_log` with `endpoint="/v1/frontiers/.../preview"`, record_count, total_cost_usd=0 (previews are free but tracked)
  2. Enforce a preview rate limit (e.g., 100 previews/day per org) once contracts define free-tier allowances
  - **Why:** Currently preview reads production data from AliCloud with no logging. Under contracts, even free access must be auditable.

###### Phase 7C — Daily Aggregation & Enforcement

- [ ] **Daily rollup job** — Cron or scheduled task that aggregates `access_log` into `usage_daily` for each (org, subscription, date). Runs at midnight UTC.
  - **Technical Notes:** SQL: `INSERT INTO usage_daily ... SELECT org_id, subscription_id, date(timestamp), count(*) filter (where endpoint like '%pull%'), sum(record_count), ... FROM access_log WHERE date(timestamp) = yesterday GROUP BY 1,2,3 ON CONFLICT (org_id, subscription_id, date) DO UPDATE SET ...`

- [ ] **API key scope enforcement** — Pull endpoints check `api_keys.subscription_ids`; reject with 403 if key tries to pull from a subscription not in its scope.

- [ ] **Daily spend limit enforcement** — Pull endpoints check `api_keys.daily_limit_usd` against today's `usage_daily.total_cost_usd` for the key's org; reject with 429 if exceeded.

- [ ] **Rate limiting middleware** — Enforce documented limits (100 req/min pull, 200 req/min feedback, 60 req/min public) using in-memory counter or Redis.

###### Phase 7D — Contracts & Invoicing (Future)

- [ ] **`contracts` table** — Org-level billing agreements.
  ```
  contracts (id uuid, org_id uuid, plan_type text,
    pricing_schedule_ids uuid[], discount_pct numeric nullable,
    monthly_credit_usd numeric nullable, free_preview_limit int nullable,
    starts_at timestamptz, ends_at timestamptz nullable,
    status text, terms_version text)
  ```
  - Plan types: `free_tier` (limited previews, no pulls), `pay_per_record` (variable pricing), `monthly_flat` (included volume + overage), `enterprise` (custom)

- [ ] **Invoice generation** — Monthly job: sum `usage_daily.total_cost_usd` for the billing period, apply contract discount/credits, generate invoice record. Ties into Stripe for payment collection.

- [ ] **Billing dashboard** — Frontend: usage charts, daily cost breakdown by frontier, downloadable CSV/PDF statements.

##### Phase 6D — Webhook Push (V1)

- [ ] **Webhook service** — Background poller delivers new submissions to `webhook_endpoints.url` with HMAC-SHA256 signature.
- [ ] **Webhook management endpoints** — Register, remove, test webhook per subscription.
- [ ] **Webhook UI** — URL field + test button in subscription edit modal.

##### Phase 6E — Consumer Feedback → Supply Side (Future)

- [ ] **Feedback bridge service** — Sync `consumer_feedback` records back to supply-side audit system (cfp-metacore). Influence contributor reputation and re-audit decisions.
  - **User:** Platform operators, supply-side QA
  - **Acceptance Criteria:** Disputed items trigger re-audit on supply side. Adopt patterns improve contributor reputation scores.
  - **Technical Notes:** Requires s2s auth with cfp-metacore API. Design the feedback protocol before building.
  - **Tests Required:** Round-trip: consumer disputes → supply-side re-audit triggered → outcome logged

#### Fix: Frontier subscription fails due to NOT NULL constraint on vertical_id ✅

- [x] **Bug:** Subscribing to a frontier (production mode) always failed with `null value in column "vertical_id" violates not-null constraint`. The `subscriptions` table required `vertical_id` to be non-null, but frontier-based subscriptions only set `frontier_id`.
- [x] **Fix:** Supabase migration `make_vertical_id_nullable_for_frontier_subscriptions` — `ALTER TABLE subscriptions ALTER COLUMN vertical_id DROP NOT NULL` + added CHECK constraint `subscriptions_requires_source` ensuring at least one of `vertical_id` or `frontier_id` is set.
- [x] **Verification:** Frontier subscription insert succeeds; both-null insert correctly rejected by CHECK constraint.

#### Phase 4A — Billing Reliability & Infrastructure ✅

- [x] **Fix: Stripe payment not crediting balance** — `POST /verify-session` fallback when webhook hasn't fired.
- [x] **DB: org_settings, delivery_items.org_id/environment, users.is_admin**
- [x] **Admin API (Phase 1)** — superadmin-gated: list orgs, get/update org settings, list/resolve disputes.

#### Phase 4B — Correct Data Charge Lifecycle ✅

- [x] **Freeze on receive** — `data.py` pull endpoint freezes balance (available → frozen) per item. Underfunded flag if insufficient.
- [x] **Settle on adopt** — adopt endpoint settles (frozen → spent). No available balance change.
- [x] **Refund on valid dispute** — admin accept: frozen → available, `refund` transaction.
- [x] **Settle on rejected dispute** — admin reject: frozen → spent, `settle` transaction.
- [x] **Spent tracking** — `accounts.balance_spent_usd` column. Updated on every settle. Shown in billing UI as 4th card.
- [x] **Frontend: correct balance flow** — 4-card layout (Available, Frozen, Total, Spent). Transaction type badges with distinct colors (topup=green, freeze=amber, settle=purple, refund=blue). Correct confirm modal text.
- [x] **Shared types** — `AnnotationItem.status` includes `adopted|disputed|refunded`. `DeliveryItem` includes `underfunded`.
- [ ] **Configurable auto-adopt period** *(deferred to Phase 4C)*
- [ ] **Configurable auto-dispute-valid period** *(deferred to Phase 4C)*

#### Phase 4D — Simulator writes to test DB (end-to-end data lifecycle) ✅

- [x] **API: `POST /v1/orgs/{org_id}/data/simulate-receive`** — JWT-authenticated, inserts delivery_item with `environment='test'`, runs `_freeze_on_receive()`.
- [x] **API: dashboard adopt/dispute endpoints** — `POST /v1/orgs/{org_id}/data/items/{id}/adopt|dispute` with JWT auth, same settle/freeze logic as API-key endpoints.
- [x] **Frontend: simulator calls simulate-receive API** — each tick POSTs to API, uses DB-created item with real ID. Falls back to local mock on failure.
- [x] **Frontend: adopt/dispute always call backend** — removed production-only guard, all actions hit real API.
- [x] **Billing reflects simulator activity** — test balance/transactions update from simulator data flow (no additional code needed).

#### Phase 4C — Org Configurable Settings with Approval Flow (Future)

> **Status:** Planned. Depends on Phase 4B (charge lifecycle must be correct before exposing configurables to orgs).

- [ ] **DB: `setting_change_requests` table**
  - `setting_change_requests(id uuid PK, org_id uuid FK, requested_by uuid FK, field text, old_value text, new_value text, status text DEFAULT 'pending', reviewed_by uuid, reviewed_at timestamptz, review_note text, created_at timestamptz DEFAULT now())`
  - `status` enum: `pending`, `approved`, `rejected`, `superseded`
  - When approved: apply value to `org_settings` and set `status=approved`.
  - When a new request is made for the same field while one is pending: mark old as `superseded`.

- [ ] **DB: `org_settings` — new columns**
  - `auto_dispute_valid_hours int DEFAULT NULL` — NULL = requires manual admin action.
  - `account_manager_id uuid FK → users(id)` — assigned Codatta/Humanbased associate. NULL = falls back to any superadmin.

- [ ] **API: org-facing settings endpoints**
  - `GET /v1/orgs/{org_id}/settings` — returns effective settings + any pending change requests.
  - `POST /v1/orgs/{org_id}/settings/request-change` — creates a `setting_change_request`. Sends email to account manager via Resend.
    - Body: `{ "field": "auto_adopt_hours", "new_value": "72" }`
    - Validates field name and value range.
    - Returns `{ "request_id": "...", "status": "pending" }`.
  - **Email to account manager:** Subject: "Setting change request — {org_name}". Body includes org name, field, old → new value, link to admin panel to review.

- [ ] **API: admin review endpoints**
  - `GET /v1/admin/setting-requests` — list all pending requests (filterable by org, field).
  - `POST /v1/admin/setting-requests/{id}/review` — approve or reject.
    - Body: `{ "action": "approve" | "reject", "adjusted_value": "72", "note": "Approved per agreement" }`
    - On approve: update `org_settings`, set request `status=approved`, email org admin confirmation.
    - On reject: set request `status=rejected`, email org admin with reason.
    - `adjusted_value` is optional — allows admin to approve with a different value than requested.
  - **Email to org admin on approval:** "Your setting change for {field} has been approved. New value: {value}."
  - **Email to org admin on rejection:** "Your setting change for {field} was not approved. Reason: {note}."

- [ ] **Frontend: Organization Settings — Data & Billing section**
  - New section in OrgSettings.tsx below Domain Allowlist.
  - Fields:
    - Auto-adopt period (number input, hours, min 1 max 720)
    - Auto-dispute-valid period (number input, hours, or "Manual" toggle for NULL)
    - Per-vertical overrides (table: vertical name | auto-adopt hours | edit/remove)
  - **Save button:** disabled/hidden when no changes. Enabled with accent color when values differ from effective settings.
  - On save: calls `POST /v1/orgs/{org_id}/settings/request-change` for each changed field.
  - **Pending state:** Fields with pending requests show amber "Pending approval" badge next to current effective value. Tooltip shows requested value and request date.
  - **Approved/rejected toast:** When a previously pending request is resolved, show a notification on next page load.

- [ ] **Legal/ToS integration (optional)**
  - Setting change requests that exceed certain thresholds (e.g., auto-adopt > 168h) may flag for ToS amendment.
  - Admin review UI shows a "Requires ToS update" warning for flagged requests.
  - Admin can attach a ToS amendment document link to the approval.
  - Org admin must acknowledge the ToS amendment before the change takes effect.

#### Phase 3E — Billing: Test/Live Mode Separation

- [x] **DB: add `environment` column to `accounts` and `transactions`**
  - `accounts.environment text NOT NULL DEFAULT 'test'` — each org gets separate test and live account rows
  - `transactions.environment text NOT NULL DEFAULT 'test'` — every transaction tagged with its mode
  - Add unique constraint on `accounts(org_id, environment)` to prevent duplicate accounts per mode
  - Backfill: existing rows get `environment = 'test'` (all current data is from Stripe test keys)
  - **Technical Notes:** Supabase migration. The API auto-detects mode from the Stripe key prefix (`sk_test_` vs `sk_live_`).

- [x] **Backend: environment-aware billing endpoints**
  - Config: derive `stripe_environment` from `stripe_secret_key` prefix at startup (`test` or `live`)
  - `GET /balance` — filter by current environment; auto-create account row if missing
  - `POST /checkout` — tag session metadata with `environment`
  - `GET /transactions` — filter by current environment
  - `POST /webhook` — read environment from session metadata; credit the correct account row
  - `GET /checkout/{session_id}` — unchanged (reads from Stripe directly)
  - **Acceptance Criteria:** Test-mode payments only affect test balances. Switching to live keys starts with $0 live balance. No cross-contamination.

- [x] **Frontend: display current billing mode**
  - Billing page shows a badge ("Test Mode" / "Live Mode") next to the heading
  - Test mode badge is amber; live mode badge is green
  - New `GET /v1/billing/mode` endpoint returns `{ "environment": "test" | "live" }`
  - **Acceptance Criteria:** User always knows which mode billing is operating in.

#### Phase 3C — Overview: Production Connection Controls ✅

- [x] **Disconnect button alongside Production toggle** — when connected to production, show an explicit red `Disconnect` button next to the DataSourceToggle (not just clicking the Simulator side). Clicking it opens the DisconnectModal.
- [x] **X button on "Connected to production" modal** — `DataSourceModal` done phase shows a close button so the user can dismiss it immediately without waiting for the auto-close timer.
- [x] **ConnectionStatus bar** — persistent footer bar showing REST API / Database / Realtime health with latency; expands to show per-connection details; polls every 30s, Realtime every 3s.

#### Phase 3B — Members: Permissions, Edit, and Invitation Confirmation

- [ ] **DB: org_invitations table + permissions field**
  - `org_invitations(id, org_id, email, role, permissions jsonb, invited_by uuid, token text, created_at, expires_at, accepted_at)` — tracks pending invites for users who don't yet have an account
  - `org_memberships.permissions jsonb DEFAULT '["data.read","subscriptions.manage"]'` — granular permission flags
  - **Technical Notes:** Apply via Supabase migration. `token` is a random 32-char string for invite link (future).

- [ ] **Backend: list/revoke pending invitations**
  - `GET /v1/orgs/{id}/invitations` — list pending (accepted_at IS NULL) invitations for org
  - `DELETE /v1/orgs/{id}/invitations/{inv_id}` — revoke (delete) pending invitation
  - `POST /v1/orgs/{id}/members/invite` — also inserts into `org_invitations` when user doesn't exist
  - **User:** org admin/owner managing pending invites
  - **Acceptance Criteria:** Revoked invites no longer appear in list; new invite for non-existent user creates `org_invitations` row

- [ ] **Backend: update member permissions**
  - `PATCH /v1/orgs/{id}/members/{member_id}` — update role and/or permissions jsonb
  - **Permissions defined:** `data.read`, `subscriptions.manage`, `members.invite`, `keys.manage`, `billing.manage`
  - Role defaults: owner/admin = all; member = `["data.read","subscriptions.manage"]`

- [ ] **Backend: auto-join on signup + confirmation email**
  - In `POST /auth/signup`: after creating user record, check `org_invitations` for matching email where `accepted_at IS NULL`
  - If found: insert `org_memberships` row with role + permissions from invitation, set `accepted_at = NOW()`
  - Send confirmation email via Resend: "Welcome to {org_name} — you've joined as {role}"
  - **Acceptance Criteria:** User signs up → auto-joined → receives confirmation email

- [ ] **Frontend: EditMemberModal + revoke invitation**
  - Edit button on each non-owner member row + each pending invitation row
  - `EditMemberModal`: role dropdown + permission checkboxes (data.read, subscriptions.manage, members.invite, keys.manage, billing.manage) → calls `PATCH /v1/orgs/{id}/members/{id}`
  - Pending invitation rows shown in a "Pending Invitations" section with "Revoke" button
  - **Acceptance Criteria:** Admin can toggle each permission independently; pending invites visible + revocable

#### Phase 2A — API Key Auth & Consumer Data API ✅

- [x] **API key auth middleware** — `app/apikey_auth.py`: verify `hb_live_sk_*` keys, hash match, expiry/revoked check, update `last_used_at`. 6 tests.
- [x] **Consumer data endpoints** — `app/routes/data.py`: verticals (public), pull, adopt, dispute, deliveries, delivery items. 6 tests.
- [x] **Key verification** — `POST /v1/auth/verify-key` returns org_id + key_name.

#### Phase 2B — CLI ✅

- [x] **CLI** — `packages/cli/` using Bun. 11 commands: auth (set-key, whoami), verticals (list, topics), subscriptions (list), data (pull, adopt, dispute), billing (balance). Config in `~/.humanbased/config.json`. 9 tests.

#### Phase 2C — Documentation ✅

- [x] **API docs** — `packages/docs/index.md`: Getting Started, Authentication, API Reference (7 endpoints with curl examples), CLI Reference (all commands), Data Schema, Billing, Rate Limits. FastAPI auto-generates OpenAPI at `/docs` and `/redoc`.

#### Phase 3D — Production Fixes (2026-03-26)

- [ ] **Invitation email delivery + progress animation**
  - **Problem:** `RESEND_API_KEY` is empty in production `.env` — `send_invite_email` silently returns. Backend returns `email_sent: true` regardless.
  - **Solution Design:**
    - Backend: Return `email_sent: false` when key is empty; log a warning. Add `send_confirmation_email` call to notify the inviter after the invite is stored.
    - Frontend: Replace the static confirm dialog with a multi-step `InviteProgressModal` showing animated progress: (1) Confirm → (2) Sending invitation email → delivered ✓ (3) Sending confirmation to inviter → delivered ✓. Each step transitions after the API responds or after a timeout.
    - **Acceptance Criteria:** When `RESEND_API_KEY` is set: invitee gets invite email, inviter gets confirmation email, progress animation reflects real delivery. When key is empty: API returns `email_sent: false`, UI shows warning that email could not be sent.
  - **Files:** `packages/api/app/routes/members.py`, `packages/webapp/src/components/dashboard/Members.tsx`

- [ ] **Connection indicator aligned with actual status**
  - **Problem:** The green pulse dot next to the DataSourceToggle in Overview is hardcoded — it always pulses green in production mode regardless of actual REST API / Database / Realtime health.
  - **Solution Design:**
    - Lift `ConnectionStatus` health into a shared context (`useConnectionHealth`) so Overview can read aggregate status.
    - DataSourceToggle's green dot color reflects aggregate health: green = all connected, amber = checking, red = any error.
  - **Files:** `packages/webapp/src/lib/connectionHealth.ts` (new context), `packages/webapp/src/components/dashboard/Overview.tsx`, `packages/webapp/src/components/dashboard/ConnectionStatus.tsx`

- [ ] **Simulator based on real production data**
  - **Problem:** Mock generators use hardcoded names/categories. Simulated data doesn't match real production payload shapes and distribution.
  - **Solution Design:**
    - Add `GET /v1/verticals/{id}/sample-items?limit=50` endpoint that returns real `delivery_items` payloads for a vertical.
    - Frontend: On simulator start, fetch sample items per subscribed vertical. Simulator picks random real payloads and replays them with fresh IDs/timestamps instead of generating fake ones.
    - Fallback to existing mock generators if the API call fails or returns empty.
  - **Files:** `packages/api/app/routes/verticals.py`, `packages/webapp/src/components/dashboard/Overview.tsx`

#### Infrastructure Debt

- [ ] **Staging database isolation** — Staging and production currently share the same Supabase project (`uxafdddzhgdhsabkwmgw`). Test users created on staging appear in production. Fix: create a Supabase branch or separate project for staging, update Cloud Run staging env vars to point to the isolated instance.
- [ ] **Staging Stripe webhook** — Staging reuses the production `STRIPE_WEBHOOK_SECRET`, but Stripe webhooks are sent to the production API URL. Fix: create a separate Stripe webhook endpoint pointing to `staging.api.humanbased.ai` with its own secret.
- [ ] **Staging HuggingFace OAuth app** — HF OAuth requires a redirect URI matching the API domain. Staging needs its own HF OAuth app registered with redirect URI `https://staging.api.humanbased.ai/v1/auth/huggingface/callback` and separate `HF_CLIENT_ID`/`HF_CLIENT_SECRET` env vars on the staging Cloud Run service.

#### Phase 2D — Remaining Gaps

- [ ] **Subscriptions: Live vertical data** — Replace hardcoded verticals with `GET /v1/verticals` API data
- [ ] **Domain allowlist API** — Backend endpoints: `GET/PUT /v1/orgs/{id}/allowlist`, auto-join on signup
- [ ] **Org context from auth** — Replace hardcoded `ORG_ID = "demo-org"` with real org from user session
- [ ] **Backup email in Account Settings** — API + frontend
- [ ] **Usage tracking** — Update `last_used_at` on key use, track request counts

#### Phase 3A — Data Review UX ✅ (in progress)

- [ ] **Auto-adopt after 48 h**
  - **User:** Data consumer who doesn't want to manually review every item
  - **Acceptance Criteria:**
    - Any `delivery_items` row with `status = 'pending'` and `created_at < NOW() - INTERVAL '48 hours'` is automatically set to `status = 'adopted'`
    - A pg_cron job runs hourly: `UPDATE delivery_items SET status = 'adopted', reviewed_at = NOW() WHERE status = 'pending' AND created_at < NOW() - INTERVAL '48 hours'`
    - Frontend shows a countdown or "auto-adopts in Xh" hint per row (future — not in this sprint)
  - **Technical Notes:**
    - DB migration: add `status text NOT NULL DEFAULT 'pending'` and `reviewed_at timestamptz` to `delivery_items`
    - API: `POST /v1/data/items/{id}/adopt` and `dispute` must set `delivery_items.status`
    - pg_cron schedule: `0 * * * *` (every hour on the hour)
  - **Tests Required:** pg_cron fires; item older than 48h is auto-adopted; item < 48h is not touched

- [ ] **Confirm modal for Adopt / Dispute**
  - **User:** Data consumer reviewing incoming items
  - **Acceptance Criteria:**
    - Clicking Adopt or Dispute on a row opens a modal: "Adopt this item? You will be charged $X.XXX" / "Dispute this item? It will be sent for re-review — no charge."
    - Modal has Confirm and Cancel buttons
    - Cancel closes modal, leaves item status unchanged
    - Confirm proceeds with the action
  - **Technical Notes:** `ConfirmModal` component — generic title/body/confirm/cancel props. Rendered at `Overview` level.
  - **Tests Required:** Modal appears on click; cancel leaves item as pending; confirm calls handler

- [ ] **Dispute Pool section in dashboard**
  - **User:** Data consumer who wants to track disputed items separately
  - **Acceptance Criteria:**
    - Below the Live Data Stream, a second section "Dispute Pool" appears when any item has been disputed
    - Same table layout as Live Stream, but with red accent border (#EF4444) on the section, red header text, and red status badges
    - Disputed items are listed newest-first (disputes most recently filed at top)
    - No Adopt/Dispute action buttons — shows "disputed" status badge only
  - **Technical Notes:** `DisputePool` component — same column structure as `LiveStream`, red variant. `Overview` maintains separate `pendingItems` and `disputedItems` state arrays.
  - **Tests Required:** Dispute pool renders when disputedItems > 0; items are sorted newest-first

- [ ] **Row transition animation: incoming → dispute pool**
  - **User:** Data consumer reviewing items
  - **Acceptance Criteria:**
    - After confirming a dispute, the row in the Live Stream fades out (opacity 0 over 300ms)
    - After fade completes, the item is removed from Live Stream and inserted at the top of Dispute Pool
    - The newly inserted Dispute Pool row slides in from top (translateY -12px → 0) and fades in (opacity 0 → 1) over 300ms
    - Adopt confirmation: row fades out and is removed (no move to another section)
  - **Technical Notes:**
    - `transitioningId: string | null` state in `Overview`
    - `LiveStream` accepts `transitioningId` prop, applies `opacity-0 transition-opacity duration-300` to matching row
    - `DisputePool` applies `@keyframes slideIn` (translateY + opacity) to first item when `justAdded` prop is set
    - Timeout-based: after 300ms fade, state update moves item between arrays
  - **Tests Required:** Animation classes applied on dispute; item removed from pending after 300ms; item appears at top of disputed

### ✅ Done

- [x] **Project Scaffold** — Monorepo with packages/webapp (Bun+React+Tailwind), packages/api (Python FastAPI), shared types. Both servers verified.
- [x] **Auth — Sign Up / Sign In** — Supabase Auth integration. API: signup, signin, /me + JWT middleware. Frontend: AuthProvider with onAuthStateChange, route guarding, sign out.
- [x] **Onboarding Flow** — 3-step: org details → invite members (with Resend email) → API key.
- [x] **Dashboard Layout** — Top-navbar (no icons), avatar dropdown with Account/Org Settings + sign out. Codatta branding with company-logo.png.
- [x] **Dashboard Overview** — Stat cards + waffle chart (black gradient blocks, status borders, R-to-L flow, 5-min ticks) + live data stream table with adopt/dispute.
- [x] **API Key Management** — Full CRUD with masked keys, create modal, reveal/copy/revoke.
- [x] **Members Management** — Invite with email confirmation dialog, Resend integration, role management, remove.
- [x] **Subscriptions** — Vertical cards (hardcoded), active subscription management with pull/edit/cancel.
- [x] **Billing** — Balance cards, Stripe Checkout (test mode), transaction history.
- [x] **Account Settings** — Name edit, email (read-only).
- [x] **Organization Settings** — Name, slug, org email, backup email, domain allowlist management, danger zone delete.
- [x] **Design System** — Quantus 2025 palette (Blue Chalk bg, Haiti borders, DM Sans font), flat design, solid black outlines, sharp corners, parametrized via config.ts.

---

## Design Reference

- Design system: `DESIGN_SYSTEM.md`
- UI wireframes: `ui-design/consumer-api-essential.md`
- Screen exports (original): `ui-design/exports/`
- Screen exports (v2): `ui-design/exports-v2/`
- Pencil source: `packages/webapp/ui-design.pen`
- Logo asset: `assets/company-logo.png`
- Branding config: `packages/webapp/src/lib/config.ts`
- Style: Quantus Palette 2025 — Blue Chalk (#E8E0F0) bg, Haiti (#1B1034) text/borders, Electric Violet (#834DFB) accent
- Typography: DM Sans, 14px body
- Borders: 1.5px solid #1B1034, sharp corners (rounded-none)
- Cards: same bg as page, defined by solid borders

---

## Open Questions & Future Considerations

### Data Licensing after Adoption

When an org adopts a data item and pays for it, what rights do they receive?

- **License scope:** Is it a perpetual license, time-limited, or usage-limited (e.g., X API calls)?
- **License artifact:** Should we generate a license certificate or token per adopted item? Per batch? Per subscription?
- **Revocation on dispute refund:** When a dispute is accepted (refund), the org must lose access. How is this enforced technically? (API access revoked? Payload scrubbed from cache? Webhook notification to consumer's system?)
- **Re-licensing:** Can an org re-adopt a previously refunded item? At the same price or updated price?
- **Downstream usage tracking:** If the org uses adopted data in a derivative product, does the license cover that? Do we need usage telemetry?
- **Future-proof DB design:** Consider a `data_licenses` table: `(id, org_id, item_id, license_type, granted_at, expires_at, revoked_at, terms_version)`. This separates the financial event (transaction) from the legal event (license grant), enabling independent audit trails.

### Audit & Detailed Charge Reports

Orgs will need itemized billing reports for their finance/accounting teams.

- **Statement API:** `GET /v1/orgs/{org_id}/billing/statements?period=2026-03` — returns all transactions for a period with item-level detail (item ID, vertical, payload summary, price, action, timestamp).
- **Exportable formats:** CSV and PDF download. PDF should include org name, period, itemized table, subtotals by type (topup, freeze, settle, refund), and running balance.
- **Reconciliation fields:** Each transaction should carry enough metadata to trace back to the source: `item_id`, `vertical_id`, `subscription_id`, `stripe_session_id` (for topups). Consider adding these to the `transactions` table as nullable FK columns.
- **Retention policy:** How long do we retain transaction history? Regulatory requirements may dictate 7+ years for financial records.
- **Future-proof DB design:** Add `transactions.item_id uuid FK → delivery_items(id)` and `transactions.metadata jsonb` for extensible audit context without schema changes. The `metadata` field can carry vertical name, payload hash, subscription details — anything the statement renderer needs.
- **Access control:** Who can request statements? `billing.manage` permission holders? Org owner only? External auditors via a time-scoped read-only token?
