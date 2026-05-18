# Release Workflow

> How we version, release, and maintain multiple major versions in parallel.
> For product context, see [prod_overview.md](./prod_overview.md). For build queue, see [prd.md](./prd.md).

---

## Versioning

**Single monorepo version.** All packages share one version number (the platform version), tracked in the root `VERSION` file. Individual package files (`package.json`, `pyproject.toml`) are synced from this source of truth during the release process.

**Semver:** `MAJOR.MINOR.PATCH`
- **MAJOR** — breaking API changes, new product generation (V1 → V2)
- **MINOR** — new features, non-breaking API additions
- **PATCH** — bug fixes, hotfixes, no API changes

---

## Branching Model

```
main (active development — next major)
 │
 ├── feat/xyz ──► PR ──► merge to main
 ├── fix/abc  ──► PR ──► merge to main
 │
 │   (when V1 ships)
 ├── release/v1  ◄── cut from main at v1.0.0 tag
 │    ├── fix/v1-hotfix ──► PR ──► merge to release/v1
 │    └── tags: v1.0.0, v1.0.1, v1.0.2 ...
 │
 │   (main becomes V2 development)
 ├── feat/v2-marketplace ──► PR ──► merge to main
 │
 │   (when V2 ships)
 └── release/v2  ◄── cut from main at v2.0.0 tag
      └── tags: v2.0.0, v2.0.1 ...
```

### Branch rules

| Branch | Purpose | Deploys to | Who merges |
|--------|---------|------------|------------|
| `main` | Active development (next major) | Staging (future) | PR with review |
| `release/v1` | V1 production maintenance | Production | PR with review |
| `release/v2` | V2 production (when V2 ships) | Production | PR with review |
| `feat/*`, `fix/*` | Feature/fix work | Nothing | Author opens PR |

### Key rules

1. **Production deploys only from `release/*` branches** (or `main` if no release branch exists yet).
2. **Never commit directly to `main` or `release/*`** — always via PR.
3. **Hotfixes for a released version** go to its `release/vN` branch, not `main`.
4. **Cherry-pick hotfixes to main** if the fix is also relevant to the next major version.
5. **Tags are immutable** — never delete or move a release tag.

---

## Release Process

### Cutting a new release

```bash
# 1. Ensure you're on the correct branch
git checkout release/v1   # or main if no release branch yet
git pull

# 2. Run the release workflow (bumps version, generates changelog, tags, creates GitHub Release)
gh workflow run release.yml -f bump=minor   # or: major, minor, patch

# 3. The workflow will:
#    - Bump VERSION file
#    - Sync version to all package files
#    - Generate changelog from conventional commits since last tag
#    - Commit, tag, push
#    - Create GitHub Release with changelog
#    - Trigger deploy workflows
```

### Cutting a release branch (major version freeze)

When V1 is feature-complete and you want to start V2 development on main:

```bash
# 1. Tag the current main as v1.0.0
gh workflow run release.yml -f bump=major -f branch=main

# 2. Create the release branch from that tag
git checkout -b release/v1 v1.0.0
git push -u origin release/v1

# 3. Main is now free for V2 development
#    Future V1 hotfixes go to release/v1
#    V2 features go to main
```

---

## Changelog

`CHANGELOG.md` is auto-generated from conventional commit messages.

### Format

```markdown
# Changelog

## [1.2.0] — 2026-04-01

### Features
- feat: add data asset marketplace (#45)
- feat: webhook notifications for balance changes (#42)

### Fixes
- fix: Stripe webhook signature validation (#41)
- fix: navbar logo not loading on Vercel (#38)

### Other
- chore: upgrade Supabase SDK to v2.16 (#40)
- docs: update API reference for v1.2 (#39)
```

### Commit message → changelog mapping

| Prefix | Changelog section | Version bump |
|--------|------------------|--------------|
| `feat:` | Features | minor |
| `fix:` | Fixes | patch |
| `docs:` | Other | patch |
| `chore:` | Other | patch |
| `refactor:` | Other | patch |
| `test:` | (excluded) | — |
| `BREAKING CHANGE:` | Breaking Changes | major |

---

## Deploy Triggers

### Current (pre-release branch)

All deploys trigger on push to `main`. This continues until V1 is frozen.

### After release branch exists

| Event | What deploys |
|-------|-------------|
| Push to `release/v1` | Production (webapp + API + docs) |
| Tag `v1.*` | GitHub Release created (no extra deploy — tag is on release branch) |
| Push to `main` | Nothing (or staging, when staging exists) |
| `workflow_dispatch` | Manual deploy from any branch |

---

## Version File Locations

All synced from root `VERSION` during release:

| File | Field |
|------|-------|
| `VERSION` | Plain text (source of truth) |
| `packages/api/pyproject.toml` | `project.version` |
| `packages/cli/package.json` | `version` |
| `packages/webapp/package.json` | `version` (added) |
| `packages/docs/package.json` | `version` |

---

## Quick Reference

```bash
# See current version
cat VERSION

# See all releases
gh release list

# See changelog for a specific release
gh release view v1.2.0

# Hotfix on V1 while developing V2
git checkout release/v1
git checkout -b fix/v1-critical-bug
# ... fix, test, commit ...
git push -u origin fix/v1-critical-bug
gh pr create --base release/v1 --title "fix: critical bug"
# After merge, cherry-pick to main if needed:
git checkout main && git cherry-pick <commit-sha>
```
