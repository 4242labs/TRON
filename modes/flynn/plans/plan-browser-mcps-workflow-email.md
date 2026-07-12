## Plan: Browser MCPs + Validation Workflow + Email Scope

> **⚠ Superseded (2026-07-05):** the `new-project-template/` kit this plan edits is retired; scaffold templates now live in `tron/tron-app/templates/project-scaffold/`. Retained as a historical record — current state in `agents/super-m/plans/plan-tron-sot-cleanup.md`.

**Created:** 2026-04-23
**Revised:** 2026-04-23 (R2 — architect feedback: TD audit task, Polar sandbox cleanup, memory-file path fix, Topic 1 split, MCP-failure echo, 42Agents PR-convention resolved at pre-step, verify-rg tightened)
**Scope:** Hiresling.ai (immediate) + 42hq templates (propagation)
**Execution order:** four topics are independent; recommended sequence 1 → 2 → 3 → 4; Topic 1 splits into 1a (skills) and 1b (agents) to reduce blast radius; all preceded by a single architect pre-step (block-spec drafting + 42Agents PR-convention confirmation).

---

## Why

Four adjustments must land together as a process correction:

1. Two browser-testing MCPs (Chrome DevTools MCP, Playwright MCP) are now available but not wired into any agent's flow. Engineers and reviewers should use them for every block that touches UI or visible behavior.
2. The MCPs are undocumented — no capability matrix, no "when to use which", no command/example reference for agents to consult.
3. Hiresling has accumulated references to a personal email (`anquadros@gmail.com`) and a now-redundant test persona (`tisuang@gmail.com`) across docs, seeds, and live TDs. Going forward only two addresses are valid: `hiresling@42labs.io` (admin / paywall-bypass / owner) and `42piratas@gmail.com` (end-user test, absorbs the former `tisuang@` role). Historical session logs and worktree copies are exempt.
4. Engineers currently open PRs and update docs as if work were done, before the user has validated. Correct flow is: build → full local validation (incl. UI via MCPs) → user-test gate (if anything visible/behavioral/workflow-changing) → user approves → PR/CI → re-validate after merge to trunk → user manually triggers session-end → only then mark blocks done and update docs.

All four apply first to Hiresling and then to 42hq templates so every project inherits the correction.

---

## Pre-step (architect, blocking all four topics)

Before any engineering branch is opened, the architect drafts block specs in `hiresling-meta/pipeline.md` + `hiresling-meta/blocks/` for each topic. No engineering work starts until the user approves the specs. Ref: `feedback_no_code_without_approval`, `feedback_architect_scope`.

- [ ] `blocks/{id}-browser-mcps-flow-skills.md` — skill-level wiring (Topic 1a)
- [ ] `blocks/{id}-browser-mcps-flow-agents.md` — agent-level wiring (Topic 1b)
- [ ] `blocks/{id}-browser-mcps-docs.md` — capability playbook + guideline (Topic 2)
- [ ] `blocks/{id}-email-scope.md` — canonical emails + purge + seed rewrite + **embedded TD-audit task** (Topic 3); the block spec must itemize every live `anquadros@` / `tisuang@` hit (TD rows, block specs, seed rows, playbook rows) as a numbered checklist with per-row intended substitution — PR diff reviewer verifies row by row, not a blanket rg-replace
- [ ] `blocks/{id}-email-scope-polar.md` — Polar sandbox customer cleanup: the existing `tisuang@gmail.com` customer record in Polar sandbox (subscription history, webhooks) does NOT transfer to `42piratas@gmail.com`. Task: archive/delete `tisuang@` customer in Polar sandbox, create a fresh `42piratas@gmail.com` customer, re-run the Polar sandbox subscription flow to regenerate state needed by staging E2E tests (referral conversion, webhook delivery)
- [ ] `blocks/{id}-validation-flow.md` — 6-stage flow rewrite across skills/agents/principles (Topic 4)

Architect also drafts pipeline one-liners and acceptance criteria. User review gate before engineer touches anything.

**Also at pre-step:** confirm 42hq's commit convention (direct-to-main or PR). Record the answer in the relevant block specs' execution-notes; do not defer to execution.

