# Consumer API Essential — UI Design Spec

> Version: 1.0 | Date: 2026-03-22
> For: Pencil + Stitch design tool
> Domain: humanbased.ai

---

## Design System

- **Style**: Clean, minimal, developer-focused (like Stripe, Linear, Vercel dashboards)
- **Colors**: Black primary, white background, gray-50 surfaces, green/orange/red for status
- **Typography**: System font stack (-apple-system, Inter fallback), 14px body, 13px secondary
- **Spacing**: 8px grid, 16px padding on cards, 32px page margins
- **Radius**: 8px cards, 6px buttons/inputs
- **Logo**: Top-left on every page (company-logo.png, ~120x32px)

---

## Navigation Structure

```
Top bar (all pages):
  [Logo]                                    [Org Switcher ▼] [User Avatar ▼]

Sidebar (dashboard pages):
  Overview
  ─────────
  API Keys
  Subscriptions
  Data Explorer (future)
  ─────────
  Members
  Billing
  Settings
```

---

## Screen 1: Landing Page

**URL**: `/`

```
┌────────────────────────────────────────────────────────────────┐
│ [Logo]                              [Sign In]  [Get Started]  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│              HumanBased                                        │
│              Data API for crowd-sourced,                       │
│              quality-controlled data                           │
│                                                                │
│              [Get Started]    [Documentation]                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Screen 2: Sign Up

**URL**: `/auth/signup`

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│     [Logo]                                                     │
│                                                                │
│     Create your account                                        │
│     Start consuming quality data in minutes                    │
│                                                                │
│     Full name          [___________________________]           │
│     Email              [___________________________]           │
│     Password           [___________________________]           │
│                                                                │
│     [        Create account         ]                          │
│                                                                │
│     Already have an account? Sign in                           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Screen 3: Onboarding — Organization Details

**URL**: `/onboarding/org-details`

**Step indicator**: `1. Organization → 2. Invite Team → 3. API Key`

```
┌────────────────────────────────────────────────────────────────┐
│  [Logo]                                                        │
│  Set up your organization                                      │
│                                                                │
│  ● Organization  →  ○ Invite Team  →  ○ API Key               │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Organization logo                                       │  │
│  │  ┌─────────────────────┐                                 │  │
│  │  │                     │  Drag & drop or click to upload │  │
│  │  │   [Upload area      │  PNG, JPG, SVG. Max 2MB.        │  │
│  │  │    with icon]       │                                 │  │
│  │  │                     │                                 │  │
│  │  └─────────────────────┘                                 │  │
│  │                                                          │  │
│  │  Organization name *    [___________________________]    │  │
│  │  Slug *                 humanbased.ai/ [______________]  │  │
│  │  Website                [___________________________]    │  │
│  │                                                          │  │
│  │  Industry          [▼ Select...]   Company size [▼...]   │  │
│  │  Billing email     [___________________________]         │  │
│  │  Country           [___________________________]         │  │
│  │                                                          │  │
│  │  [              Continue              ]                   │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

**Logo upload details:**
- Drag & drop zone with dashed border
- Click to open file picker
- Accepts PNG, JPG, SVG, max 2MB
- Shows preview after upload (circular crop)
- Stored in Supabase Storage → URL saved to `organizations.logo_url`

---

## Screen 4: Onboarding — Invite Members

**URL**: `/onboarding/invite-members?org=xxx`

```
┌────────────────────────────────────────────────────────────────┐
│  [Logo]                                                        │
│  Set up your organization                                      │
│                                                                │
│  ✓ Organization  →  ● Invite Team  →  ○ API Key               │
│                                                                │
│  Invite team members                                           │
│  Add colleagues who need access. You can always do this later. │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  [email@company.com___________]  [▼ Admin ]  [×]        │  │
│  │  [email@company.com___________]  [▼ Member]  [×]        │  │
│  │  + Add another                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌ Roles ──────────────────────────────────────────────────┐   │
│  │ Admin: manage members, API keys, billing, subscriptions │   │
│  │ Member: view data, create subscriptions, pull data      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  [  Send invites & continue  ]          [ Skip ]               │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Screen 5: Onboarding — API Key

**URL**: `/onboarding/api-key?org=xxx`

```
┌────────────────────────────────────────────────────────────────┐
│  [Logo]                                                        │
│  Set up your organization                                      │
│                                                                │
│  ✓ Organization  →  ✓ Invite Team  →  ● API Key               │
│                                                                │
│  Your API key                                                  │
│  Save this key now — it won't be shown again.                  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ⚠️ hb_live_sk_aAIN6Xw-VdPiwW2wX-I2DBaMs31gBjpk [Copy] │  │
│  │                                                          │  │
│  │ Save this key securely. Store it in your environment     │  │
│  │ variables or secret manager.                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌ Quick start ────────────────────────────────────────────┐   │
│  │ npm install -g @humanbased/cli                          │   │
│  │ hb auth set-key hb_live_sk_aAIN...                      │   │
│  │ hb verticals list                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  [           Go to Dashboard            ]                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Screen 6: Dashboard — Overview

