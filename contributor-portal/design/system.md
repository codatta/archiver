# Humanbased Developer Portal — Design System

> **Source of truth for all frontend UI decisions.** Derived from the live implementation in `packages/webapp/src` and verified against UX screenshots in `ux-tests/`. Update this document whenever a new pattern is established in code.

Clean, sharp, typographic. White canvas with dark-purple anchors and vibrant-purple accents.

---

## Core Principles

1. **Sharp over soft** — `rounded-none` on all inputs, buttons, cards, and modals. Rounded shapes (`rounded-full`) reserved for circular indicators only (status dots, avatars, spinners).
2. **White canvas, purposeful color** — Background is pure white. Color is reserved for brand accent, status semantics, and interaction states — never decoration.
3. **Typographic hierarchy** — DM Sans at multiple weights carries the structure. Size and weight define importance; color is secondary.
4. **Bold borders, minimal shadows** — `1.5px solid #1B1034` defines all structure. Shadows only on modals (`shadow-xl`). Cards rely on border contrast, not elevation.
5. **Consistent density** — inputs and buttons share `py-2.5` vertical rhythm. Labels sit `mb-1.5` above their fields. Table rows use `px-5 py-4`.

---

## Theme Constants

All design decisions are encoded in `src/lib/config.ts`. Import `THEME` instead of hardcoding hex values.

```typescript
// src/lib/config.ts
export const THEME = {
  bg:            "#FFFFFF",
  surface:       "#FFFFFF",
  accent:        "#834DFB",   // vibrant purple — interactive accent
  accentHover:   "#7340E0",   // darker purple on hover
  accentLight:   "#F0EBFF",   // light purple background tint
  btnBg:         "#1B1034",   // primary button / card border
  btnHover:      "#2A1D4E",   // primary button hover
  textPrimary:   "#1B1034",   // headings, labels, strong text
  textSecondary: "#5C5470",   // secondary / descriptive text
  textMuted:     "#9890A8",   // de-emphasised / disabled text
  border:        "#1B1034",   // universal border color
  borderWidth:   "1.5px",     // universal border width
  danger:        "#EF4444",   // destructive actions, errors
  avatarBg:      "#834DFB",   // avatar background
} as const;

export const BRAND = {
  name:    "Humanbased",
  logo:    "/assets/company-logo.png",
  version: "0.2.1",
} as const;
```

---

## Color Tokens

### Brand palette

| Token | Hex | Usage |
|---|---|---|
| Brand primary | `#1B1034` | Button bg, border, primary text, code bg |
| Brand accent | `#834DFB` | Focus rings, hover links, interactive highlights, spinners |
| Accent hover | `#7340E0` | Accent color on hover |
| Accent light | `#F0EBFF` | Accent section backgrounds, OTP code block bg, badge bg |
| Primary hover | `#2A1D4E` | Primary button hover state |

### Text

| Token | Value | Usage |
|---|---|---|
| `textPrimary` | `#1B1034` | Headings, labels, table cell text |
| `textSecondary` | `#5C5470` | Page subtitles (e.g. "Welcome back to Humanbased") |
| `textMuted` | `#9890A8` | Timestamps, metadata, empty-state icons |
| Tailwind `gray-400` | `#9CA3AF` | Placeholder text, "OR" divider, secondary captions |
| Tailwind `gray-500` | `#6B7280` | Helper text |

### Backgrounds

| Token | Value | Usage |
|---|---|---|
| Page / surface | `#FFFFFF` | All backgrounds — no off-white tints |
| Hover row | `bg-gray-50` | Table row hover, secondary button hover |
| Code block | `#1B1034` | Dark code / API key display areas |
| OTP / accent block | `#F0EBFF` | OTP code display, accent-tinted surfaces |

### Status / semantic

| Meaning | Color | Tailwind classes |
|---|---|---|
| Success / adopted / available | `#22C55E` | `text-green-500`, `text-emerald-600`, `bg-green-50`, `border-green-200` |
| Error / danger / taken | `#EF4444` | `text-red-500`, `bg-red-50`, `border-red-200` |
| Warning | `#F59E0B` | `text-amber-600`, `bg-amber-50`, `border-amber-400` |
| Info | `#6366F1` | `text-indigo-500` |
| Checking / muted / inactive | `#9890A8` | `text-gray-400` |

### Borders