---

## Topic 1 — Browser-testing MCPs wired into engineer + reviewer flow

Split into **1a (skills)** and **1b (agents)** to reduce blast radius. 1a lands first; 1b follows after 1a is merged and validated.

### Topic 1a — Hiresling skills

Files to change:

- [ ] `hiresling-meta/skills/skill-block-completion.md` — insert a dedicated §Browser Validation section that feeds §4 (a11y), §6 (perf), §9 (acceptance-criteria verification). Mandatory whenever the block touches UI or visible behavior. Evidence: screenshots to `~/Downloads/`, console + network capture, perf trace where applicable. **MCP-failure rule (echo of playbook):** if Chrome DevTools MCP fails, proceed with Playwright MCP; if Playwright fails, proceed with Chrome DevTools; if both fail, stop — do not skip validation, escalate to user
- [ ] `hiresling-meta/skills/skill-review-code.md` — add §3.9 Browser Validation row to Phase 3 audit checklist (severity BLOCKER for UI/visible-behavior changes); Phase 4 Output requires browser-evidence linkage
- [ ] `hiresling-meta/skills/skill-review-cycle.md` — §7 Block-Level Validation adds browser-evidence row to the four-signal check for UI-touching blocks
- [ ] `hiresling-meta/principles.md` — add browser-testing to §Skills registry; note it as mandatory gate for UI work

### Topic 1b — Hiresling agents

Files to change (after 1a lands):

- [ ] `hiresling-meta/agents/engineer.md` — `## Block Completion` section (line ~74, not "Definition of Done"): add browser-testing responsibility to the local-validation step
- [ ] `hiresling-meta/agents/reviewer-code.md` — add browser-testing verification to review procedure
- [ ] `hiresling-meta/agents/reviewer-branding-design.md` — browser tests become the primary validation tool for visual/interaction checks (capture screenshots, interaction recordings)
- [ ] `hiresling-meta/agents/reviewer-security.md` — browser tests required when auditing auth flows, CSP, cookies, redirects, any client-visible security surface

### 42hq

Files to change:

- [ ] `knowledge-base/skills/skill-code-review.md` — add browser-testing section inside Phase 1 Audit Execution (MCP-agnostic wording, link to `reference/guidelines-browser-testing.md`)
- [ ] `knowledge-base/skills/skill-pre-deploy-verification.md` — add new §7 UI Validation before the Deploy Workflow section
- [ ] `art-director/art-director.md` + `art-director/skills/` — browser MCPs are the primary hands-on validation tool for art direction (visual regression, interaction capture)
- [ ] `new-project-template/skills/skill-audit.md` — browser-testing capability check when auditing an existing project
- [ ] `new-project-template/agents/scaffolder.md` + `new-project-template/agents/upgrader.md` — ensure new/upgraded projects have browser-testing MCPs configured and referenced in generated agent/skill templates

---

## Topic 2 — Browser-testing MCPs documentation

### Hiresling

Files to change:

- [ ] `hiresling-app/docs/playbook-browser-testing.md` (new) — purpose, capability matrix (Chrome DevTools MCP vs Playwright MCP), when to use which, setup/config notes, canonical test patterns (navigate, click, fill, screenshot, console/network capture, perf trace, heap snapshot, CPU/network throttling, attach to existing session), example invocations, evidence-capture conventions, MCP-failure fallback note (if one MCP fails, proceed with the other; if both fail, stop — do not skip validation)
- [ ] `hiresling-meta/context.md` — no "Tools & Integrations" section exists today; add a new `## Tools & MCPs` section (after `## Conventions`) that lists browser-testing MCPs + links to the playbook
- [ ] `CLAUDE.md` (root) — add `playbook-browser-testing.md` to Key Files table

### 42hq

Files to change:

