# Release Workflow

How code goes from idea to production — with semantic versioning, staging validation, and zero-downtime releases.

---

## Branch Model

```
feat/* ──► PR to staging ──► staging (auto-deploy to staging env)
                                ↓
                         manual QA + sign-off
                                ↓
         [Promote workflow]  staging → main  (PR auto-generated)
                                ↓
                         review + merge PR
                                ↓
                             main (auto-deploy to production)
                                ↓
                        [Release workflow]  tag + changelog + GitHub Release
```

| Branch | Environment | Audience | Deploy trigger |
|--------|------------|----------|---------------|
| `staging` | staging.*.humanbased.ai | Internal team | Push (auto) |
| `main` | *.humanbased.ai | Customers | PR merge (auto) |
| `release/**` | *.humanbased.ai | Customers | Push (emergency hotfix) |

---

## Environments

### Staging (integration)
- **Webapp**: staging.developer.humanbased.ai
- **API**: staging.api.humanbased.ai
- **Docs**: staging.docs.humanbased.ai
- Deploys automatically on every push to `staging`
- Uses staging Supabase, staging Cloud Run service
- Safe to break — this is the experimentation zone

### Production (stable)
- **Webapp**: developer.humanbased.ai
- **API**: api.humanbased.ai
- **Docs**: docs.humanbased.ai
- Deploys automatically on push to `main` (via PR merge)
- Real customer traffic — must be stable

---

## Day-to-Day: Feature Development

```bash
# 1. Start from staging
git checkout staging && git pull
git checkout -b feat/my-feature

# 2. Implement, test, lint
# ...

# 3. Open PR targeting staging
git push -u origin feat/my-feature
gh pr create --base staging --title "feat: my feature" --body "IN-123 ..."

# 4. After review, merge to staging → auto-deploys to staging env
# 5. QA on staging.developer.humanbased.ai
```

Multiple features can accumulate on `staging` before promoting to production. This is the fast iteration loop.

---

## Promoting to Production

When staging is stable and you're ready to ship:

### Option A: Automated (recommended)

1. Go to **Actions → Promote Staging to Production**
2. Click **Run workflow**
3. Select version bump type:
   - **patch** (0.2.0 → 0.2.1) — bug fixes, small tweaks
   - **minor** (0.2.0 → 0.3.0) — new features, non-breaking changes
   - **major** (0.2.0 → 1.0.0) — breaking changes, major milestones
4. Optionally add a one-line summary
5. The workflow creates a PR from `staging → main` with a changelog

### Option B: Manual

```bash
# Create the PR yourself
gh pr create --base main --head staging \
  --title "release: v0.3.0" \
  --body "## Release v0.3.0 ..."
```

### After the promotion PR is merged

All three deploy workflows trigger automatically:
- `deploy-webapp.yml` → Vercel production
- `deploy-api.yml` → Cloud Run production
- `deploy-docs.yml` → Vercel production

Linear tickets referenced in the PR (via `IN-<number>`) are automatically moved to **Done**.

---

## Cutting a Release (tagging + changelog)

After the promotion PR merges to `main`:

1. Go to **Actions → Release**
2. Click **Run workflow** on the `main` branch
3. Select the same bump type you used for the promotion
4. The workflow will:
   - Bump `VERSION` file (e.g., 0.2.0 → 0.3.0)
   - Sync version to all `packages/*/package.json` and `packages/api/pyproject.toml`
   - Generate a changelog entry from conventional commits
   - Create a git tag (`v0.3.0`)
   - Create a GitHub Release with release notes

### Semantic Versioning Rules

| Bump | When | Example |
|------|------|---------|
| `patch` | Bug fixes, dependency updates, docs | 0.2.0 → 0.2.1 |
| `minor` | New features, non-breaking API additions | 0.2.0 → 0.3.0 |
| `major` | Breaking API changes, architectural shifts | 0.2.0 → 1.0.0 |

The VERSION file is the source of truth. Package versions are synced from it during release.

---

## Emergency Hotfixes

For critical production bugs that can't wait for the staging cycle:

```bash
# 1. Branch from main
git checkout main && git pull
git checkout -b release/hotfix-description

# 2. Fix, test, push
git push -u origin release/hotfix-description

# 3. PR targeting main (bypasses staging)
gh pr create --base main --title "fix: critical bug description"

# 4. After merge, deploy workflows fire automatically

# 5. IMPORTANT: backport to staging
git checkout staging && git pull
git merge main
git push
```

`release/**` branches deploy directly to production on push — use only for emergencies.

**Always backport hotfixes to staging** to prevent regression on the next promotion.

---

## Workflow Summary

| Step | Trigger | Automated? |
|------|---------|-----------|
| Feature → staging | PR merge | Deploy: yes |
| Staging → main (promote) | `promote.yml` dispatch | PR creation: yes, merge: manual |
| Production deploy | Push to main | Yes |
| Version tag + release | `release.yml` dispatch | Yes |
| Linear ticket sync | PR merge | Yes |
| Hotfix → main | PR merge | Deploy: yes, backport: manual |

---

## Checklist: Before Promoting

- [ ] All features on staging are QA'd
- [ ] No known regressions on staging
- [ ] API endpoints tested (staging.api.humanbased.ai)
- [ ] Webapp tested (staging.developer.humanbased.ai)
- [ ] No pending migrations that need manual steps
- [ ] Linear tickets for included features are up to date
