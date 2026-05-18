# codatta/archiver

Graveyard for deprecated Codatta GitHub repositories. Every directory here is a verbatim snapshot of a standalone repo at the time it was retired. No active development happens here.

**Migration tracked in Linear:** [IN-210 — Codatta GitHub Repository Cleanup / Monorepo Migration](https://linear.app/inductive-network/issue/IN-210/codatta-github-repository-cleanup-monorepo-migration)

---

## Archived projects

### `codatta-frontier-standards/`

| Field | Value |
|---|---|
| **Original repo** | [`codatta/codatta-frontier-standards`](https://github.com/codatta/codatta-frontier-standards) |
| **Description** | Public standards and JSON schema for multi-frontier data annotation, starting with crypto account annotation. Intended as the canonical taxonomy layer for Codatta's contribution pipeline. |
| **Original position** | Standalone public repo — reference for external contributors and partners integrating with the annotation pipeline |
| **Created** | 2024-11-02 |
| **Last active** | 2024-11-02 |
| **Archived** | 2026-05-18 |
| **Owner / creator** | Yi Zhang (`@beingzy`) |
| **Top contributors** | Yi Zhang — 2 commits (sole contributor) |

**Why archived:** Dormant for 18+ months. The schema work was never adopted downstream and the annotation pipeline evolved independently. Content preserved for reference.

---

### `AI-Evolution-Game/`

| Field | Value |
|---|---|
| **Original repo** | [`codatta/AI-Evolution-Game`](https://github.com/codatta/AI-Evolution-Game) |
| **Description** | Browser-based interactive game prototype where falling pieces progressively transform a rectangle into a trapezoid shape. Built as an experiment in AI-assisted game development. |
| **Original position** | Private prototype repo — internal experiment, never shipped or linked to any product |
| **Created** | 2024-10-26 |
| **Last active** | 2024-10-27 |
| **Archived** | 2026-05-18 |
| **Owner / creator** | Yi Zhang (`@beingzy`) |
| **Top contributors** | Yi Zhang — 9 commits (sole contributor) |

**Why archived:** Abandoned prototype after 2 days of development, Oct 2024. No downstream use. Preserved as a historical artifact.

---

## How to add to the archiver

When retiring a repo:

1. Clone the repo and copy its contents (excluding `.git/`) into a new subdirectory named after the original repo
2. Add an entry to this README with the table above filled in
3. Commit directly to `main` (no PRs needed — this is an archive, not active code)
4. Delete the original GitHub repo
5. Update [IN-210](https://linear.app/inductive-network/issue/IN-210/codatta-github-repository-cleanup-monorepo-migration) with the completed status
