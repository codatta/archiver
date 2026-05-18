# Code Review Guidelines

> This file configures Claude Code Review. It only affects automated PR reviews,
> not interactive Claude Code sessions (those follow CLAUDE.md).

## Always check

### Security
- OAuth flows validate state, PKCE, and nonce parameters
- HuggingFace OAuth: id_token claims (iss, aud, exp, email_verified) are validated server-side
- Supabase admin API calls (`supabase.auth.admin.*`) are backend-only, never in frontend code
- API keys, client_secret, and tokens are never exposed to the frontend or logged
- User input is validated at API boundaries (FastAPI models, not raw dict access)
- No plaintext credentials in committed files — use `.env` references only

### Auth & authorization
- New API routes have appropriate auth middleware (`get_current_user`, `require_org_member`, or `require_org_admin`)
- Frontend routes that need auth are guarded (redirect to /auth/signin if no session)
- Org-scoped endpoints verify membership, not just authentication

### Data integrity
- Database writes use Supabase SDK properly (check `.execute()` return, handle errors)
- Destructive operations (delete, update) have confirmation or idempotency guards
- MySQL (AliCloud PolarDB) access is read-only — no writes to supply-side data

### Testing
- New logic has corresponding tests (pytest for API, bun test for webapp)
- Tests cover happy path + at least one edge case (empty, null, invalid input)
- Existing tests are not weakened or deleted without explanation
- Test assertions are specific (not just `assert res.status_code == 200` — check the body too)

### Frontend
- No `any` types, `@ts-ignore`, or `as any` — fix the actual type
- React components don't leak state (useEffect cleanup, unmount guards)
- API calls use `apiFetch` helper (not raw `fetch`) for consistent auth headers

### Deployment
- Vercel commands include `--scope=inductive-network`
- CI workflows only trigger on `main`, `staging`, or `release/**` branches
- No hardcoded environment URLs — use `settings.webapp_url`, `ENV.API_URL`

## Ignore

- Files in `node_modules/`, `.venv/`, `dist/`, `__pycache__/`
- Generated lockfiles (`bun.lock`, `uv.lock`)
- Screenshot PNGs in `ux-tests/` and `screenshots/`
- Puppeteer capture scripts in `scripts/capture-*.mjs`
- The `ai-native-collaboration.md` file (retrospective doc, not code)

## Style preferences

- Prefer early returns over deeply nested conditionals
- Keep functions under ~50 lines — extract helpers if longer
- Use conventional commit messages (`feat:`, `fix:`, `chore:`, `test:`, `docs:`)
- Python: follow ruff defaults (E, F, I, N, W rules)
- TypeScript: no unused imports, no unused variables
