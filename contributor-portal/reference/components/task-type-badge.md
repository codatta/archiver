# Component: Task Type Badge

> Visual indicator for task type. Used inline on campaign cards, task headers, and pipeline bars.

---

## Three Badges

| Type | Icon | Label | Use |
|---|---|---|---|
| Supply | 📤 | Supply | Contributor generates data from scratch |
| Labeling | 🏷 | Labeling | Contributor annotates an existing instance |
| Validation | ✅ | Validation | Contributor reviews a labeled instance |

---

## Variants

### Inline (campaign card, task header)

```
  📤 Supply ($2.50) · 🏷 Labeling ($1.50) · ✅ Agent
```

Styling: `text-xs text-gray-600` — icon + label + optional pay rate.

### Pill (standalone, filter)

```
  ┌──────────────┐
  │ 📤 Supply     │
  └──────────────┘
```

Styling: `bg-gray-100 text-gray-700 text-xs px-2.5 py-1 rounded-full font-medium`

### Icon-only (compact pipeline bar, small spaces)

Just the emoji: `📤` / `🏷` / `✅`

---

## With Pay Rate

When shown with per-type pay rate on the campaign card:

```
  📤 Supply ($2.50) · 🏷 Labeling ($1.50)
```

Agent-only tasks omit the pay rate:

```
  ✅ Agent
```

---

## Props

```typescript
interface TaskTypeBadgeProps {
  type: 'supply' | 'labeling' | 'validation';
  variant: 'inline' | 'pill' | 'icon';
  pay_rate?: { amount: number; currency: string };
  executor?: 'human' | 'agent';  // if agent, show "Agent" instead of pay
}
```
