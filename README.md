# codatta/archiver

Graveyard for deprecated Codatta GitHub repositories. Every directory here is a verbatim snapshot of a standalone repo at the time it was retired. No active development happens here.

**Migration tracked in Linear:** [IN-210 — Codatta GitHub Repository Cleanup / Monorepo Migration](https://linear.app/inductive-network/issue/IN-210/codatta-github-repository-cleanup-monorepo-migration)

---

## Archived projects

| Repo | Description | Original position | Language | Created | Last active | Archived | Owner | Top contributors | Why archived |
|---|---|---|---|---|---|---|---|---|---|
| [`codatta/developer-portal`](https://github.com/codatta/developer-portal) | HumanBased Data API + Web App — enterprise data delivery platform for crowd-sourced data. Developer-facing portal for API key management, campaign creation, and billing. | Primary developer-facing product portal; superseded by `frontend/developer-portal-web` in the monorepo | TypeScript | 2026-03-22 | 2026-05-18 | 2026-05-18 | Yi Zhang (`@beingzy`) | Yi Zhang — 234 commits · 316105wwll-sudo — 50 commits · JessieJiang2021 — 6 commits · zouqinghua — 4 commits | Superseded by `frontend/developer-portal-web` in the monorepo. Standalone repo retired as part of IN-210 monorepo consolidation. |
| [`codatta/contributor-portal`](https://github.com/codatta/contributor-portal) | Contributor-facing portal for the Humanbased platform — task browsing, campaign participation, and submission management. | Primary contributor-facing product portal; superseded by `frontend/contributor-portal-web` in the monorepo | TypeScript | 2026-04-15 | 2026-04-24 | 2026-05-18 | Yi Zhang (`@beingzy`) | Yi Zhang — 33 commits (sole contributor) | Superseded by `frontend/contributor-portal-web` in the monorepo. Standalone repo retired as part of IN-210 monorepo consolidation. |
| [`codatta/attempt-index`](https://github.com/codatta/attempt-index) | AttemptIndex — submission attempt tracking microservice for the Humanbased contribution pipeline. Tracks and deduplicates contributor submission attempts. | Standalone Python microservice in the CFP backend stack; logic migrated into the monorepo `backend/` | Python | 2026-04-27 | 2026-04-27 | 2026-05-18 | Yi Zhang (`@beingzy`) | Yi Zhang — 14 commits (sole contributor) | Logic migrated into monorepo `backend/`. Standalone microservice repo retired as part of IN-210 monorepo consolidation. |
| [`codatta/codatta-frontier-standards`](https://github.com/codatta/codatta-frontier-standards) | Public standards and JSON schema for multi-frontier data annotation, starting with crypto account annotation. Intended as the canonical taxonomy layer for Codatta's contribution pipeline. | Standalone public repo — reference for external contributors and partners integrating with the annotation pipeline | Markdown | 2024-11-02 | 2024-11-02 | 2026-05-18 | Yi Zhang (`@beingzy`) | Yi Zhang — 2 commits (sole contributor) | Dormant for 18+ months. Schema work was never adopted downstream and the annotation pipeline evolved independently. |
| [`codatta/AI-Evolution-Game`](https://github.com/codatta/AI-Evolution-Game) | Browser-based interactive game prototype where falling pieces progressively transform a rectangle into a trapezoid shape. Built as an experiment in AI-assisted game development. | Private prototype repo — internal experiment, never shipped or linked to any product | JavaScript | 2024-10-26 | 2024-10-27 | 2026-05-18 | Yi Zhang (`@beingzy`) | Yi Zhang — 9 commits (sole contributor) | Abandoned prototype after 2 days of development. No downstream use. |

---

## How to add to the archiver

When retiring a repo:

1. Clone the repo and copy its contents (excluding `.git/`) into a new subdirectory named after the original repo
2. Add a row to the table above
3. Commit directly to `main` (no PRs needed — this is an archive, not active code)
4. Delete the original GitHub repo
5. Update [IN-210](https://linear.app/inductive-network/issue/IN-210/codatta-github-repository-cleanup-monorepo-migration) with the completed status