- [ ] `knowledge-base/reference/guidelines-browser-testing.md` (new) — same capability matrix + decision framework, written as provider-agnostic reference for any project; deep-link to current MCP docs (Microsoft Playwright MCP, Google Chrome DevTools MCP); include the MCP-failure fallback rule
- [ ] `knowledge-base/reference/guidelines-frontend-stacks.md` — cross-reference new browser-testing guideline
- [ ] `knowledge-base/reference/guidelines-ui-ux.md` — cross-reference new browser-testing guideline

---

## Topic 3 — Email scope + personal-email purge

Canonical emails going forward (Hiresling only):

- `hiresling@42labs.io` → admin / owner / paywall-bypass whitelist
- `42piratas@gmail.com` → end-user test account (absorbs former `tisuang@` role — Polar sandbox flow, referral E2E, etc.)
- `anquadros@gmail.com` → retired from all live files
- `tisuang@gmail.com` → retired; use `42piratas@gmail.com` instead

Semantic substitution rule per reference: where `anquadros@` meant "whitelisted admin account" → `hiresling@42labs.io`; where it meant "generic end-user test" → `42piratas@gmail.com`. Context-judge each hit.

### Hiresling — code

- [ ] `hiresling-app/app/supabase/seed.sql` — replace `anquadros@gmail.com` whitelist seed with `hiresling@42labs.io`; remove `tisuang@gmail.com` whitelist row (role absorbed into `42piratas@gmail.com`); update the `hiresling_user_whitelist` INSERTs and the two `-- ...@` comment lines
- [ ] Verify: any migration or fixture that inserts user rows with these addresses (`rg -n '@gmail\.com' hiresling-app/app/supabase/` + `hiresling-app/app/scripts/`)

### Hiresling — docs & specs

- [ ] `hiresling-app/docs/playbook-infra.md` line 131 — Resend account login references `anquadros@gmail.com`; replace with `hiresling@42labs.io` (or flag to user if the real Resend account login must stay personal — then move out of the public doc)
- [ ] `hiresling-app/docs/playbook-infra.md` — add "Canonical Emails" subsection documenting the two live roles
- [ ] `hiresling-meta/context.md` — add "Canonical Emails" subsection under project identity
- [ ] `hiresling-meta/pipeline.md` — 15+ live TDs reference `anquadros@` and `tisuang@` as test-instruction artifacts (TD-57, TD-62, TD-69, TD-70, TD-72, TD-73, TD-74, TD-75, TD-76, TD-97, TD-102, TD-109, TD-122, S6-15 notes, etc.). **Do not use a blanket rg-replace.** The block spec's embedded TD-audit task itemizes each hit with the intended substitution; PR diff reviewer confirms every row individually before merge. TD-102 already excludes `anquadros@` and `tisuang@` — keep that note but mention the new canonicals
- [ ] `hiresling-meta/blocks/47-02-staging-smoke-tests.md` — live, substitute per semantic rule
- [ ] `hiresling-meta/blocks/47-04-i18n-smoke-tests.md` — live, substitute per semantic rule
- [ ] `hiresling-meta/blocks/42-06-internal-referrals-validation.md` — live, substitute per semantic rule
- [ ] `hiresling-meta/principles.md` — if it mentions staging test accounts, update

### Hiresling — purge verification

- [ ] `rg -n 'anquadros|tisuang' hiresling-app/ hiresling-meta/ --glob '!hiresling-meta/logs/**' --glob '!**/worktrees/**' --glob '!hiresling-meta/blocks/archive/**'` returns zero hits
- [ ] `rg -l 'anquadros|tisuang' hiresling-meta/logs/ hiresling-meta/blocks/archive/ hiresling-app/**/worktrees/` — historical / stale copies, expected to still have hits; no action required (rebased-away worktrees will self-clean per W3 cleanup)

### 42hq

No action on live files — templates must not hard-code any personal address.

- [ ] Verify: `rg -n 'anquadros|tisuang' 42hq/ --glob '!super-m/logs/**' --glob '!**/logs/**' --glob '!super-m/plans/**'` returns zero hits (plans exempt). Do **not** `rg` for `@gmail\.com` in templates — `42piratas@gmail.com` is a valid canonical once templates reference it as an example, so the bare pattern will false-positive

### Memory updates