**URL**: `/dashboard`

```
┌────────────────────────────────────────────────────────────────┐
│ [Logo]                        [▼ Acme AI Labs]  [👤 Yi ▼]     │
├──────────┬─────────────────────────────────────────────────────┤
│          │                                                     │
│ Overview │  Welcome back, Yi                                   │
│ ──────── │                                                     │
│ API Keys │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│ Subscr.  │  │ $10,000  │  │ 2 keys   │  │ 1 sub    │          │
│ ──────── │  │ Balance  │  │ Active   │  │ Active   │          │
│ Members  │  └──────────┘  └──────────┘  └──────────┘          │
│ Billing  │                                                     │
│ Settings │  Recent Activity                                    │
│          │  ┌──────────────────────────────────────────────┐   │
│          │  │ Mar 22  API key "Production" created         │   │
│          │  │ Mar 22  Subscription to Crypto Annotation    │   │
│          │  │ Mar 21  Account funded: $10,000              │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
└──────────┴─────────────────────────────────────────────────────┘
```

---

## Screen 7: API Key Management

**URL**: `/dashboard/api-keys`

```
┌────────────────────────────────────────────────────────────────┐
│ [Logo]                        [▼ Acme AI Labs]  [👤 Yi ▼]     │
├──────────┬─────────────────────────────────────────────────────┤
│          │                                                     │
│ Overview │  API Keys                    [+ Create API Key]     │
│ ──────── │                                                     │
│ ●API Keys│  ┌ New key created! ────────────────────────────┐   │
│ Subscr.  │  │ ⚠️ hb_live_sk_xxx...xxx              [Copy] │   │
│ ──────── │  │ Save this key now. [Dismiss]                 │   │
│ Members  │  └──────────────────────────────────────────────┘   │
│ Billing  │                                                     │
│ Settings │  ┌──────────────────────────────────────────────┐   │
│          │  │ Name        Key            Status  Expires   │   │
│          │  │ ─────────────────────────────────────────────│   │
│          │  │ Production  hb_li••••••••  🟢active 87d left │   │
│          │  │             [👁] [📋]                [Revoke]│   │
│          │  │                                              │   │
│          │  │ CI/CD       hb_li••••••••  🟢active Never   │   │
│          │  │             [👁] [📋]                [Revoke]│   │
│          │  │                                              │   │
│          │  │ Old key     hb_li••••••••  🟠expired 3/1/26 │   │
│          │  │             [👁] [📋]                        │   │
│          │  │                                              │   │
│          │  │ Revoked     hb_li••••••••  🔴revoked         │   │
│          │  │             [👁] [📋]                        │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
│          │  ┌ Create API Key ──────────────────────────────┐   │
│          │  │ Name: [Production key____________]           │   │
│          │  │ Expiration:                                  │   │
│          │  │ [7d] [30d] [60d] [●90d] [1y] [Never] [Custom]│  │
│          │  │                                              │   │
│          │  │ [Create key]  [Cancel]                       │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
└──────────┴─────────────────────────────────────────────────────┘
```

**Key actions per row:**
- 👁 Eye: toggle reveal/hide full prefix
- 📋 Copy: copy prefix to clipboard (shows ✓ for 2s)
- Revoke: red text, confirmation dialog before action

**Status badges:**
- 🟢 `active` — green pill
- 🟠 `expired` — orange pill (auto-detected from `expires_at`)
- 🔴 `revoked` — red pill

---

## Screen 8: Member Management

**URL**: `/dashboard/members`

