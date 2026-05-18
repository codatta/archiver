# codatta/archiver

Graveyard for deprecated Codatta GitHub repositories. Every directory here is a verbatim snapshot of a standalone repo at the time it was retired. No active development happens here.

**Migration tracked in Linear:** [IN-210 — Codatta GitHub Repository Cleanup / Monorepo Migration](https://linear.app/inductive-network/issue/IN-210/codatta-github-repository-cleanup-monorepo-migration)

---

## Archived projects

| # | Repo | Description | Language | Created | Last active | Archived | Owner | Top contributors | Why archived |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [`codatta/developer-portal`](https://github.com/codatta/developer-portal) | Developer-facing portal for API key management, campaign creation, and billing. | TypeScript | 2026-03-22 | 2026-05-18 | 2026-05-18 | Yi Zhang | Yi Zhang — 234 · 316105wwll-sudo — 50 · JessieJiang2021 — 6 · zouqinghua — 4 | Superseded by `frontend/developer-portal-web` in the monorepo. |
| 2 | [`codatta/contributor-portal`](https://github.com/codatta/contributor-portal) | Contributor-facing portal for task browsing, campaign participation, and submission management. | TypeScript | 2026-04-15 | 2026-04-24 | 2026-05-18 | Yi Zhang | Yi Zhang — 33 (sole) | Superseded by `frontend/contributor-portal-web` in the monorepo. |
| 3 | [`codatta/attempt-index`](https://github.com/codatta/attempt-index) | Microservice for tracking and deduplicating contributor submission attempts. | Python | 2026-04-27 | 2026-04-27 | 2026-05-18 | Yi Zhang | Yi Zhang — 14 (sole) | Logic migrated into monorepo `backend/`. |
| 4 | [`codatta/codatta-frontier-standards`](https://github.com/codatta/codatta-frontier-standards) | Public JSON schema for multi-frontier data annotation. | Markdown | 2024-11-02 | 2024-11-02 | 2026-05-18 | Yi Zhang | Yi Zhang — 2 (sole) | Dormant 18+ months; schema never adopted downstream. |
| 5 | [`codatta/AI-Evolution-Game`](https://github.com/codatta/AI-Evolution-Game) | Browser-based game prototype built as an AI-assisted development experiment. | JavaScript | 2024-10-26 | 2024-10-27 | 2026-05-18 | Yi Zhang | Yi Zhang — 9 (sole) | Abandoned after 2 days; no downstream use. |

---

## How to add to the archiver

When retiring a repo:

1. Clone the repo and copy its contents (excluding `.git/`) into a new subdirectory named after the original repo
2. Add a row to the table above
3. Commit directly to `main` (no PRs needed — this is an archive, not active code)
4. Delete the original GitHub repo
5. Update [IN-210](https://linear.app/inductive-network/issue/IN-210/codatta-github-repository-cleanup-monorepo-migration) with the completed status