- [ ] Create `project_staging_test_accounts.md` (auto-memory, project type) at `~/.claude/projects/-Users-42piratas-Spaceship-hiresling-ai/memory/` — body: admin `hiresling@42labs.io` (whitelisted, paywall bypass), end-user test `42piratas@gmail.com` (Polar sandbox, referral E2E, absorbs former `tisuang@` role). Note `anquadros@` and `tisuang@` retired 2026-04-23. Add the pointer to `MEMORY.md`. (Previous file of this name was deleted earlier this session; re-creating with new canonical content.)

---

## Topic 4 — Corrected validation workflow

### Target flow (every block, every agent)

1. **Build**
2. **Local validation** — every acceptance criterion verified, including UI via browser MCPs
3. **User-test gate** — mandatory if the change is visible, behavioral, or workflow-altering; skippable only for truly invisible backend (pure internal refactor, server-only log change, etc.). Default: gate applies.
4. **User approves → PR opened → CI runs**
5. **Post-merge re-validation** — once branch lands on trunk (hiresling-meta: `main`; hiresling-app: `staging` while it exists, `main` post-split), full criteria re-run; user-test gate re-applied with same rule
6. **User manually triggers session-end** — only then block marked ✅ Done, pipeline/archive updated, docs synced

### Hiresling — skills

- [ ] `hiresling-meta/skills/skill-block-completion.md` — rewrite:
  - §1–§9 stay (local validation gate), plus the new §Browser Validation from Topic 1
  - §10 User Verification List becomes the user-test gate artifact (output consumed at step 3 of the flow)
  - **Remove** §11 Core Docs Check from this skill
  - **Remove** §12 Block Status Update from this skill
  - End of skill: hand off to user for step 3 user-test gate, then PR opens only after user approves
- [ ] `hiresling-meta/skills/skill-session-end-engineer.md` — rewrite:
  - Top note: runs only when user explicitly triggers session-end, never after PR merge
  - New §: Post-merge re-validation (flow step 5) — re-run acceptance criteria + browser tests on trunk
  - Absorb §11 Core Docs Check (relocated from block-completion)
  - Absorb §12 Block Status Update (relocated from block-completion) — now flips status to ✅ only here
  - **Fix pre-existing bug:** §3 Git Sync currently says `git push origin main` directly — violates `feedback_no_direct_staging_edits`. Rewrite to require feature branch + PR in all cases
- [ ] `hiresling-meta/skills/skill-session-end-architect.md`, `skill-session-end-reviewer-code.md`, `skill-session-end-reviewer-security.md`, `skill-session-end-data-architect.md` — top note: user-explicit-trigger only
- [ ] `hiresling-meta/skills/skill-review-cycle.md` — reconcile §11 Archive Completed Blocks with new rule. Cycle review is itself a user-initiated event, so batch-archival inside it IS the user-triggered session-end equivalent for that scope. Add note to that effect so future rewriters don't regress it

### Hiresling — agents & principles

- [ ] `hiresling-meta/agents/engineer.md` — `## Block Completion` section (line ~74) rewritten to the 6-stage flow; remove any wording that implies PR-open == work-complete
- [ ] `hiresling-meta/principles.md` — codify the 6-stage flow under §Skills or a new §Workflow section; cross-reference `feedback_no_pr_before_local_validation`, `feedback_no_deploy_without_local_test`, `feedback_no_done_before_user_approval`

### 42hq

- [ ] `knowledge-base/principles-base.md` §12 Definition of Done — extend with the 6-stage flow (do not add a new section; §12 is already the canonical home)
- [ ] `knowledge-base/skills/skill-pre-deploy-verification.md` — align with flow step 5 (post-merge re-validation) + note that deploy only happens after user trigger
- [ ] `knowledge-base/skills/skill-change-tracking.md` — §4 Verify at Session End: mark-done gate is user-triggered session-end, not PR merge; align with `principles-base.md §12`
- [ ] `new-project-template/spec.md` — scaffolder must emit `skill-block-completion.md` + `skill-session-end-{role}.md` templates with the 6-stage flow pre-wired (not merely "reference" it); update the spec's generated-artifact list to reflect this
- [ ] `new-project-template/agents/scaffolder.md` — encode the emission requirement

