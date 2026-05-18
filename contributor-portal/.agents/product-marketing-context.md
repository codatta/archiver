# Product Marketing Context

*Last updated: 2026-04-14*

## Product Overview

**One-liner:** Humanbased is a data contribution platform where humans collect, annotate, and validate AI training data — with lineage tracking built in for on-chain attribution.

**What it does:** Humanbased connects data contributors (humans who capture and label video) with campaign builders (AI teams who need high-quality training data). Contributors work through the Contributor Kitchen portal — uploading footage, reviewing vision-processed segments, annotating with spatial/temporal/semantic labels. Builders configure campaigns via Builder Studio, define annotation schemas using Label Studio XML, and consume quality-gated output with full lineage metadata.

**Product category:** AI training data platform / data labeling marketplace

**Product type:** Two-sided platform — supply portal (Contributor Kitchen) + demand portal (Builder Studio)

**Business model:** Campaign-based — builders fund data collection campaigns; contributors earn compensation per validated instance. On-chain attribution distributes royalties upstream through the lineage chain.

---

## Target Audience

**Supply side (Contributor Kitchen):**
- Data contributors: freelancers, researchers, annotation workers, hobbyist data collectors
- Decision-makers: the contributors themselves (individual, not enterprise)
- Primary use case: earn by contributing high-quality video data + annotations for robotics AI training

**Demand side (Builder Studio):**
- AI companies, research labs, university robotics programs, embodied AI teams
- Decision-makers: ML engineers, research leads, data ops managers
- Primary use case: commission and receive annotated training data with provenance for specific AI domains (V1: robotics/embodiment)

**Jobs to be done:**
- Contributor: "I want to monetize my ability to capture and label data with fair, traceable credit"
- Builder: "I need domain-specific labeled data at scale, with quality I can trust and lineage I can verify"

---

## Personas

| Persona | Cares about | Challenge | Value we promise |
|---------|-------------|-----------|------------------|
| **Contributor** | Fair pay, clear tasks, meaningful work | No visibility into how data is used; annotation tools are complex | Clear workflow, quality feedback, lineage-based attribution |
| **Campaign Builder** | Data quality, reproducibility, cost efficiency | Custom annotation schemas are hard to build; vendor lock-in | Open LS XML standard, ML Backend protocol, full lineage metadata |
| **ML Engineer (Builder)** | Pipeline integration, format compatibility | Converting labeled data to training format is painful | Embodiment-X schema, standard export formats |

---

## Problems & Pain Points

**Core problem (Builder):** High-quality domain-specific training data (especially robotics/embodiment) is scarce, expensive, and comes without provenance. Annotated data has no lineage back to the original capture conditions.

**Core problem (Contributor):** Data contribution platforms treat contributors as interchangeable workers with no credit, no quality feedback, and no stake in the data's value chain.

**Why alternatives fall short:**
- Scale.ai / Labelbox: no on-chain attribution, no lineage, platform lock-in, proprietary annotation schemas
- Label Studio self-hosted: no contributor network, no campaign management, no payment rails
- Manual data collection: no quality gates, no structured annotation, no reusability

**What it costs them (Builder):** 3-6 months per dataset, $50K-$500K+ for domain-specific robotics data. No audit trail.

**Emotional tension (Contributor):** "My work disappears into a black box. I don't know if it's being used, how it performed, or whether I'll ever be compensated fairly."

---

## Competitive Landscape

**Direct:** Scale.ai, Labelbox, Appen — fall short because: proprietary schemas, no contributor attribution, no lineage standard, closed ecosystems

**Secondary:** Label Studio (self-hosted) — falls short because: no contributor network, no campaign management, no compensation layer

**Indirect:** In-house data teams — fall short because: expensive, slow, no reusability, no lineage

---

## Differentiation

**Key differentiators:**
- **Open annotation standard:** Label Studio XML as the canonical schema — any LS-compatible model (SAM2, YOLO, GroundingDINO) is drop-in compatible via ML Backend protocol
- **Built-in lineage:** Every instance tracks `parent_instances[]` through the full T1→T2→T3→T4 pipeline — suitable for future on-chain attribution
- **Vision Engine pre-labeling:** Automated motion detection, pose estimation, scene segmentation reduces annotation burden while keeping humans in the loop
- **Shared infrastructure:** Both portals share one Supabase instance — campaign config flows directly from Builder Studio to Contributor Kitchen with no ETL

**Why customers choose us:**
- Builders: open standard means no vendor lock-in; lineage means auditable data provenance
- Contributors: transparent quality feedback, attribution tied to their specific contribution

---

## Objections

| Objection | Response |
|-----------|----------|
| "We already have an annotation pipeline" | Contributor Kitchen adds the supply network and lineage layer on top of standard LS XML configs — not a replacement, an upgrade |
| "On-chain attribution is vaporware" | Lineage staging uses the same interface as production; the data model is ready when the chain layer is |
| "Robotics data is too niche" | V1 is robotics because the annotation schema is richest there; the campaign framework supports any domain |

**Anti-persona:** Teams that need generic image classification at commodity prices; teams that don't care about data provenance

---

## Customer Language

**How builders describe the problem:**
- "We spend more time cleaning data than training models"
- "We have no idea who labeled this or under what conditions"
- "Custom annotation tools take months to build and break every release"

**How contributors describe the problem:**
- "I label data all day but never see where it goes"
- "The tools are confusing and I don't know if my work is good"

**Words to use:** lineage, attribution, contribution, crafted, Kitchen, Studio, campaign, instance, quality gate, Embodiment-X
**Words to avoid:** crowdsourcing (implies race-to-bottom), gig work (implies disposable), portal (generic)

**Glossary:**
| Term | Meaning |
|------|---------|
| Contributor Kitchen | Supply-side portal for data contributors |
| Builder Studio | Demand-side portal for campaign builders |
| Campaign | Scoped data collection + annotation request with LS XML config |
| Instance | Atomic contribution with lineage and content hash |
| Lineage | Parent chain (T1→T2→T3→T4) tracked for attribution |
| ML Backend | Standard LS protocol wrapping any AI model (Vision Engine, SAM2, etc.) |
| Embodiment-X | Humanbased's robotics annotation schema (temporal + spatial + language) |

---

## Brand Voice

**Tone:** Contributor Kitchen — warm, empowering, craft-forward. Builder Studio — capable, precise, productive. Platform-level — human-first, technically credible, lineage-honest.

**Style:** Direct and specific. No jargon for contributors. Technical precision for builders. Both: no hype.

**Personality:** Humanbased: rigorous, human, transparent. Kitchen: approachable chef. Studio: focused director.

---

## Proof Points

*(V1 — no external proof points yet. Placeholders for when available.)*

**Value themes:**
| Theme | Proof |
|-------|-------|
| Open standard | LS XML config = any LS-compatible model works out of the box |
| Lineage-ready | content_hash + parent_instances[] per instance from day one |
| Human in the loop | Vision Engine pre-labels + human cull/annotate/validate pipeline |

---

## Goals

**Business goal:** Establish Humanbased as the reference platform for domain-specific embodiment data with full lineage — starting with robotics video.

**Conversion action (Contributor):** Upload first video and complete first annotation in Contributor Kitchen

**Conversion action (Builder):** Launch first campaign in Builder Studio and receive validated instances