```
┌────────────────────────────────────────────────────────────────┐
│ [Logo]                        [▼ Acme AI Labs]  [👤 Yi ▼]     │
├──────────┬─────────────────────────────────────────────────────┤
│          │                                                     │
│ Overview │  Members                                            │
│ ──────── │                                                     │
│ API Keys │  ┌ Invite member ───────────────────────────────┐   │
│ Subscr.  │  │ [email@company.com____] [▼ Admin] [Add]      │   │
│ ──────── │  └──────────────────────────────────────────────┘   │
│ ●Members │                                                     │
│ Billing  │  ┌──────────────────────────────────────────────┐   │
│ Settings │  │ Member          Role       Permissions  │     │   │
│          │  │ ─────────────────────────────────────────────│   │
│          │  │ Yi Zhang        [▼ Owner]  Full access       │   │
│          │  │ yi@acme.ai                                   │   │
│          │  │ Joined Mar 21                                │   │
│          │  │                                              │   │
│          │  │ Anna Chen       [▼ Admin]  Full access       │   │
│          │  │ anna@acme.ai                  [Deactivate]   │   │
│          │  │ Joined Mar 22                 [Remove]       │   │
│          │  │                                              │   │
│          │  │ Bob Smith       [▼ Member] data.read,        │   │
│          │  │ bob@acme.ai               subscriptions...   │   │
│          │  │ Joined Mar 22                 [Deactivate]   │   │
│          │  │                               [Remove]       │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
│          │  ┌ Roles ───────────────────────────────────────┐   │
│          │  │ Owner:  full access, can't be removed        │   │
│          │  │ Admin:  manage members, keys, billing, subs  │   │
│          │  │ Member: read data, manage subscriptions      │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
└──────────┴─────────────────────────────────────────────────────┘
```