### Memory updates

- [ ] New `feedback_six_stage_flow.md` (auto-memory, feedback type): the 6-stage flow is the single rule for all blocks; why: user correction 2026-04-23 — agents were opening PRs and marking done prematurely; how to apply: every role, every block, no exceptions
- [ ] New `project_browser_mcps.md` (auto-memory, reference type): Chrome DevTools MCP + Playwright MCP are the canonical browser-validation tools; pointer to `playbook-browser-testing.md` and `guidelines-browser-testing.md`

---

## Out of scope

- Retrofitting closed/done blocks with new validation evidence — applies going forward only
- CI wiring to enforce browser-test runs on PR — future block; this plan covers agent/process layer only
- MCP installation/configuration across other machines — assumes MCPs are already installed locally
- Stale worktree cleanup (W3) — tracked separately; email purge excludes worktree paths so it is not blocked by W3
- Deciding whether the Resend account login in `playbook-infra.md` line 131 stays personal or moves to `hiresling@42labs.io` — open question for the user; default patch is substitute-and-flag

---

## Execution notes

- **Pre-step:** architect drafts six block specs (1a + 1b + 2 + 3 + 3-polar + 4) in `pipeline.md` + `blocks/`; user approves before any engineer branch opens. Also at pre-step: confirm 42hq commit convention (direct vs PR) and record in block specs
- **Six separate PRs**, in order: 1a skills → 1b agents → 2 docs → 3 email purge → 3-polar sandbox cleanup → 4 workflow correction. Each independently mergeable
- **Hiresling PRs:** branch names per commitlint lowercase rule (`chore/b{id}-browser-mcps-flow-skills`, etc. — real block IDs assigned at pre-step)
- **42hq changes:** convention resolved at pre-step, not at execution
- **Every PR:** user validates locally before merge; no auto-merge
- **CI monitoring:** `gh pr checks {PR} --watch` after push; do not proceed until green (per `feedback_monitor_ci`)
- **Rebase before push:** hiresling-app on `origin/staging`, hiresling-meta on `origin/main` (per `feedback_always_rebase`)

---

## Verification

After all four topics land:

- [ ] Pick a pending UI-touching block; run through engineer flow end-to-end — confirm browser MCPs are invoked at local-validation step, user-test gate fires before PR, session-end does not fire until user triggers, status flips to ✅ only inside session-end
- [ ] `rg -n 'anquadros|tisuang' hiresling-app/ hiresling-meta/ --glob '!hiresling-meta/logs/**' --glob '!**/worktrees/**' --glob '!hiresling-meta/blocks/archive/**'` → zero hits
- [ ] `rg -n 'anquadros|tisuang' 42hq/ --glob '!super-m/logs/**' --glob '!**/logs/**' --glob '!super-m/plans/**'` → zero hits
- [ ] `playbook-browser-testing.md` exists, linked from `CLAUDE.md` Key Files table and from `hiresling-meta/context.md` §Tools & MCPs
- [ ] `guidelines-browser-testing.md` exists under `knowledge-base/reference/` and is cross-linked from UI/UX + frontend guidelines
- [ ] `knowledge-base/principles-base.md §12` contains the 6-stage flow
- [ ] `hiresling-meta/skills/skill-block-completion.md` no longer contains §11 Core Docs Check or §12 Block Status Update
- [ ] `hiresling-meta/skills/skill-session-end-engineer.md` §3 Git Sync uses feature branch + PR, not direct push to main
- [ ] `hiresling-app/app/supabase/seed.sql` whitelist seeds `hiresling@42labs.io` + `42piratas@gmail.com`, no `anquadros@` or `tisuang@`
- [ ] Polar sandbox: `tisuang@` customer archived/deleted, `42piratas@gmail.com` customer created, subscription flow re-run end-to-end
- [ ] Memories: `project_staging_test_accounts.md` re-created with new canonicals; new `feedback_six_stage_flow.md` + `project_browser_mcps.md` present; all three linked from `MEMORY.md`
