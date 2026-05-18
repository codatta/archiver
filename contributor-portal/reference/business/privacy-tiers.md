# Privacy Tiers

> Campaign creators control how much of their identity and campaign details are visible to contributors. Higher privacy = smaller contributor pool + higher cost.

---

## Four Tiers

| Tier | k-anonymity | Org identity | Campaign brief | Cost multiplier |
|---|---|---|---|---|
| **Open** | k = 1 | Real name + logo | Original text | 1.0x (baseline) |
| **Shielded** | k ≥ 5 | Verified badge, no name | AI-masked description | ~1.2x |
| **Guarded** | k ≥ 20 | Category icon only | Heavily abstracted | ~1.5x |
| **Sealed** | k = ∞ | Fully anonymous | Opaque until accepted | ~2x+ |

---

## UI Adaptation Rules

Every contributor-facing screen adapts based on the campaign's privacy tier. These rules apply uniformly across all screens.

### Org Card

| Element | Open | Shielded | Guarded | Sealed |
|---|---|---|---|---|
| Logo | Real logo | Generic verified badge | Category icon | Lock icon |
| Name | Real name | "Verified AI Company" | "Technology Company" | "Anonymous Employer" |
| Industry | Full | Full | Category only | Hidden |
| Trust badge | Full tier name | "Verified ✓" | Hidden | Hidden |
| Track record | Stars, on-time %, campaign count | Campaign count only | Hidden | Hidden |
| Description | Full | Hidden | Hidden | Hidden |
| "View Profile" | Yes | Yes (limited) | No | No |

### Campaign Content

| Element | Open | Shielded | Guarded | Sealed |
|---|---|---|---|---|
| Campaign name | Original | Original | Anonymized | Generic |
| Description | Original | AI-masked version | "A verified company seeks [modality] data" | "Details available after acceptance" |
| Task instructions | Full preview | Masked preview | Generic template | Hidden until accepted |
| Compensation | Full detail | Full detail | Amount only | Amount only |
| Tags / frontiers | Full | Full | Frontier only | Hidden |

### Contributor Reviews

| Element | Open | Shielded | Guarded | Sealed |
|---|---|---|---|---|
| Review text | Visible | Visible (org name redacted) | Hidden | Hidden |
| Star rating | Visible | Aggregate only | Hidden | Hidden |

---

## Implementation

```typescript
type PrivacyTier = 'open' | 'shielded' | 'guarded' | 'sealed';

interface PrivacyConfig {
  tier: PrivacyTier;
  masked_description?: string;    // AI-generated for Shielded
  auto_declassification?: {
    after_months: number;
    target_tier: PrivacyTier;
  };
}

// Helper: determine what to show
function getOrgDisplay(org: Org, privacy: PrivacyConfig): OrgDisplay {
  switch (privacy.tier) {
    case 'open':
      return { name: org.name, logo: org.logo, stats: org.fullStats };
    case 'shielded':
      return { name: 'Verified AI Company', logo: VERIFIED_BADGE, stats: { campaigns: org.campaignCount } };
    case 'guarded':
      return { name: `${org.category} Company`, logo: CATEGORY_ICONS[org.category], stats: null };
    case 'sealed':
      return { name: 'Anonymous Employer', logo: LOCK_ICON, stats: null };
  }
}
```

---

## k-Anonymity Validation

When a campaign creator selects a privacy tier, the system validates the k value:

- Count the number of orgs in the same frontier
- If the frontier has < k orgs, warn: "Only 8 orgs in this frontier — k ≥ 20 is not effective"
- This is a campaign builder concern (Step 5), not a contributor portal concern — but the contributor portal must render the resulting adaptation correctly.