**Actions per member:**
- Role dropdown: change role (owner can't be changed)
- **Deactivate**: suspends access without removing (grayed row, can reactivate)
- **Remove**: permanently removes from org (confirmation dialog)
- Owner row has no action buttons

---

## Screen 9: Billing / Make Payment

**URL**: `/dashboard/billing`

```
┌────────────────────────────────────────────────────────────────┐
│ [Logo]                        [▼ Acme AI Labs]  [👤 Yi ▼]     │
├──────────┬─────────────────────────────────────────────────────┤
│          │                                                     │
│ Overview │  Billing                                            │
│ ──────── │                                                     │
│ API Keys │  ┌ Balance ─────────────────────────────────────┐   │
│ Subscr.  │  │                                              │   │
│ ──────── │  │  $8,420.00          $1,580.00     $10,000.00 │   │
│ Members  │  │  Available          Frozen        Total      │   │
│ ●Billing │  │                                              │   │
│ Settings │  │  [  Add funds  ]                             │   │
│          │  │                                              │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
│          │  ┌ Add Funds ───────────────────────────────────┐   │
│          │  │                                              │   │
│          │  │  Amount: [$______]                           │   │
│          │  │                                              │   │
│          │  │  Quick amounts:                              │   │
│          │  │  [$100] [$500] [$1,000] [$5,000] [$10,000]  │   │
│          │  │                                              │   │
│          │  │  [   Pay with Stripe   ]                     │   │
│          │  │                                              │   │
│          │  │  Powered by Stripe. Cards, bank, Apple Pay.  │   │
│          │  │                                              │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
│          │  Transaction History                                │
│          │  ┌──────────────────────────────────────────────┐   │
│          │  │ Date       Type     Amount     Balance  Ref  │   │
│          │  │ ──────────────────────────────────────────── │   │
│          │  │ Mar 22     freeze   -$17.35    $8,402   dlv_ │   │
│          │  │ Mar 22     settle   -$15.00    $8,420   dlv_ │   │
│          │  │ Mar 21     topup    +$10,000   $10,000  cs_  │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
└──────────┴─────────────────────────────────────────────────────┘
```

---

## Screen 10: Topic Subscriptions

**URL**: `/dashboard/subscriptions`

```
┌────────────────────────────────────────────────────────────────┐
│ [Logo]                        [▼ Acme AI Labs]  [👤 Yi ▼]     │
├──────────┬─────────────────────────────────────────────────────┤
│          │                                                     │
│ Overview │  Subscriptions              [+ New Subscription]    │
│ ──────── │                                                     │
│ API Keys │  ┌──────────────────────────────────────────────┐   │
│ ●Subscr. │  │ Crypto Account Annotation                    │   │
│ ──────── │  │ 🟢 Active · Pull mode · Since Mar 21         │   │
│ Members  │  │                                              │   │
│ Billing  │  │ Filters:                                     │   │
│ Settings │  │   min quality: 0.8                           │   │
│          │  │   chains: ethereum, base                     │   │
│          │  │   categories: dex, cex, lending              │   │
│          │  │                                              │   │
│          │  │ Stats: 347 items pending · $17.35 frozen     │   │
│          │  │                                              │   │
│          │  │ [Pull Data]  [Edit Filters]  [Cancel]        │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
│          │  ┌ New Subscription ─────────────────────────────┐  │
│          │  │                                               │  │
│          │  │ Vertical: [▼ Crypto Account Annotation     ]  │  │
│          │  │                                               │  │
│          │  │ Topics (select to filter, or leave empty for  │  │
│          │  │ all topics):                                  │  │
│          │  │ ☑ DeFi Protocol Labeling                      │  │
│          │  │ ☑ Exchange Identification                     │  │
│          │  │ ☐ Risk Flagging                               │  │
│          │  │ ☐ NFT & Gaming                                │  │
│          │  │                                               │  │
│          │  │ Mode: [● Pull]  [○ Push]                      │  │
│          │  │                                               │  │
│          │  │ Min quality score: [0.8____]                   │  │
│          │  │ Chains: [ethereum, base____________]           │  │
│          │  │ Categories: [dex, cex, lending______]          │  │
│          │  │                                               │  │
│          │  │ ☐ Auto-accept deliveries                      │  │
│          │  │                                               │  │
│          │  │ [   Create Subscription   ]  [Cancel]         │  │
│          │  └───────────────────────────────────────────────┘  │
│          │                                                     │
└──────────┴─────────────────────────────────────────────────────┘
```

---

## Screen 11: Settings

**URL**: `/dashboard/settings`

```
┌────────────────────────────────────────────────────────────────┐
│ [Logo]                        [▼ Acme AI Labs]  [👤 Yi ▼]     │
├──────────┬─────────────────────────────────────────────────────┤
│          │                                                     │
│ Overview │  Settings                                           │
│ ──────── │                                                     │
│ API Keys │  ┌ Organization ────────────────────────────────┐   │
│ Subscr.  │  │                                              │   │
│ ──────── │  │  Logo  [○ current logo]  [Change]            │   │
│ Members  │  │  Name  [Acme AI Labs___________]             │   │
│ Billing  │  │  Slug  humanbased.ai/[acme-ai__]             │   │
│ ●Settings│  │  Website [https://acme.ai______]             │   │
│          │  │  Industry [▼ AI / Machine Learning]          │   │
│          │  │  Size [▼ 11-50]                              │   │
│          │  │  Billing email [billing@acme.ai___]          │   │
│          │  │                                              │   │
│          │  │  [Save changes]                              │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
│          │  ┌ Danger Zone ─────────────────────────────────┐   │
│          │  │  Delete organization                         │   │
│          │  │  This will permanently delete the org and    │   │
│          │  │  all associated data, API keys, and          │   │
│          │  │  subscriptions.                              │   │
│          │  │                              [Delete org]    │   │
│          │  └──────────────────────────────────────────────┘   │
│          │                                                     │
└──────────┴─────────────────────────────────────────────────────┘
```

---

## Interaction Patterns

### Logo Upload (Onboarding + Settings)
1. Drag & drop zone with dashed border (128x128px area)
2. Click zone opens native file picker
3. Accept: PNG, JPG, SVG, max 2MB
4. On select: show circular preview with crop overlay
5. Upload to Supabase Storage bucket `org-logos`
6. Save URL to `organizations.logo_url`
7. Show in org switcher, sidebar, settings

### Member Actions
- **Invite**: email + role → if user exists, add membership immediately. If not, create pending invite.
- **Deactivate**: set membership status to `suspended`. User can't access org but record preserved.
- **Reactivate**: restore suspended membership to active.
- **Remove**: delete membership. Confirmation: "Remove [name] from [org]? They will lose access immediately."
- **Change role**: dropdown. Can't change own role. Can't demote the last owner.

### API Key Actions
- **Eye (reveal)**: toggle between `hb_li••••••••••••` and `hb_live_sk_aAIN6•••••••`
- **Copy**: copy prefix to clipboard. Button shows ✓ checkmark for 2 seconds.
- **Revoke**: red text link. Confirmation dialog: "Revoke [name]? This cannot be undone. Any systems using this key will immediately lose access."

### Stripe Payment
- Click "Add funds" → amount input with quick-select chips
- Click "Pay with Stripe" → redirects to Stripe Checkout
- On success → redirect back with `?status=success`, balance updated
- On cancel → redirect back with `?status=cancelled`

---

## Responsive Behavior

- **Desktop (>1024px)**: sidebar + content layout
- **Tablet (768-1024px)**: collapsible sidebar (hamburger menu)
- **Mobile (<768px)**: bottom tab navigation, full-width cards, stacked forms
