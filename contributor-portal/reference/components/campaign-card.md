# Component: Campaign Card

> The core unit of Campaign Browse. Answers three questions at a glance: Who is hiring? What's the work? What does it pay?

---

## Anatomy

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌──────┐  NVIDIA                            Trusted ✓      │
│  │      │  Technology / AI                                   │
│  │  ◉   │  4.9★  ·  100% on-time pay  ·  12 campaigns      │
│  └──────┘                                            (ORG)  │
│                                                              │
│  ─────────────────────────────────────────────────────────   │
│                                                              │
│  Housekeeping Video Collection                      (TITLE)  │
│                                                              │
│  Collect multi-angle video of humans performing household    │
│  activities for robotics training data.               (DESC) │
│                                                              │
│  🤖 Robotics    📹 Video    🏠 Indoor                (TAGS)  │
│                                                              │
│  📤 Supply ($2.50) · 🏷 Labeling ($1.50) · ✅ Agent  (TYPES) │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  💵  $2.50 / instance  ·  Fixed pay             (COMP) │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  3 tasks  ·  360 remaining  ·  ~2 weeks left        (STATS) │
│                                                              │
│  ✓ You qualify                            [View Campaign]    │
│                                                      (FOOT)  │
└──────────────────────────────────────────────────────────────┘
```

---

## Sections

### 1. Org Header (ORG)

See [org-card.md](org-card.md). Privacy-adapted.

| Element | Styling |
|---|---|
| Logo | `w-12 h-12 rounded-lg` |
| Name | `text-base font-semibold text-gray-900` |
| Industry | `text-xs text-gray-500` |
| Trust badge | `text-xs font-medium` — green for Trusted/Established, gray for Verified |
| Track record | `text-xs text-gray-400` — stars, payment %, campaign count |

### 2. Campaign Title (TITLE)

`text-lg font-semibold text-gray-900` — max 2 lines, truncated.

### 3. Description (DESC)

`text-sm text-gray-600` — max 2 lines, truncated. May be AI-masked per privacy tier.

### 4. Tags (TAGS)

Inline pill badges: frontier + modality + domain.

`bg-gray-100 text-gray-700 text-xs px-2.5 py-1 rounded-full font-medium`

### 5. Task Type Breakdown (TYPES)

**New element.** Shows task types with per-type pay rate. Addresses situation A1.

```
  📤 Supply ($2.50) · 🏷 Labeling ($1.50) · ✅ Agent
```

- Each task type badge (see [task-type-badge.md](task-type-badge.md)) with pay rate
- Agent-only tasks shown as `✅ Agent` (no pay — contributor doesn't do these)
- `text-xs text-gray-600`

### 6. Compensation Pill (COMP)

Prominent pay display. The highest per-type pay rate is featured.

| Model | Display |
|---|---|
| Fixed | `💵 $2.50 / instance · Fixed pay` |
| Royalty | `📈 Revenue share · est. $1.80/instance` |
| Hybrid | `🔀 $1.00 + royalty` |
| Bounty | `🎯 $500 milestone` |

**Styling:** `border border-green-200 bg-green-50 text-green-800 rounded-lg px-3 py-2`

### 7. Stats (STATS)

`text-xs text-gray-400` — task count, remaining instances, estimated time left.

### 8. Footer (FOOT)

| State | Display | Button |
|---|---|---|
| Qualified | `✓ You qualify` (green) | `[View Campaign]` black |
| Partially qualified | `⚠ 1 req not met` (amber) + what's missing | `[View Campaign]` gray outline |
| Not qualified | `✕ 3 reqs not met` (red, muted) | `[View Details]` text link |
| Already contributing | `● Contributing` (blue) + progress | `[Continue →]` black |

---

## Card Styling

```css
/* Card container */
.campaign-card {
  @apply border border-gray-200 rounded-xl p-5 hover:border-gray-400 
         hover:shadow-sm transition-all cursor-pointer;
}

/* Dimmed state (not qualified) */
.campaign-card--dimmed {
  @apply opacity-60;
}
```
