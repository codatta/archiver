# Team Workflow — Linear + Claude Code

How we use Linear to coordinate work on the developer portal.

## Principles

1. **Issues carry the context, PRs carry the code.** Non-technical context (what, why, acceptance criteria) lives in the Linear issue. The PR only needs to describe *how* it was built.
2. **Claim before you build.** No work starts without assigning yourself and moving the issue to "In Progress."
3. **Every task connects to the bigger picture.** Issues belong to Projects, Projects belong to Initiatives.

## Linear Structure

```
Initiative: Launch developer.humanbased.ai v1
├── Project: Auth & Onboarding
│   ├── Issue: Email/password sign-up flow
│   ├── Issue: GitHub OAuth sign-in
│   └── Issue: HuggingFace OAuth sign-in
├── Project: API Key Management
│   ├── Issue: Generate API keys
│   └── Issue: Revoke API keys
├── Project: Documentation Site
│   └── Issue: Getting started guide
└── ...
```

- **Initiatives** = quarter-level goals (the vision)
- **Projects** = feature groups with auto-calculated progress bars
- **Issues** = individual tasks one person can complete

## Issue Template

When creating an issue, fill in:

```
### What
One-line description of the task.

### Why
Business or user context — why this matters, what problem it solves.

### Acceptance Criteria
- [ ] What must be true when this is done
- [ ] Specific UI behavior, API response, or edge case handling

### Technical Notes (optional)
Files likely to change, dependencies, gotchas.
```

This ensures any builder — regardless of experience level — has the context they need before writing a single line of code.

## Daily Workflow

### Starting work

1. Open Linear → check the current Cycle
2. Pick an unassigned issue (or one assigned to you)
3. **Assign yourself** and move to **"In Progress"**
4. Create a branch named after the issue:
   ```bash
   git checkout develop && git pull
   git checkout -b feat/LIN-123-short-description
   ```

### While building

- If you need clarification → comment on the Linear issue, not Slack DMs
- If scope changes → update the issue description before continuing
- If blocked → move to "Blocked" status and tag the blocker

### Finishing work

1. Push branch and open PR targeting `develop`
2. In the PR body, link the issue: `Closes LIN-123`
3. Move issue to **"In Review"**
4. After merge → Linear auto-moves to **"Done"** (if GitHub integration is connected)

## Avoiding Duplicate Work

| Problem | Solution |
|---------|----------|
| Two people start the same task | **Always check assignee + status before starting.** If it's "In Progress" with an assignee, it's taken. |
| Similar issues created by different people | Use Linear's duplicate detection. Before creating, search existing issues. |
| Overlapping scope between issues | PM breaks down issues so each has a single clear owner and non-overlapping scope. |

## Using Claude Code with Linear

Each team member has Linear MCP configured in this repo (`.mcp.json`). This means inside Claude Code you can:

```
"Show me my assigned issues"
"What's the acceptance criteria for LIN-123?"
"Move LIN-123 to In Progress"
"Create an issue: OAuth callback fails on Safari — assign to me, label: bug, priority: high"
```

### Recommended flow for builders

1. Start a Claude Code session
2. Ask: "What issues are assigned to me in the current cycle?"
3. Pick one: "Let's build LIN-123"
4. Claude reads the issue context, creates the branch, and starts implementing
5. When done, Claude can update the issue status and open the PR

This keeps less-experienced builders on track — Claude has the full issue context loaded and can reference the acceptance criteria as it works.

## Cycles (Sprints)

- **Duration:** 1 week (adjust as team finds its rhythm)
- **Planning:** Monday — PM moves prioritized issues into the cycle
- **Review:** Friday — check what shipped, carry over what didn't
- **Metrics:** Linear auto-tracks velocity (issues closed per cycle) and scope creep (issues added mid-cycle)

## Big Picture View

Use Linear's **Roadmap** view to see:
- All active Projects with progress bars
- Which Initiative each Project contributes to
- What's coming next vs. what's in flight

This answers: "Where are we relative to the overall vision?" without anyone maintaining a spreadsheet.
