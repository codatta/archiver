# Contributor Archetypes

> Four profiles used throughout the design docs. Real contributors fall between these.

---

## The Four Archetypes

### Supply Specialist

| Attribute | Profile |
|---|---|
| Primary task | 📤 Supply (80%+) |
| Campaign pattern | High volume, broad frontiers |
| Reward orientation | Prefers royalty or high fixed; cares about downstream pipeline speed |
| Key anxiety | "Will anyone actually label my data?" |
| Strength | Fast at generating content, high acceptance rate on supply |
| Weakness | Lower skill at labeling; supply rejection rates hurt confidence when doing labeling |

**What they look for in a campaign:**
- Fast pipeline velocity (supply gets labeled quickly)
- Clear supply instructions with examples
- High per-instance rate for supply tasks specifically

---

### Labeling Specialist

| Attribute | Profile |
|---|---|
| Primary task | 🏷 Labeling (80%+) |
| Campaign pattern | Focused on specific frontiers (e.g., robotics, NLP) |
| Reward orientation | Fixed pay preferred; wants a steady labeling queue |
| Key anxiety | "Will there be enough instances to label when I show up?" |
| Strength | Deep annotation skill, high acceptance rate, fast throughput |
| Weakness | Frustrated by thin supply queues; dislikes supply tasks |

**What they look for in a campaign:**
- Large instance pool with deep supply backlog
- Agent pre-labeling (faster labeling when agent does first pass)
- Per-instance pay rate for labeling, not just overall campaign rate

---

### Validation Specialist

| Attribute | Profile |
|---|---|
| Primary task | ✅ Validation (80%+) |
| Campaign pattern | High reputation, selective campaign enrollment |
| Reward orientation | Premium fixed or hybrid; high responsibility mindset |
| Key anxiety | "Am I being consistent? My rejections affect others' income." |
| Strength | Calibrated judgment, high consistency, respected reputation |
| Weakness | Queue depends entirely on labeling throughput; feels isolated |

**What they look for in a campaign:**
- Clear rubric and gold standard examples
- Reasonable rejection thresholds (not punished for being thorough)
- Visibility into how their decisions affect pipeline flow

---

### Generalist

| Attribute | Profile |
|---|---|
| Primary task | Mixed — no dominant type yet |
| Campaign pattern | Exploratory; tries many campaigns and task types |
| Reward orientation | Learning mode; no strong pay model preference |
| Key anxiety | "Where do I start? Which campaigns are good for beginners?" |
| Strength | Flexible, willing to try any task type |
| Weakness | Lower acceptance rate across all types; hasn't specialized yet |

**What they look for in a campaign:**
- "Good for beginners" signal
- Supply tasks (lowest barrier, no instance dependency)
- Clear instructions with sample submissions and rejection examples

---

## Specialization Is Emergent

Contributors don't choose an archetype — they drift into one. The platform surfaces this through the Reputation screen:

```
Your strongest task type: Labeling (94% acceptance)
You earn $18.40/hr on labeling vs. $11.20/hr on supply
```

The system recommends campaigns matching the contributor's observed strength but never locks them out of other task types.
