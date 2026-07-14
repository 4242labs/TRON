# Skill: Project Audit

**Purpose:** Canonical gap-analysis checklist for an existing 42Labs project. Scores every applicable item: ✅ present and correct / ⚠️ partial or misconfigured / ❌ missing.

**Prerequisite:** `skills/skill-project-profile.md` has run and locked the profile — **including the app toolchain and layout (Step 1)**. Audit only for services in the confirmed profile — omit rows for services the project does not use.

**Toolchain scoping — read before scoring the app repo.** Canon's *discipline* is universal and every project is held to it: two repos, a staging gate, a commit-message check, a pre-push check that the code is sound, CI that gates the merge, protected branches, portable worktrees. The *tools that implement that discipline* are not universal — they are whatever the confirmed toolchain uses. Every app-repo row below states the **obligation**, then gives the Node/Next form as the *example*. Score the obligation in the project's own toolchain:

| Toolchain | Manifest | Commit-msg hook | Pre-push soundness check | CI gate |
|:--|:--|:--|:--|:--|
| Node/Next | `package.json` | `commitlint` | `tsc --noEmit` | `lint → typecheck → test → build` |
| Python | `pyproject.toml` | `commitlint` (or any conventional-commit check) | `ruff`/`mypy` | `lint → typecheck → test` |
| Go | `go.mod` | same | `go vet` / `go build` | `vet → test → build` |
| Rust | `Cargo.toml` | same | `cargo check` | `clippy → test → build` |

A row marked ❌ must name an obligation the project genuinely lacks — **never** a Node file a non-Node project could never have. Where an obligation has no equivalent in the toolchain (a static site has no test step), mark it **N/A**, not ❌. The **agent roster** rows likewise scope to the project's *confirmed* set (from the profile), not a fixed list of role names — check that each confirmed agent carries the required wiring, not that a specific role file exists.

**Output:** Gap report in the format defined at the end of this skill. Then run `skills/skill-project-discard.md` — this skill finds what canon requires and the project lacks; that one finds what the project carries and canon never asked for. Present both reports together, then hand off to `skills/skill-project-upgrade.md` for remediation.

---

## Project Structure

- [ ] Two separate git repos: `<project>-meta/` and `<project>-app/`
- [ ] Both repos have `staging` as the default branch
- [ ] Both repos have `main` branch (for production promotion)

---

## Meta Repo

