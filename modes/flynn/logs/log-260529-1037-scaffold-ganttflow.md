# SUPER-M Session: 2026-05-29

**Mode:** SCAFFOLD PROJECT
**Project:** GanttFlow

## Workflow Health Summary

Scaffolded GanttFlow from a single `BRIEFING.md` to a complete, lean 42Labs workflow skeleton — two git repos pushed + branch-protected, hooks wired, pipeline seeded. App code intentionally not initialized (architect owns specifics). One self-improvement applied: added `scaffold`/`upgrade` branch slugs to close a vocabulary gap that would have made this very session's canon commit a C1 finding.

## Session Flow

1. **Session start** — `super-m-local.md` absent + no git/meta → pre-scaffold project, not bootstrappable. Routed to SCAFFOLD PROJECT (user-confirmed).
2. **Profile (fresh mode)** — resolved blocking open decisions with the user:
   - **O1** (packaging) → **standalone** repo pair (LENS integration deferred/TBD). Briefing updated.
   - **O2** (stack) → **lean**: only certain-now elements committed (Next.js + Tailwind/42labs.ds + Supabase + Auth). Architect scaffolds specifics after tech specs exist. Briefing updated; added **O7** (hosting Vercel-vs-Railway, deferred).
   - Correction taken from user: do **not** over-specify stack pre-requirements; 42Labs canon stack (read from `42labs.ds` + `the-void/infra`) is the reference, not "reuse from LENS."
   - Service profile: Supabase + Google OAuth only. No payments/email/Sentry/Matomo/affiliates/Plain/Slack/AI-proxy/hosting-CI. No stubs.
   - Package manager: **pnpm** (canon app convention; scaffold template was npm — adapted).

## Scaffold Output

| Item | Result |
|:--|:--|
| `ganttflow-meta` | git `main` → `github.com/42piratas/ganttflow-meta` (private), `main` protected |
| `ganttflow-app` | git `staging`+`main` → `github.com/42piratas/ganttflow-app` (private), default `staging`, both protected |
| Hooks | canon `.githooks` + markers (`.repo-class`/`.integration-branch`) in both; lefthook wired in app (commitlint bad-msg block verified ✓) |
| Portable worktrees | `worktree.useRelativePaths=true` both repos; git 2.54.0 |
| Templates | filled, trimmed to lean profile, npm→pnpm (ci.yml, lefthook, settings.json hook, skill cmds) |
| Lean choices | no `create-next-app` (avoids locking Next version — architect's call); minimal `package.json` (prepare + commitlint + lefthook) so hooks bite; `.mcp.json` = GitHub + Chrome DevTools + Playwright (Supabase MCP deferred until live project) |
| pipeline.md | seeded: Phase 1 (architect specs + app init), backlog from briefing MVP/v1 estimates |
| Artifacts dir | set to `ganttflow-meta/artifacts` (NOT `~/Downloads`, per C1) + gitignored |

## Self-Improvements Applied

| # | Target | Change | Rationale |
|:--|:--|:--|:--|
| 1 | `super-m.md` §Operating Rules slug table | Added `scaffold` + `upgrade` slugs | SCAFFOLD/UPGRADE sessions produce canon bookkeeping (registry + log) but had no valid branch slug → every such commit was a self-inflicted C1 finding. Surfaced on first scaffold under the absorbed flow. User-approved. |

## Deviations from `skill-project-scaffold.md` (all deliberate, lean profile)

1. **pnpm, not npm** — canon app convention; adapted ci.yml (pnpm/action-setup, frozen-lockfile, pnpm exec), lefthook `npx` left (resolves via node_modules/.bin), settings.json hook → `pnpm run --if-present test`.
2. **No `create-next-app`** — app not initialized; architect initializes Next on confirmed specs. Minimal `package.json` only.
3. **CI** — only `ci.yml` + `pr-base-guard.yml` + `staging-db.yml` (Supabase). No deploy-notify/release/e2e/stress.
4. **services-setup.md / mcp-setup.md / playbook-infra.md / .env.example** — trimmed to Supabase + Google OAuth; omitted services documented as "add via UPGRADE."
5. **MCP/Supabase setup (scaffold steps 15–16) + live Supabase project** — deferred to architect (no live project at scaffold).
6. **Step 14 PostToolUse hook** — user must open `/hooks` once to force settings reload (instructed separately).

## Recommendations

1. **[architect, next]** Block S1-01: turn briefing → tech specs (confirm stack, design scheduler engine + gCal sync/echo-suppression, decide O7 hosting). The sync layer is the risk per the briefing.
2. **[low]** Once Supabase project exists, complete `mcp-setup.md#supabase-mcp` + fill `.env.example`/`playbook-infra.md` URLs; activate `staging-db.yml` secrets.
3. **[info]** App pre-push runs `pnpm exec tsc --noEmit` — will fail until the architect adds TypeScript (expected; first architect task initializes Next+TS).

## Next Run

- Recommended: after architect completes S1-01 (first real engineering blocks) → first AUDIT pass.
- Next deep-dive category: C1 (Checklist Compliance) — verify hook discipline holds on the first worktree-based blocks.
