# Skill: Project Profile (existing)

Profiling step for the upgrade flow. Determines which templates, services, and audit rows apply to a project that **already exists**.

Read the repo, infer the answers, present them for confirmation. Lock the confirmed `{profile, values}` pair before handing off to `skill-project-audit.md`. **No stubs for skipped services** — if a service is not confirmed, its templates, audit rows, and service-setup sections are omitted entirely.

**TRON is out of scope.** TRON seeds itself when the operator activates it in a project — the audit and upgrade flows do not ask about it, do not copy `tron.md`/`skill-tg-comms.md`, and do not audit TRON wiring.

> New projects are not KONDO's. A project that doesn't exist yet is scaffolded by `/tron-scaffold`, which runs its own fresh-profile skill.

---

## Step 1 — App shape (2 questions)

**Ask these first — they decide which audit rows even apply.** Canon's workflow discipline is universal
(two repos, a staging gate, hooks, protected branches, CI that gates merges); the *tools that implement
it* are not. A Python service has no `package.json`, a Go binary has no `tsc`. Auditing a non-Node
project against Node-specific rows produces a page of false gaps — the exact defect this step exists to
prevent.

| # | Question | Determines |
|---|----------|-----------|
| A | **App toolchain?** — Node/Next.js · Python · Go · Rust · static/other. (More than one? Name the primary; the app-repo rows scope to it.) | Which form each app-repo row takes — the commit-message hook, the pre-push compile/lint check, the CI lint→typecheck→test→build steps, the dependency-install bootstrap all resolve to *this* toolchain's equivalent |
| B | **App-repo layout?** — monorepo with an `app/` subdirectory (Next.js default) · flat single-package at repo root | Where the tooling files live — hooks' `root:`, the config files, the Claude hook path all anchor here |

Read the app repo before asking: a `package.json` + `next.config.*` means Node/Next; a
`requirements.txt` / `pyproject.toml` means Python; a `go.mod` means Go; a `Cargo.toml` means Rust.
Infer, then confirm.

**The rule the audit inherits:** every app-repo obligation is checked as an *obligation*, in the
confirmed toolchain's own form. "There is a pre-push check that the code compiles" is the obligation;
`npx tsc --noEmit` is only its Node form. A Python project satisfies the same obligation with its own
type/lint gate, or is exempt where the obligation has no equivalent — never marked ❌ for lacking a
Node file it could never have.

---

## Step 2 — Service profile (11 questions)

| # | Question | Determines |
|---|----------|-----------|
| 1 | Project type? (SaaS / internal tool / API service / other) | Tier of services to include |
| 2 | Hosting: Vercel? Railway? Both? Neither? | `deploy-notify.yml`, Vercel plugin, `services-setup.md#railway` |
| 3 | DB: Supabase? Other? None? | `staging-db.yml`, `mcp-setup.md#supabase-mcp` |
| 4 | Payments: Polar? Stripe? None? | `services-setup.md#polar` |
| 5 | Email notifications: Brevo? Resend? None? | `services-setup.md#brevo` |
| 6 | Error monitoring: Sentry? None? | `services-setup.md#sentry` |
| 7 | Analytics: Matomo? None? | `services-setup.md#matomo` |
| 8 | Affiliates: FirstPromoter? None? | `services-setup.md#firstpromoter` |
| 9 | Support ticketing: Plain? None? | `mcp-setup.md#plain` |
| 10 | Slack notifications? (yes / no) | `services-setup.md#slack`, `deploy-notify.yml` |
| 11 | AI proxy: LiteLLM on Railway? Direct API? None? | `services-setup.md#railway`, `infra/` templates |

### Procedure

Read each of the following before asking the operator anything; fill the table with inferred answers and a confidence note, then ask them to confirm or correct each row:

- Workspace + app `AGENTS.md` / `CLAUDE.md`
- The app's manifest — `package.json` (Node), `pyproject.toml` / `requirements.txt` (Python), `go.mod` (Go), `Cargo.toml` (Rust) — and its `.env.example`
- The app's CI directory (`.github/workflows/`)
- `infra/` (if present)
- `meta/agents/`, `meta/skills/`
- `meta/principles.md`, `meta/context.md`

Unconfirmed services are excluded from downstream audit and upgrade work.

---

## Step 3 — Project values

| Value | Example |
|-------|---------|
| `PROJECT_NAME` | `myproject` |
| `WORKSPACE_PATH` | `~/projects/myproject` |
| `APP_REPO_NAME` | `myproject-app` |
| `APP_REPO_ROOT` | `~/projects/myproject/myproject-app` |
| `APP_SUBDIR` | `~/projects/myproject/myproject-app/app` |
| `META_REPO_NAME` | `myproject-meta` |
| `META_REPO_ROOT` | `~/projects/myproject/myproject-meta` |
| `APP_TOOLCHAIN` | `node` \| `python` \| `go` \| `rust` \| `static` *(from Step 1A)* |
| `APP_LAYOUT` | `subdir` (`app/`) \| `flat` *(from Step 1B)* |
| `GITHUB_ORG` | `alice` |
| `RUNTIME_VERSION` | `24` (Node) · `3.12` (Python) · etc. — the pinned language version, if the toolchain pins one |
| `STAGING_SUPABASE_URL` | `https://xyz.supabase.co` *(if Supabase)* |
| `PROD_SUPABASE_URL` | `https://abc.supabase.co` *(if Supabase)* |
| `VERCEL_PROJECT_NAME` | `myproject` *(if Vercel)* |

Fill these from disk; ask the operator only for what the repo can't tell you.

---

## Output

A locked `{profile, values}` pair — **including the app toolchain and layout from Step 1** — passed verbatim to `skill-project-audit.md` and `skill-project-discard.md`. Re-confirm with the operator before handoff. No upgrade work proceeds without an explicit lock; the audit scopes every app-repo row to the locked toolchain; and the discard pass is only safe once the profile is locked (a workflow for a service the project doesn't use is cruft; the same file in a project that does use it is canon).