- [ ] `pipeline.md` exists with at least one active block, and follows the **Format contract** (phases are `### Phase N:` headers; tables are `ID | Task | Status | Notes`; the Status cell is exactly one emoji from the indicator set; a row with a block file names it in Notes as `Block `blocks/<id>.md``) — a deterministic reader depends on this shape
- [ ] `context.md` exists with project overview **and a `## Deploy` section** (Enabled + Success check) — the deploy gate of the definition-of-done reads it
- [ ] `principles.md` definition-of-done carries the **deploy gate**: PR-merged ≠ done — when a block declares a deploy check (`Deploy:` field, or the `context.md → Deploy` default) the change must deploy clean + verify post-deploy before the block is done; a failed deploy is not-done and must be fixed
- [ ] `principles.md` exists with agent behavior rules and inherits canon at the top (`Apply knowledge-base/principles-base.md first`). Does **not** carry a localized `## Shared Knowledge Base` section — that would duplicate canon §9 and `meta/agent.md §3.1, §3.2, §7.1, §7.2`. Inheritance is the contract; do not redocument the procedure.
- [ ] Every `agents/*.md` has the canonical Session-Start trigger bullet pointing at `{shared_knowledge_path}/meta/agent.md §3.1 + §3.2`. One bullet, no inline procedure detail.
- [ ] Every `skills/skill-session-end-*.md` has the canonical Session-End trigger bullet pointing at `{shared_knowledge_path}/meta/agent.md §4` (lessons) and `§7.2` (warning closure). One bullet, no inline procedure detail.
- [ ] `principles.md` and all `agents/*.md` and `skills/*.md` use the `{shared_knowledge_path}` placeholder or the project's configured KB path — **no machine-specific absolute paths** (`~/Spaceship/...`, `/Users/.../`, etc.) per `principles-base.md §14`
- [ ] `CLAUDE.md` exists — includes agents table and skills table
- [ ] Workspace `CLAUDE.md` Key Files section references the **42labs Design System canon** (`https://42labs.io/design`; an optional offline mirror may be referenced via a `~/`-relative path that resolves on the contributor's machine — never a machine-specific absolute path baked into the doc) — required so every agent loads the canon as a premise
- [ ] **Agent roster present and wired.** The kit ships a standard set (architect, engineer, data-architect, reviewer-code, reviewer-security); a project may run a different set — audit the **confirmed roster from the profile**, not these names. Each confirmed agent has its doc, and each has a matching `skills/skill-session-end-<role>.md`. A project running its own personas is compliant when *its* agents are fully wired — not when it happens to carry the kit's role names.
- [ ] `agents/flynn-local.md` present (thin wrapper pointing to `<tron-app>/modes/flynn/flynn.md`)
- [ ] `skills/skill-validate.md` present
- [ ] `skills/skill-review-cycle.md` present
- [ ] `skills/skill-review-code.md` present
- [ ] `skills/skill-security-scan.md` present
- [ ] `skills/skill-worktree-and-branching.md` present
- [ ] `blocks/block-template.md` present and carries the **`Merge:`** (`self | needs-user`) and **`Deploy:`** (`none | check`) header fields after `Reviewer class:` — active blocks may stamp them; default to `self` / inherit
- [ ] `logs/` has subdirs: `engineering/`, `architecture/`, `review-code/`, `review-security/`
- [ ] Ref formats present: `ref-session-log-format.md`, `ref-audit-report-format.md`, `ref-review-report-format.md`

> TRON is out of scope here. TRON owns its own seeding and its own audit of `tron.md` / `skill-tg-comms.md` / Telegram wiring — do not gate the project audit on those files.

---

## App Repo — Root Level

*(Rows are toolchain-scoped — see the scoping table at the top. `<root>` means the app repo root for a
flat layout, or the `app/` subdir for a monorepo layout, per the confirmed `APP_LAYOUT`.)*

- [ ] **Language version pinned**, where the toolchain pins one — `.nvmrc` (Node), `.python-version` / `[project.requires-python]` (Python), the `go` line in `go.mod`, `rust-toolchain.toml`. N/A for toolchains that don't pin.
- [ ] **A managed git-hook config at the app repo root** — `lefthook.yml` (no dot prefix) is the kit's tool; any equivalent that installs the two hooks below counts.
- [ ] **A commit-message hook** enforcing conventional, lowercase-subject commits — kit form: `commit-msg` running `commitlint`, scoped to `<root>`.
- [ ] **A pre-push soundness check** in the confirmed toolchain — kit form (Node): `pre-push` running `tsc --noEmit`. Python: `ruff`/`mypy`. Go: `go vet`. Whatever proves the code compiles/lints before it leaves the machine.
- [ ] **No pre-commit hook running the test suite** (too slow — tests run in CI). Toolchain-independent.
- [ ] `.env.example` documents all required env vars, grouped by concern
- [ ] `.github/workflows/` directory exists
- [ ] `mcp-setup.md` present and covers all integrations used by the project
- [ ] `services-setup.md` present and covers all services used by the project
- [ ] `docs/playbook-infra.md` present — covers secrets ref, rotation, per-service operational notes

---

## App Repo — Tooling Anchor (`<root>`)

*(`<root>` = the `app/` subdir for a monorepo layout, the repo root for a flat layout.)*

- [ ] `CLAUDE.md` exists at `<root>` — includes tech stack table and project structure
- [ ] **Conventional-commit config present at `<root>`** — kit form (Node): `commitlint.config.js` extending `@commitlint/config-conventional`. The commit-msg hook above must resolve against it. N/A only if the commit-msg hook needs no config file in this toolchain.

---

## Claude Code Configuration

*(Toolchain-independent — every project driven by Claude gets these.)*

- [ ] `.claude/settings.json` exists at workspace root (where Claude is invoked — NOT inside any repo)
- [ ] `vercel@claude-plugins-official` present in `enabledPlugins` (or absent for non-Vercel projects)
- [ ] `PostToolUse` hook present, matcher = `Edit|Write|MultiEdit`
- [ ] Hook command uses an **absolute path** to `<root>` (the tooling anchor — not a relative path)
- [ ] Hook fires after an Edit — no path errors in Claude terminal output
- [ ] Memory directory initialized: `~/.claude/projects/<encoded-workspace-path>/memory/MEMORY.md`
  - Path encoding: the full host workspace path with `/` replaced by `-` (illustrative shape: a path like `/Users/<name>/myproject` encodes to `-Users-<name>-myproject`). Generated at runtime from the actual host path; never persisted in tracked files.

---

## MCP + Integrations

- [ ] Supabase MCP configured — `SUPABASE_ACCESS_TOKEN` in shell env *(Supabase only)*
- [ ] GitHub MCP configured — `GITHUB_PAT` in shell env with correct permissions
- [ ] Vercel plugin authenticated via `/vercel authenticate` *(Vercel only)*
- [ ] Plain API key in `.env.local` + Vercel env *(Plain only)*
- [ ] `mcp-setup.md` in app repo documents all above integrations with setup steps and verify instructions

### Browser validation (always applicable — no project is exempt)

- [ ] One **devtools-class** browser MCP present in `.mcp.json` (e.g., Chrome DevTools MCP)
- [ ] One **automation-class** browser MCP present in `.mcp.json` (e.g., Playwright MCP)
- [ ] Devtools-class MCP verified — list pages or take screenshot of `about:blank` returns non-error
- [ ] Automation-class MCP verified — navigate + DOM snapshot returns a tree
- [ ] `app/docs/playbook-browser-testing.md` present (project-local copy or pointer to `knowledge-base/reference/guidelines-browser-testing.md`)
- [ ] `meta/skills/skill-validate.md` contains a §3 Browser MCP Validation section — mandatory gate when block touches UI/visible behavior
- [ ] `meta/skills/skill-review-code.md` (if present) contains the browser-validation row in Phase 1 audit
- [ ] Evidence directory convention documented — where screenshots / console / network / perf artifacts land (default: `~/Downloads/`)

---

## CI/CD

**Always required** *(the CI gate is universal; the steps inside it are the confirmed toolchain's):*
- [ ] `ci.yml` — triggers on all PRs + push to `main`
- [ ] `ci.yml` — runs the toolchain's **lint → typecheck → test → build** chain. Kit form (Node): `npm run lint` → `npx tsc --noEmit` → `npm test` → `npm run build`. Python: `ruff` → `mypy` → `pytest`. Go: `go vet` → `go test` → `go build`. A step with no equivalent (a static site has no test) is omitted, not faked.
- [ ] `ci.yml` — pins the language version from the repo, not hardcoded — kit form: `node-version-file: '.nvmrc'`; the equivalent `setup-*` pin for other toolchains.
- [ ] `ci.yml` — has concurrency block cancelling in-progress runs on same ref
- [ ] `pr-base-guard.yml` — blocks PRs to `main` from any branch except `staging` or `hotfix/*`

**Conditional:**
- [ ] `staging-db.yml` — auto-applies migrations to staging on PR *(Supabase only)*
- [ ] `deploy-notify.yml` — posts Vercel deploy events to Slack channels *(Vercel + Slack)*
- [ ] `release-please.yml` — auto-generates changelog + GitHub Releases *(if public changelog)*
- [ ] `release-notify.yml` — triggers email blast on release publish; requires email provider env var *(if subscriber emails + Brevo)*
- [ ] `e2e.yml` — end-to-end test suite *(if Playwright)*
- [ ] `stress.yml` — stress/load tests *(if load requirements)*

---

## Branching

- [ ] Default branch is `staging` on both repos
- [ ] `main` branch protection: no direct push
- [ ] `staging` branch protection: no direct push
- [ ] Auto-merge NOT armed (no `gh pr merge --auto` in any workflow)
- [ ] Worktree location documented: `<workspace>/worktrees/` (workspace-internal, not `~/worktrees/`, never `/tmp`)
- [ ] Commit subjects are lowercase — enforced by the commit-message hook + the CI conventional-commit step (kit form: Lefthook `commit-msg` + `commitlint`)

---

## Services

*(Audit only for services in the confirmed project profile)*

### Railway / LiteLLM
- [ ] `infra/Dockerfile.litellm` — pinned to exact stable image tag (e.g. `main-v1.63.14-stable`)
- [ ] `infra/Dockerfile.litellm` — does NOT use `main-stable` (unpinned, causes OOM from Prisma migration loop)
- [ ] `infra/litellm_config.yaml` — defines virtual model aliases; does NOT include `tag_budget_config` (Enterprise-only, causes crash)
- [ ] `infra/litellm-entrypoint.sh` — drops `litellm_spend_logs` view before startup (prevents cold-start migration conflict)
- [ ] Railway project created with Postgres add-on
- [ ] `LITELLM_API_KEY` + `LITELLM_BASE_URL` set in Vercel (all scopes)
- [ ] Spend cap configured; `/ui` dashboard accessible

### Slack
- [ ] All required channels created (see `services-setup.md#slack` for channel map)
- [ ] Webhook env vars set in Vercel: `SLACK_WEBHOOK_FINANCIAL`, `SLACK_WEBHOOK_AFFILIATES`, `SLACK_WEBHOOK_DEPLOYS_STAGING`, `SLACK_WEBHOOK_DEPLOYS_PROD`, `SLACK_WEBHOOK_DIGEST`, `SLACK_WEBHOOK_INFRA`
- [ ] Native integrations wired: Sentry → `#errors-sentry`, Plain → `#support-plain`
- [ ] Pipedream relay workflow live for Railway → `#infra-railway` (bypasses Railway Slack Muxer null-blocks bug)
- [ ] Pipedream URL + rotation documented in `playbook-infra.md`

### Brevo
- [ ] `BREVO_API_KEY` set in Vercel **production scope only** (unset = no-op in staging/preview)
- [ ] `BREVO_SENDER_EMAIL` + `BREVO_SENDER_NAME` set in Vercel
- [ ] Sender domain verified (SPF, DKIM, DMARC DNS records confirmed)
- [ ] Send paths no-op gracefully when `BREVO_API_KEY` is unset

### Polar
- [ ] `POLAR_SERVER=sandbox` in staging Vercel env; `POLAR_SERVER=production` in production
- [ ] `POLAR_ACCESS_TOKEN` set per environment
- [ ] `POLAR_WEBHOOK_SECRET` set per environment
- [ ] Webhook handler at `app/api/webhooks/polar/route.ts` — verifies signature before processing
- [ ] Events handled: `subscription.created`, `subscription.updated`, `subscription.canceled`, `subscription.revoked`

### Sentry
- [ ] `SENTRY_DSN` set in Vercel **production scope only**
- [ ] `@sentry/nextjs` installed
- [ ] `sentry.client.config.ts` + `sentry.server.config.ts` present
- [ ] `next.config.ts` wraps build with `withSentryConfig()`
- [ ] `SENTRY_AUTH_TOKEN` set as GitHub secret for source map uploads in CI
- [ ] Sentry → `#errors-sentry` Slack integration wired

### Matomo
- [ ] `NEXT_PUBLIC_MATOMO_URL` + `NEXT_PUBLIC_MATOMO_SITE_ID` set in Vercel
- [ ] Matomo script in root layout — disabled on non-production `VERCEL_ENV`
- [ ] `trackEvent(category, action, name?)` utility in `lib/analytics.ts`
- [ ] Key user actions instrumented: signup, subscription, key feature use

### FirstPromoter
- [ ] `NEXT_PUBLIC_FP_ACCOUNT_ID` set in Vercel (all scopes)
- [ ] `FP_API_KEY` set in Vercel (production only)
- [ ] Tracking script self-hosted at `app/public/fpr.js` — NOT loaded from CDN
- [ ] Inline stub + deferred script in root layout
- [ ] Signup attribution wired in auth callback (reads `_fprom_ref` cookie)
- [ ] Sale attribution wired in Polar `subscription.created` webhook handler

---

## Portable Worktrees

Implements `42hq/knowledge-base/principles-base.md §14 Portability — Relative-path worktrees`. Required so the workspace tree can be moved/renamed as a unit without `git worktree repair`.

- [ ] Git version on the host is ≥ 2.48 (`git --version`)
- [ ] `<workspace>/worktrees/` directory exists (workspace-internal worktree base)
- [ ] `<app>/scripts/setup-repo.sh` exists, is executable (`chmod +x`), and has body byte-identical to `tron/tron-app/templates/project-scaffold/templates/meta/scripts/setup-repo.sh`
- [ ] `<meta>/scripts/setup-repo.sh` exists, is executable, body identical to canonical
- [ ] The app's **dependency-install step auto-runs `setup-repo.sh`** — kit form (Node): a `"prepare": "../scripts/setup-repo.sh"` in `<root>/package.json`, firing on `npm`/`pnpm install`. Other toolchains: the equivalent post-install/bootstrap hook, or a documented one-time `setup-repo.sh` run in the app README where the toolchain has no install hook.
- [ ] `<app>` repo git config: `core.repositoryformatversion = 1`, `extensions.relativeWorktrees = true`, `worktree.useRelativePaths = true`
- [ ] `<meta>` repo git config: same three keys set
- [ ] Existing worktrees in `.git/worktrees/*/gitdir` use **relative** paths (`../../../worktrees/<repo>--<branch>/.git`), not absolute
- [ ] `meta/skills/skill-worktree-and-branching.md` documents `<workspace>/worktrees/` as the worktree base path (not `~/worktrees/`) and includes a §Setup section pointing to `scripts/setup-repo.sh`
- [ ] App repo `README.md` (or equivalent setup doc) mentions the Git ≥ 2.48 requirement and how the bootstrap runs — auto-applied on dependency install where the toolchain has an install hook (kit form: `pnpm`/`npm install`), or the one-time `setup-repo.sh` run where it doesn't

---

## Memory

- [ ] `~/.claude/projects/<encoded-path>/memory/MEMORY.md` initialized
- [ ] At least 3 feedback entries covering key project-specific guidance
- [ ] User profile entry present
- [ ] Project context entry present

---

## Gap Report Format

After scoring, produce:

```
## Gap Report — <Project Name> — <Date>

### Project Profile
[list of confirmed services]

### Gaps

| Item | Status | Severity | Effort |
|------|--------|----------|--------|
| `.claude/settings.json` PostToolUse hook | ❌ | Critical | 5 min |
| `lefthook.yml` at repo root | ⚠️ (inside app/ subdir) | Critical | 5 min |
| `ci.yml` — tsc step missing | ⚠️ | Important | 15 min |

### Summary
- Critical: N items
- Important: N items
- Nice-to-have: N items
- Total effort estimate: ~Xh
```

Do **not** present the gap report on its own. Run `skills/skill-project-discard.md` next and present both
reports in one pass — the operator rules on what to add and what to remove in the same sitting. Only then
hand off to `skills/skill-project-upgrade.md`.
