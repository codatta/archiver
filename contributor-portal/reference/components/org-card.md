# Component: Org Card

> The campaign creator's identity. Appears in campaign cards (compact) and campaign detail (hero). Fully adapted by privacy tier.

---

## Compact Variant (Campaign Card)

```
┌──────┐  NVIDIA                            Trusted ✓
│      │  Technology / AI
│  ◉   │  4.9★  ·  100% on-time pay  ·  12 campaigns
└──────┘
```

## Hero Variant (Campaign Detail)

```
┌──────────┐
│          │  NVIDIA                          Trusted ✓
│   ◉◉◉   │  Technology / AI / Robotics
│   ◉◉◉   │
└──────────┘  NVIDIA is pioneering accelerated computing...
                                          [View Profile →]

4.9★ rating  ·  12 campaigns  ·  100% on-time  ·  $284K paid
```

---

## Privacy Adaptation

| Element | Open | Shielded | Guarded | Sealed |
|---|---|---|---|---|
| Logo | Real | Verified badge | Category icon | Lock icon |
| Name | Real | "Verified AI Company" | "Technology Company" | "Anonymous Employer" |
| Industry | Full | Full | Category only | Hidden |
| Trust badge | Full tier | "Verified ✓" | Hidden | Hidden |
| Track record | Full stats | Campaign count only | Hidden | Hidden |
| Description | Full | Hidden | Hidden | Hidden |
| "View Profile" | Yes | Yes (limited) | No | No |

---

## Props

```typescript
interface OrgCardProps {
  org: {
    id: string;
    name: string;
    logo_url: string;
    industry: string;
    trust_tier: 'new' | 'verified' | 'established' | 'trusted';
    rating: number;
    on_time_pct: number;
    campaign_count: number;
    total_paid: number;
    description?: string;
  };
  privacy_tier: 'open' | 'shielded' | 'guarded' | 'sealed';
  variant: 'compact' | 'hero';
}
```

## Styling

| Element | Compact | Hero |
|---|---|---|
| Logo | `w-12 h-12 rounded-lg` | `w-16 h-16 rounded-xl` |
| Name | `text-base font-semibold` | `text-xl font-bold` |
| Container | None (inline in card) | `bg-gray-50 rounded-xl p-6` |