| Context | Value |
|---|---|
| All cards, inputs, modals, tables | `1.5px solid #1B1034` (`border-[1.5px] border-[#1B1034]`) |
| Subtle internal dividers | `#E8E5ED` or `#D4CDE0` |
| Danger borders | `border-red-200` |
| Alert (API key) borders | `border-amber-400 border-2` |
| Dashed (upload / placeholder) | `border-dashed border-[#1B1034]` |

---

## Typography

### Font

- **Primary:** `DM Sans` — imported from Google Fonts with full optical-size and weight range.
- **Fallback stack:** `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- **Monospace:** Tailwind default — `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas`
- **Base body size:** `14px` (set in `src/styles.css`)

### Scale

| Class | Size | Usage |
|---|---|---|
| `text-[10px]` / `text-[11px]` | 10–11px | Tiny timestamps, metadata |
| `text-xs` | 12px | Captions, badges, table headers |
| `text-sm` | 14px | Body text, labels, buttons — **default** |
| `text-base` | 16px | Emphasis paragraphs |
| `text-lg` | 18px | Section titles |
| `text-xl` | 20px | Card titles |
| `text-2xl` | 24px | Page headings (e.g. "Sign in", "Create your account") |
| `text-4xl` | 36px | Hero stats / metrics |

### Weights

| Class | Weight | Usage |
|---|---|---|
| `font-normal` | 400 | Default body text |
| `font-medium` | 500 | Buttons, input values, interactive labels |
| `font-semibold` | 600 | Section headers, table column headers |
| `font-bold` | 700 | Page titles, stat numbers, email headings |
| `font-mono` | — | API keys, OTP codes, code snippets |

### Letter spacing

- `tracking-wide` / `tracking-wider` — uppercase category labels, column headers, OR divider
- Default (`tracking-normal`) — all other text

---

## Spacing & Layout

### Vertical rhythm (form fields)

```
[label]      text-sm font-medium text-[#1B1034] mb-1.5
[input]      px-4 py-2.5
[hint/error] text-xs mt-0.5 (text-gray-400 or text-red-500)
```

### Common padding values

| Context | Classes |
|---|---|
| Standard input / button | `px-4 py-2.5` |
| Primary CTA button | `px-5 py-2.5` |
| Small action button | `px-3 py-1.5` |
| Card / panel | `p-5` or `p-6` |
| Table cell | `px-5 py-4` |
| Table header cell | `px-5 py-3` |
| Modal header | `px-8 pt-8 pb-7` |
| Modal body | `px-6 py-4` |
| Modal footer | `px-6 pb-5` |
| Dense list item | `px-4 py-2.5` |

### Common gap values

- `gap-1`, `gap-2`, `gap-3`, `gap-4` — flex row gaps
- `space-y-2`, `space-y-4`, `space-y-6` — stacked form fields
- `gap-3` — button group inside modal footer

### Layout containers

- Auth / forms: `max-w-sm` centered
- Modals: `max-w-sm` (standard), `max-w-md` (larger content)
- Content grids: `grid grid-cols-2`, `grid grid-cols-3` with `gap-4`

---

## Page Layouts

### Auth pages (sign-in / sign-up)

Confirmed visually from `ux-tests/oauth-signin/`. Centered single-column layout.

```
[Logo mark — top left of form, not nav]
[Heading — text-2xl font-bold text-[#1B1034]]
[Subtitle — text-sm text-[#5C5470] mt-1]

[OAuth button — Continue with GitHub]
[OAuth button — Continue with HuggingFace]

[OR divider]

[Email label + input]
[Password label + input]   ← sign-in only
[Primary CTA — full width]

[Footer link — "Don't have an account? Sign up"]
```

- Logo mark: small rounded-square brand icon (`/assets/company-logo.png`), ~32–40px, top of form block
- Form container: `max-w-sm mx-auto` with vertical `space-y-4`
- OAuth buttons appear before email/password — OAuth is the primary path
- Footer link: muted gray text + vibrant purple link (see Auth footer link component)

### Onboarding pages

Confirmed from `ux-tests/onboarding-get-started/`. Full-page with top nav bar + centered content.

- Top-left: small logo mark in nav bar
- Onboarding stepper immediately below heading
- Content centered, `max-w-2xl` or similar
- Final step ("Get Started") shows action card grid (see Action cards)

---

## Components

### Buttons

#### Primary

```tsx
className="px-5 py-2.5 bg-[#1B1034] text-white rounded-none text-sm font-medium hover:bg-[#2A1D4E] disabled:opacity-50"
```

#### Full-width CTA (auth / onboarding)

```tsx
className="w-full py-2.5 bg-[#1B1034] text-white rounded-none text-sm font-medium hover:bg-[#2A1D4E] disabled:opacity-50"
```

When loading, replace label with inline spinner:
```tsx
<span className="inline-block w-4 h-4 rounded-full border-2 border-t-transparent animate-spin"
  style={{ borderColor: `${THEME.accent} transparent ${THEME.accent} ${THEME.accent}` }} />
```

#### Secondary (outline)

```tsx
className="px-4 py-2.5 text-sm border-[1.5px] border-[#1B1034] rounded-none bg-white hover:bg-gray-50 disabled:opacity-50"
```

#### Ghost (text only)

```tsx
// Accent — primary ghost action
className="text-sm font-medium text-[#834DFB] hover:text-[#7340E0]"
// Muted — secondary / cancel ghost
className="text-sm text-gray-400 hover:text-[#1B1034]"
```

#### Skip link

Visually confirmed: used below primary CTA in forms where the step is optional (e.g. org creation, invite team).

```tsx
<div className="text-center mt-2">
  <button
    type="button"
    className="text-sm text-gray-400 hover:text-[#1B1034] hover:underline underline-offset-2"
  >
    Skip for now
  </button>
</div>
```

- Centered, below the primary button
- `text-sm text-gray-400` — clearly secondary, not competing with CTA
- Underline appears only on hover

#### OAuth / third-party

```tsx
className="w-full py-2.5 px-4 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm font-medium flex items-center justify-center gap-2 hover:bg-gray-50"
```

Icon on left (`width=18 height=18`), label text centered. Two providers: GitHub (inline SVG) and HuggingFace (emoji 🤗 or image icon).

#### Danger (destructive)

```tsx
// Filled:
className="px-4 py-2 text-sm bg-red-600 text-white rounded-none hover:bg-red-700 disabled:opacity-50"
// Outline:
className="px-4 py-2 text-sm border border-red-200 text-red-600 rounded-none hover:bg-red-50"
```

**Rules for all buttons:**
- Corners: always `rounded-none`
- Disabled: always `disabled:opacity-50` — no color/layout change
- No icon-only buttons without accessible label

---

### Inputs & Forms

#### Standard input class constant

```tsx
const inputCls =
  "w-full px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none " +
  "text-sm placeholder:text-gray-400 focus:outline-none " +
  "focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";
```

Apply to `<input>`, `<textarea>`, `<select>`.

#### Label

```tsx
<label className="block text-sm font-medium text-[#1B1034] mb-1.5">
  Field name
</label>
```

#### Error message

```tsx
<p className="text-xs text-red-500 mt-0.5">Error text</p>
```

#### Helper / hint

```tsx
<p className="text-xs text-gray-400 mt-0.5">Hint text</p>
```

#### Input with inline action (show/hide password)

Visually confirmed in password strength screenshots: "Show" toggle sits right-aligned inside the input border.

```tsx
<div className="relative">
  <input type={show ? "text" : "password"} className={inputCls} />
  <button
    type="button"
    onClick={() => setShow(s => !s)}
    className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-400 hover:text-[#1B1034]"
  >
    {show ? "Hide" : "Show"}
  </button>
</div>
```

#### Input with text prefix (slug field)

Visually confirmed in org availability screenshots: "humanbased.ai/" renders as gray text before the input, all within the same visual row — but the border wraps only the input, not the prefix.

```tsx
<div className="flex items-center gap-1">
  <span className="text-sm text-gray-400 whitespace-nowrap">humanbased.ai/</span>
  <input className={inputCls.replace("w-full", "flex-1")} placeholder="your-slug" />
</div>
```

#### Availability indicator (real-time check)

Visually confirmed: appears directly below the input, `mt-1`, replaces or accompanies the hint slot.

```tsx
// Checking (gray):
<p className="text-xs text-gray-400 mt-1">Checking…</p>
// Available (green checkmark prefix):
<p className="text-xs text-emerald-600 mt-1">✓ Available</p>
// Taken (red, no prefix icon):
<p className="text-xs text-red-500 mt-1">Already in use</p>
```

#### Checkbox

```tsx
<input type="checkbox" className="accent-[#834DFB]" />
```

#### File / drag-drop upload area

```tsx
className="w-20 h-20 border border-dashed border-[#1B1034] rounded-none flex flex-col items-center justify-center text-gray-400 text-xs overflow-hidden hover:border-[#834DFB] transition-colors"
```

#### OR divider

Visually confirmed between OAuth buttons and email/password form on auth pages.

```tsx
<div className="flex items-center gap-3 my-2">
  <div className="flex-1 h-px bg-gray-200" />
  <span className="text-xs text-gray-400 tracking-wider uppercase">or</span>
  <div className="flex-1 h-px bg-gray-200" />
</div>
```

#### Auth footer link

```tsx
<p className="text-center text-sm text-gray-400 mt-4">
  Don't have an account?{" "}
  <a href="/signup" className="text-[#834DFB] font-medium hover:text-[#7340E0]">
    Sign up
  </a>
</p>
```

Gray base text + vibrant purple link, `font-medium`. Used for all auth page cross-links.

---

### Password Strength Module

Located at `src/lib/password/`. Visually confirmed across 5 states (`ux-tests/password-strength/`).

#### Anatomy

```
[Password label]
[Input with Show/Hide toggle inside]
[Strength meter — 4 equal segments]
[Strength label — "Too weak" / "Fair" / "Strong"]
[Rules list — 6 rules with ✓/✗]

[Confirm password label]           ← appears after first field
[Confirm input with Show/Hide]
["Passwords match" / "Passwords do not match"]
```

#### Strength meter

4 equal horizontal segments below the input, gap between them. Color fills left-to-right based on score:

| Score | Segments filled | Color |
|---|---|---|
| 0 (empty) | 0 | All gray (`bg-gray-200`) |
| 1 (weak) | 1 | Red (`bg-red-400`) |
| 2 (fair) | 2 | Amber (`bg-amber-400`) |
| 3 (good) | 3 | Teal/green (`bg-teal-400`) |
| 4 (strong) | 4 | Green (`bg-green-500`) |

```tsx
<div className="flex gap-1 mt-2">
  {[0,1,2,3].map(i => (
    <div
      key={i}
      className={`flex-1 h-1 rounded-full transition-colors ${
        i < score ? strengthColor : "bg-gray-200"
      }`}
    />
  ))}
</div>
<p className="text-xs text-gray-400 mt-1">{strengthLabel}</p>
```

Note: the meter segments use `rounded-full` (pill shape) — the only bar/progress element to do so.

#### Rules list

Six rules, each with a pass/fail indicator. Visually: ✗ in red, ✓ in green, text color matches icon color.

```tsx
<ul className="mt-2 space-y-1">
  {rules.map(rule => (
    <li key={rule.id} className={`flex items-center gap-1.5 text-xs ${rule.pass ? "text-green-600" : "text-red-500"}`}>
      <span>{rule.pass ? "✓" : "✗"}</span>
      {rule.label}
    </li>
  ))}
</ul>
```

Rules: at least 10 characters · at least one uppercase · at least one lowercase · at least one number · at least one special character · no spaces.

#### Match indicator

```tsx
// Match:
<p className="text-xs text-green-600 mt-1">Passwords match</p>
// No match:
<p className="text-xs text-red-500 mt-1">Passwords do not match</p>
```

---

### Stepper / Progress Indicator

Two variants used in the app — confirmed visually.

#### Sign-up progress (bottom of auth form)

Three steps shown as numbered circles connected by lines. Used at the bottom of the sign-up form.

```
● Verify email  ——  ○ Set up profile  ——  ○ Start building
```

- Active/complete step: filled dark circle (`bg-[#1B1034]`) with white checkmark or number
- Upcoming step: outlined circle (`border-2 border-gray-300`), gray number
- Connector: thin line (`h-px bg-gray-200 flex-1`)

```tsx
<div className="flex items-center gap-2 mt-6">
  {steps.map((step, i) => (
    <React.Fragment key={step.id}>
      <div className="flex flex-col items-center gap-1">
        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
          step.done ? "bg-[#1B1034] text-white" : "border-2 border-gray-300 text-gray-400"
        }`}>
          {step.done ? "✓" : i + 1}
        </div>
        <span className="text-[10px] text-gray-400 whitespace-nowrap">{step.label}</span>
      </div>
      {i < steps.length - 1 && <div className="flex-1 h-px bg-gray-200 mb-3" />}
    </React.Fragment>
  ))}
</div>
```

#### Onboarding top stepper

Horizontal tabs above the onboarding form. Current step is highlighted; completed steps show a checkmark.

```
✓ Organization  ·  ✓ Invite Team  ·  ③ Get Started
```

```tsx
<div className="flex items-center gap-3 text-sm mb-6">
  {steps.map((step, i) => (
    <React.Fragment key={step.id}>
      <span className={`flex items-center gap-1 ${
        step.active ? "text-[#1B1034] font-medium" :
        step.done   ? "text-[#834DFB]" : "text-gray-400"
      }`}>
        {step.done ? <span className="text-[#834DFB]">✓</span> : <span>{i + 1}</span>}
        {step.label}
      </span>
      {i < steps.length - 1 && <span className="text-gray-300">·</span>}
    </React.Fragment>
  ))}
</div>
```

---

### Cards & Surfaces

#### Standard card

```tsx
className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-5"
```

#### Stat / metric card

```tsx
<div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6">
  <p className="text-4xl font-bold text-[#1B1034]">{value}</p>
  <p className="text-sm text-gray-400 mt-1">{label}</p>
</div>
```

#### Interactive card (hover elevation)

```tsx
className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-5 hover:shadow-lg transition-shadow cursor-pointer"
```

#### Get-started action card

Visually confirmed in `ux-tests/onboarding-get-started/`. Two-column grid of cards shown after onboarding completion. Each has a screenshot thumbnail, title, description, and purple arrow link.

```tsx
<div className="grid grid-cols-2 gap-4">
  <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none overflow-hidden hover:shadow-lg transition-shadow">
    {/* thumbnail — screenshot of destination page */}
    <div className="aspect-[4/3] bg-gray-50 overflow-hidden">
      <img src={thumbnail} alt="" className="w-full h-full object-cover object-top" />
    </div>
    {/* content */}
    <div className="p-4">
      <p className="text-sm font-semibold text-[#1B1034] mb-1">{title}</p>
      <p className="text-xs text-gray-400 mb-3">{description}</p>
      <a href={href} className="text-xs font-medium text-[#834DFB] hover:text-[#7340E0]">
        {cta} →
      </a>
    </div>
  </div>
</div>
```

- Thumbnail fills top of card with `aspect-[4/3]`
- Arrow (`→`) is part of the link text, not a separate icon
- Purple accent link is the only interactive element in the card

#### Code / dark surface

```tsx
className="bg-[#1B1034] text-gray-100 rounded-none p-4 text-xs font-mono space-y-1"
```

#### API key / secret alert card

```tsx
<div className="bg-amber-50 border-2 border-amber-400 rounded-none p-4">
  <code className="text-sm font-mono break-all text-amber-900">{key}</code>
</div>
```

---

### Modals & Dialogs

#### Overlay

```tsx
<div
  className="fixed inset-0 z-50 flex items-center justify-center px-4"
  style={{ background: "rgba(27, 16, 52, 0.45)" }}
>
```

#### Modal container

```tsx
<div className="w-full max-w-sm bg-white border-[1.5px] border-[#1B1034] rounded-none shadow-xl">
  {/* header */}
  <div className="px-8 pt-8 pb-7 text-center">…</div>
  {/* body */}
  <div className="px-6 py-4">…</div>
  {/* footer */}
  <div className="px-6 pb-5 flex gap-3 justify-end">
    <button /* secondary/cancel */>Cancel</button>
    <button /* primary/confirm */>Confirm</button>
  </div>
</div>
```

**Rules:**
- Overlay: `rgba(27,16,52,0.45)` standard, `rgba(27,16,52,0.5)` heavier variant
- Shadow: always `shadow-xl`
- Button order: cancel left, confirm right — `justify-end gap-3`
- Width: `max-w-sm` default, `max-w-md` for content-heavy modals

---

### Tables

#### Wrapper

```tsx
<div className="bg-white border-[1.5px] border-[#1B1034] rounded-none overflow-hidden">
  <table className="w-full">
```

#### Header row

```tsx
<thead>
  <tr className="text-xs text-gray-400 text-left">
    <th className="px-5 py-3 font-medium">Column</th>
  </tr>
</thead>
```

#### Body row

```tsx
<tr className="border-t border-[#1B1034] hover:bg-gray-50">
  <td className="px-5 py-4 text-sm text-[#1B1034]">…</td>
  <td className="px-5 py-4 text-sm text-gray-400">…</td>
</tr>
```

Row entrance animation: `rowSlideIn` (0.3s ease) — defined in `src/styles.css`.

#### Empty table state

```tsx
<tr>
  <td colSpan={n} className="px-5 py-8 text-center text-sm text-gray-400">
    No items yet.
  </td>
</tr>
```

---

### Badges & Tags

#### Standard label badge

```tsx
<span className="inline-block px-2 py-0.5 text-xs rounded-sm"
  style={{ background: "#E8E0F0", color: "#1B1034" }}>
  label
</span>
```

#### Accent badge

```tsx
<span className="inline-block px-2 py-0.5 text-xs rounded-sm"
  style={{ background: THEME.accentLight, color: THEME.accent }}>
  label
</span>
```

#### Status dot

```tsx
<span className="inline-block w-2 h-2 rounded-full"
  style={{ background: "#22C55E" /* or #EF4444, #F59E0B */ }} />
```

---

### Empty States

```tsx
<div className="text-center py-8">
  <i className="fi fi-ss-inbox text-3xl mb-3" style={{ color: THEME.textMuted }} />
  <p className="text-sm text-gray-400">No items yet.</p>
</div>
```

---

### Loading States

#### Inline spinner (inside button while submitting)

```tsx
<span className="inline-block w-4 h-4 rounded-full border-2 border-t-transparent animate-spin"
  style={{ borderColor: `${THEME.accent} transparent ${THEME.accent} ${THEME.accent}` }} />
```

#### Section loading

```tsx
<p className="text-xs text-gray-300">Loading…</p>
```

---

## Email Template Design

Visually confirmed across all 8 templates in `ux-tests/email-template/`.

### Anatomy

```
[black outer background]
  ┌─────────────────────────────────┐  ← white card, 1.5px #1B1034 border, sharp corners
  │ [logo mark — top left, ~32px]   │
  │                                 │
  │ Hi [Name],                      │  ← greeting, body text color
  │                                 │
  │ ## Heading                      │  ← bold, large, #1B1034
  │                                 │
  │ Body paragraph text…            │
  │                                 │
  │ ┌─────────────────────────────┐ │  ← OTP block: #F0EBFF bg
  │ │   8  4  7  2  9  1          │ │  ← monospace, bold, large, letter-spaced
  │ └─────────────────────────────┘ │
  │                                 │
  │ Muted helper text (expires…)    │  ← text-gray-400 / muted
  │                                 │
  │ [  CTA button — full width  ]   │  ← #1B1034 bg, white text, sharp
  │                                 │
  ├─────────────────────────────────┤  ← 1.5px divider line
  │ [logo mark — centered, ~20px]   │
  │ humanbased.ai                   │  ← accent/dark link
  │ Codatta PTE LTD                 │  ← gray-400, small
  └─────────────────────────────────┘
```

### Key properties

- **Outer background:** pure black (`#000000`)
- **Card:** white, `1.5px solid #1B1034` border, sharp corners, `max-width: 520px` centered
- **Greeting:** "Hi [Name]," or "Hi there," — `text-sm` body color, above heading
- **Heading:** `font-bold`, `~22px`, `#1B1034`
- **OTP code block:** `background: #F0EBFF`, `font-family: monospace`, `font-size: 32px`, `font-weight: 700`, `letter-spacing: 0.3em`, centered
- **CTA button:** `background: #1B1034`, white text, `rounded-none`, no pill shape
- **Footer divider:** `1.5px solid #1B1034` horizontal line
- **Footer:** centered — logo mark (~20px) → `humanbased.ai` link → `Codatta PTE LTD` in gray
- **Logo:** symbol-only mark (no wordmark) from CDN

---

## Borders & Radius

| Rule | Value |
|---|---|
| All cards, inputs, buttons, modals | `rounded-none` |
| Status dots, avatars, spinners | `rounded-full` |
| Strength meter segments | `rounded-full` (exception — pill bar segments) |
| Badges / tags | `rounded-sm` |
| Upload drop zones | `rounded-none border-dashed` |

**Never use `rounded-md`, `rounded-lg`, or `rounded-xl` on new components.** These appear in older code and are not the current standard.

---

## Shadows

| Context | Class |
|---|---|
| Default (cards, inputs) | none |
| Interactive card on hover | `hover:shadow-lg transition-shadow` |
| Modal | `shadow-xl` |
| Modal (heavy) | `shadow-2xl` |

---

## Icons

### Flaticon Uicons (primary set)

```tsx
<i className="fi fi-ss-{icon-name}" style={{ color: THEME.textMuted }} />
```

Size controlled by parent `text-*` class. Color via `style={{ color }}` or text-color class.

| Icon | Name |
|---|---|
| Lock / secret | `fi-ss-lock` |
| API key | `fi-ss-key` |
| Inbox / empty | `fi-ss-inbox` |
| Sandbox / lab | `fi-ss-flask` |
| Production | `fi-ss-bolt` |
| Team | `fi-ss-users` |
| Email | `fi-ss-envelope` |
| Organisation | `fi-ss-building` |
| User | `fi-ss-user` |
| Wallet | `fi-ss-wallet` |
| Celebration | `fi-ss-party-horn` |

### Inline SVG (OAuth providers)

```tsx
const GitHubIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">…</svg>
);
```

Color inherits from parent via `fill="currentColor"`.

### Image icons

```tsx
<img src="/icons/huggingface.svg" alt="" width={20} height={20} aria-hidden="true" />
```

### Emoji icons

Used in domain/vertical labels (🏦 👕 🍲 📄 ⚖️ ✏️ 🎙 🌍). Prefer Flaticon for interactive UI; emoji for data display labels only.

---

## Interaction Patterns

### Hover

| Target | Treatment |
|---|---|
| Primary button | `hover:bg-[#2A1D4E]` |
| Secondary / outline button | `hover:bg-gray-50` |
| Ghost / text link | `hover:text-[#7340E0]` (accent on accent), `hover:text-[#1B1034]` (gray on muted) |
| Danger text link | `hover:text-red-500` |
| Interactive card | `hover:shadow-lg transition-shadow` |
| Skip link | `hover:text-[#1B1034] hover:underline underline-offset-2` |
| Arrow link (`→`) | `hover:text-[#7340E0]` |
| Icon | `hover:opacity-80` |

### Focus (inputs)

```
focus:outline-none
focus:border-[#834DFB]
focus:ring-2 focus:ring-[#834DFB]/10
```

Focus ring uses `[#834DFB]/10` — very subtle halo. Remove browser default with `focus:outline-none`.

### Disabled

```
disabled:opacity-50
```

No other treatment. Do not change color, border, or layout for disabled states.

### Selected / active toggle

```tsx
// Selected:
className="bg-[#1B1034] text-white border-[#1B1034]"
// Unselected:
className="bg-white text-[#1B1034] border-[#1B1034]"
```

### Transitions

- `transition-colors` — color-changing elements (hover color shifts)
- `transition-shadow` — hover-elevation cards
- `transition-opacity` — show/hide elements
- Custom animations in `src/styles.css`:
  - `rowSlideIn` — 0.3s ease (new table rows)
  - `fadeSlideUp` — 0.25s ease (modal entrance)

---

## Dark Mode

**Not implemented.** The portal is light-mode only. Do not add `dark:` prefixed classes. The email renderer has `prefers-color-scheme` media queries for email clients only — that does not apply to the webapp.

---

## Anti-patterns

| Anti-pattern | Correct alternative |
|---|---|
| `rounded-md` / `rounded-lg` on any new component | `rounded-none` |
| `border` (1px) on structural containers | `border-[1.5px] border-[#1B1034]` |
| `border-gray-300` as primary border | `border-[#1B1034]` |
| Arbitrary `bg-purple-*` | `bg-[#834DFB]` or `bg-[#F0EBFF]` via `THEME` |
| `px-6 py-3` on a standard button | `px-5 py-2.5` (primary) or `px-4 py-2.5` (secondary) |
| Custom shadow on cards | No shadow — border defines structure |
| `focus:ring-purple-500` | `focus:ring-[#834DFB]/10` |
| Hardcoded hex without THEME reference | Import and use `THEME.*` from `src/lib/config.ts` |
| "Skip" link styled as a ghost button | Plain text, centered, `text-gray-400`, underline on hover only |
| Arrow links using `<button>` | Use `<a>` with `text-[#834DFB]` and literal `→` in text |
| Wordmark logo in emails | Symbol-only mark (`symbol_black.png`) |