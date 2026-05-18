# Contributor Situations

> 25+ named situations across 5 phases. Each situation describes who faces it, what they're thinking, and what the UI must answer. Use these to validate screen designs and interaction flows.

---

## Phase A — Exploration (browsing campaigns)

### A1 · Specialist evaluating unfamiliar task mix

**Who:** Labeling specialist. **Trigger:** Campaign card shows "3 tasks" but no breakdown.

**Mindset:** "Is this mostly labeling or mostly supply? If it's supply-heavy, my hourly earnings drop significantly."

**UI must answer:** Task type breakdown with per-type pay rate on the campaign card.

---

### A2 · New contributor, no specialization

**Who:** First-timer. **Trigger:** First visit to campaign browse.

**Mindset:** "I have no idea which campaign to pick. I'm afraid of failing and hurting my reputation."

**UI must answer:** Beginner-friendly filter/tag. Recommend supply tasks (lowest barrier).

---

### A3 · Supply specialist evaluating royalty campaigns

**Who:** Experienced supply contributor. **Trigger:** Royalty campaign with attractive estimated earnings.

**Mindset:** "Royalties depend on downstream pipeline. How fast is labeling happening on this campaign?"

**UI must answer:** Pipeline velocity indicator on campaign detail ("Fast-moving" / "Moderate").

---

### A4 · Partial qualification

**Who:** Any contributor. **Trigger:** Qualifies for supply but not labeling in the same campaign.

**Mindset:** "Can I join for supply-only? Will I see labeling tasks I can't do?"

**UI must answer:** Per-task-type qualification display. Clear enrollment scope: "You qualify for supply tasks only."

---

### A5 · Fixed vs. royalty risk comparison

**Who:** Any contributor evaluating two campaigns. **Trigger:** $2.50 fixed vs. $1.00 + royalty (est. $2.50).

**Mindset:** "Fixed is guaranteed. Royalty is a bet on the pipeline. What's the actual distribution of outcomes?"

**UI must answer:** Royalty campaigns show: estimated range, typical time-to-first-payment, historical completion rate.

---

## Phase B — Enrollment (accepting a campaign)

### B1 · Understanding the commitment

**Who:** Any contributor. **Trigger:** About to click "Accept & Start Working."

**Mindset:** "If I stop after 20 submissions, do I keep my earnings? Can I leave?"

**UI must answer:** "You can stop contributing at any time. Completed work will still be paid. Royalties accrue per-instance as each clears validation."

---

### B2 · Setting expectations for mixed-type campaign

**Who:** Any contributor. **Trigger:** Campaign has supply + labeling; labeling queue starts empty.

**Mindset:** "If I'm a labeling specialist and the queue is empty for days, I've wasted my commitment."

**UI must answer:** Pipeline ordering explanation at enrollment: "Labeling tasks open up as supply submissions are accepted. Expect ~24 hours."

---

### B3 · Validation specialist accepting high-responsibility work

**Who:** Validation specialist. **Trigger:** Accepting campaign where they review others' work.

**Mindset:** "My rejections hurt others' income. I need the rubric to be clear BEFORE I commit."

**UI must answer:** Show rubric, gold standard examples, and acceptance/rejection threshold before enrollment.

---

## Phase C — Active Work (in a session)

### C1 · Supply contributor hitting session quota

**Who:** Supply specialist. **Trigger:** Reached daily cap (e.g., 20 videos/day).

**Mindset:** "I'm on a roll. Why am I stopped? Is something wrong with my work?"

**UI must answer:** "You've reached today's cap (20/20). Come back tomorrow. Your submissions are in review." Distinguish from quality hold.

---

### C2 · Labeling contributor, thin supply queue

**Who:** Labeling specialist. **Trigger:** Only 3 labeling tasks available.

**Mindset:** "I planned an hour of work. There's almost nothing here."

**UI must answer:** "Supply queue is building. Typically refills every ~2 hours. [Notify me when 10+ ready] or [Browse other campaigns]."

---

### C3 · Validation contributor waiting for labeling

**Who:** Validation specialist. **Trigger:** Zero validation tasks.

**Mindset:** "I'm the last human in the chain. Waiting is especially unproductive."

**UI must answer:** Pipeline depth: "18 instances currently in labeling — validation tasks will appear in ~3-5 hours." Offer notification + alternative campaign.

---

### C4 · Specialist doing off-type tasks

**Who:** Labeling specialist doing supply. **Trigger:** Joined for labeling but supply tasks opened first.

**Mindset:** "I'm slower at this. My rejection rate is higher. This is affecting my reputation for work I'm not good at."

**UI must answer:** Extra examples and edge-case guidance. Show acceptance rate vs. campaign average. Task type badge always visible.

---

### C5 · Specialist in flow state

**Who:** Labeling specialist with deep queue. **Trigger:** Normal high-velocity session.

**Mindset:** "Fast, familiar, rewarding. Don't interrupt me."

**UI must answer:** Streamlined task cycling. Keyboard shortcuts. Streak indicator. Minimal friction between completions. Quick-dismiss instructions.

---

### C6 · Cross-campaign session

**Who:** Any contributor working 2-3 campaigns. **Trigger:** Campaign A's queue is thin, switching to B.

**Mindset:** "The UI looks completely different in Campaign B. I need to re-orient."

**UI must answer:** Cross-campaign task view in My Tasks. Consistent workspace layout even when annotation config differs. Campaign switcher.

---

### C7 · Campaign nearing deadline

**Who:** Any contributor. **Trigger:** 800 remaining, 3 days left.

**Mindset:** "I could earn a lot by pushing hard but don't want to sacrifice quality."

**UI must answer:** Deadline signal without panic. Quality gate reminders: "Your acceptance rate is 94% — keep above 90%."

---

## Phase D — Reward Tracking

### D1 · Fixed pay — clean feedback loop

**Who:** Any contributor, fixed pay. **Trigger:** Submitted instance, waiting for review.

**Mindset:** "Accepted or rejected? And if rejected, why specifically?"

**UI must answer:** Sub-hour review turnaround (or SLA). Specific rejection reason. Running earnings tally visible in workspace.

---

### D2 · Royalty supply contributor tracking pipeline

**Who:** Supply specialist, royalty campaign. **Trigger:** 50 instances submitted, some through pipeline, some not.

**Mindset:** "My money is on a conveyor belt I can't control."

**UI must answer:** Per-submission pipeline status: `accepted → in labeling → labeled → validated → royalty-eligible → paid`. Visible at a glance for all submissions.

---

### D3 · Label rejection without feedback

**Who:** Labeling specialist. **Trigger:** 8 of 60 rejected, no specific reason.

**Mindset:** "What did I do wrong? How do I fix it?"

**UI must answer:** Specific annotation that failed + rubric reason + gold standard reference. Appeal option.

---

### D4 · Validator carrying weight of decisions

**Who:** Validation specialist. **Trigger:** Rejected 15 labels; labelers lost income.

**Mindset:** "Am I being consistent with the rubric? What if I'm wrong?"

**UI must answer:** Calibration tools. Own accept/reject ratio vs. campaign average. Appeals process awareness.

---

### D5 · Pipeline stalled — royalty anxiety

**Who:** Supply or labeling contributor, royalty campaign. **Trigger:** Campaign hasn't moved in 10 days.

**Mindset:** "Is this campaign dead? Will I ever see these royalties?"

**UI must answer:** Campaign health status. Clear notification if paused/abandoned. What happens to pending royalties on cancellation.

---

### D6 · Campaign ends before royalties unlock

**Who:** Supply contributor. **Trigger:** Org ends campaign. 30/50 instances passed validation; 20 still in labeling.

**Mindset:** "Do I get royalties for the 30? What about the 20?"

**UI must answer:** Policy surfaced at enrollment AND campaign close: royalties vest per instance as each clears validation. Clear outcome for stuck instances.

---

## Phase E — Specialization Over Time

### E1 · Discovering a niche from outcome data

**Who:** Generalist, 3–6 months in. **Trigger:** Acceptance rate on labeling is 94% vs. 78% on supply.

**Mindset:** "The data is telling me to focus on labeling."

**UI must answer:** Reputation screen surfaces insight: "Your strongest type: Labeling. You earn $18.40/hr vs. $11.20/hr on supply." Recommend matching campaigns.

---

### E2 · Specialist re-evaluating niche

**Who:** Established labeling specialist. **Trigger:** Market saturation — fewer labeling spots available.

**Mindset:** "Maybe I need to expand into validation or supply."

**UI must answer:** Skill expansion pathways (validation certification). Platform-wide demand signals ("Supply tasks are in high demand this week").

---

### E3 · Joining new campaign, recalibrating

**Who:** Labeling specialist joining a 70% supply campaign. **Trigger:** First session, doing supply.

**Mindset:** "This is jarring. I need to slow down and read carefully."

**UI must answer:** Force instruction read on first task in any new campaign. Task type badge always visible. Pipeline context bar shows campaign structure at a glance.
