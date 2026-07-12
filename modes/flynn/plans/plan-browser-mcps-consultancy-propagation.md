# Plan: Browser MCPs + 6-Stage Flow — 42Agents Propagation

> **⚠ Superseded (2026-07-05):** the `new-project-template/` kit this plan edits is retired; scaffold templates now live in `tron/tron-app/templates/project-scaffold/`. Retained as a historical record — current state in `agents/super-m/plans/plan-tron-sot-cleanup.md`.

**Created:** 2026-04-23
**Scope:** 42hq only — `knowledge-base/`, `new-project-template/`, `art-director/`
**Parent plan:** `plan-browser-mcps-workflow-email.md` (R2, Hiresling-scope portions already delivered via hiresling-meta PR #73 merged 2026-04-23)
**Execution owner:** super-m (not engineer — this is process/doc propagation, same role that authored parent plan)

---

## Why

The Hiresling-scope process correction landed in hiresling-meta PR #73 (Phase 48 block specs B48-01 / B48-02 / B48-03). Two of those topics — browser MCPs wired into workflow, and the 6-stage validation flow — must propagate into 42hq so every downstream project scaffolded from `new-project-template/` inherits the correction. Email scope (B48-02) is Hiresling-specific and does **not** propagate.

42Agents templates must not hard-code any project-specific account, URL, or persona. Everything below is provider-agnostic / project-agnostic.

---

## Out of scope

- Anything in `hiresling-app/` or `hiresling-meta/` — delivered via PR #73
- Email-scope work (B48-02 equivalent) — Hiresling-specific
- Adding new agent roles (e2e-tester, coo) — tracked separately on the session agenda
- Retrofitting already-scaffolded downstream projects with browser MCPs — applies to new scaffolds only; existing projects update out-of-band when each touches its own workflow

---

## Topic A — Browser MCPs in 42Agents templates (mirrors Hiresling B48-01)

### A1. `knowledge-base/reference/guidelines-browser-testing.md` — new file

Provider-agnostic reference. Eight sections:

1. **Purpose** — why browser validation is a first-class procedure, not nice-to-have. When it is mandatory (any UI-touching or visible-behavior change).
2. **Capability matrix** — MCP-agnostic columns (navigate/click/fill/screenshot, console/network capture, perf trace + insight, CPU/network throttling, heap snapshot, Lighthouse, attach-to-session, DOM snapshot + a11y tree, multi-tab, file upload, dialog handling). Rows mark "typical devtools-class MCP" vs "typical automation-class MCP". Deep-link to current reference providers: Microsoft Playwright MCP, Google Chrome DevTools MCP.
3. **Decision framework** — principles-based (not provider-specific):
   - Deep tracing / throttling / heap / Lighthouse / attach-to-session → devtools-class MCP
   - Scripted multi-step flows with assertions → automation-class MCP
   - One-off probes → either; prefer devtools for debugging, automation for reproducibility
4. **Evidence-capture conventions** — project-agnostic: screenshots + console + network capture, linked into whatever completion-gate equivalent exists. File-name convention: `{block-or-task-id}-{check}-{timestamp}.{png|json}`. Location: project's conventional artifact-dump directory (e.g., `~/Downloads/` for Hiresling; project-specific otherwise).
5. **MCP-failure fallback rule** — verbatim: *"If one MCP fails, proceed with the other. If both fail, stop — do not skip validation. Escalate to user."*
6. **Integration points** — where this guideline plugs in: `skill-code-review.md`, `skill-pre-deploy-verification.md`, `skill-change-tracking.md`, `art-director/` workflows, downstream project block-completion gates emitted by `new-project-template/scaffolder`.
7. **Setup guidance** — expected project pre-conditions (MCPs configured in project's MCP config), how to verify availability, first-pass troubleshooting (not installed / auth expired / port collision / browser not reachable).
8. **Downstream project checklist** — when a new project is scaffolded, what artifacts must reference this guideline (list of files the scaffolder emits with browser-testing hooks).

### A2. `knowledge-base/skills/skill-code-review.md` — Phase 1 browser-validation row

Inside **Phase 1 Audit Execution** (not Phase 0 Scope, not Phase 4 Output), add row:

- **Browser Validation** — For any UI-touching or visible-behavior diff under review: confirm the engineer captured browser evidence (screenshots, console, network). Severity BLOCKER if missing. Cross-link to `reference/guidelines-browser-testing.md`.

Phase 4 Output: add requirement that findings cite browser-evidence paths when applicable.

### A3. `knowledge-base/skills/skill-pre-deploy-verification.md` — new §UI Validation

Add a new `§N UI Validation` section (position: before the Deploy Workflow section). Contents:

- Mandatory whenever the change affects a rendered page, overlay, route transition, or any visible state.
- References `guidelines-browser-testing.md` decision framework.
- Evidence capture requirement parallel to other pre-deploy checks.
- MCP-failure fallback rule (echo).

### A4. `knowledge-base/reference/guidelines-frontend-stacks.md` — cross-reference

Add short pointer paragraph or bullet: when evaluating / validating a frontend stack, browser MCP validation is the canonical runtime-check procedure — see `guidelines-browser-testing.md`.

### A5. `knowledge-base/reference/guidelines-ui-ux.md` — cross-reference

Add short pointer paragraph or bullet: for runtime / rendered-behavior validation of UI/UX decisions, use browser MCPs — see `guidelines-browser-testing.md`.

### A6. `art-director/art-director.md` + `art-director/skills/` — primary tool elevation

- Update `art-director.md` to make browser MCPs the **primary hands-on validation tool** for visual regression + interaction capture (not optional screenshots).
- If any art-director skill describes visual checks, wire the browser-testing reference as the canonical procedure.

### A7. `new-project-template/spec.md` — scaffolder emission requirement

Update the spec's generated-artifact list so the scaffolder emits:
- A project-local `playbook-browser-testing.md` (parallel to Hiresling's `hiresling-app/docs/playbook-browser-testing.md`) — or a short pointer to the 42hq-level `guidelines-browser-testing.md`, depending on project scale.
- Block-completion + session-end skill templates already include a §Browser Validation section pre-wired.

### A8. `new-project-template/agents/scaffolder.md` + `new-project-template/agents/upgrader.md`

Encode the emission requirement from A7 so `scaffolder` enforces it on every new project and `upgrader` adds it when upgrading an existing project.

### A9. `new-project-template/skills/skill-audit.md` — browser-testing capability check

When auditing an existing project, check whether browser MCPs are configured and wired into the completion gate. Flag if absent.

---

## Topic B — 6-Stage Validation Flow in 42Agents templates (mirrors Hiresling B48-03)

### B1. `knowledge-base/principles-base.md §12 Definition of Done` — extend

Do NOT add a new section; §12 already exists as the canonical DoD home. Extend §12 with the 6-stage flow, template-agnostic wording:

1. Build
2. Local validation (every acceptance criterion; UI via browser MCPs per `guidelines-browser-testing.md`)
3. User-test gate — mandatory for visible / behavioral / workflow-altering changes; default applies
4. User approves → PR → CI → user clicks Merge (no auto-merge)
5. Post-merge re-validation on trunk
6. User explicitly triggers session-end → only then status flips to Done, docs sync, block archives

Cross-link: `skills/skill-pre-deploy-verification.md`, `skills/skill-change-tracking.md`.

### B2. `knowledge-base/skills/skill-pre-deploy-verification.md` — align to flow step 5

Explicit wording: deploy happens only after user trigger. Pre-deploy verification includes post-merge re-validation equivalent to flow step 5.

### B3. `knowledge-base/skills/skill-change-tracking.md §4 Verify at Session End` — align

Explicit wording change: mark-done gate is user-triggered session-end, not PR merge. Cross-reference `principles-base.md §12`.

### B4. `new-project-template/spec.md` — emission requirement

Scaffolder must emit `skill-block-completion.md` + `skill-session-end-{role}.md` templates with the 6-stage flow **pre-wired** (not merely "referenced"). Update the spec's generated-artifact list.

### B5. `new-project-template/agents/scaffolder.md` — enforcement

Encode B4 so every scaffold enforces it.

---

## Execution

**Owner:** super-m (same role that authored this plan and PR #73).

**Branch + PR convention in 42hq:** confirmed 2026-04-23 by user — `feat/` or `fix/` branches → PR to `main`. Same pattern as hiresling-meta. No direct pushes to `main`.

**Suggested commit structure:** 2 PRs (or 1 if 42hq uses direct-to-main).
- **PR-A:** Topic A — `guidelines-browser-testing.md` (new) + 6 files touched (code-review, pre-deploy, frontend-stacks, ui-ux, art-director, new-project-template/scaffolder+upgrader+spec+audit).
- **PR-B:** Topic B — `principles-base.md §12` + pre-deploy + change-tracking + new-project-template/spec + scaffolder.

Topic A lands first (B references browser-MCP guideline from A). If direct-to-main, sequence the same.

---

## Verification

After both topics land:

- [ ] `knowledge-base/reference/guidelines-browser-testing.md` exists with all 8 sections
- [ ] `skill-code-review.md` Phase 1 has browser-validation row (BLOCKER)
- [ ] `skill-pre-deploy-verification.md` has §UI Validation + align to flow step 5
- [ ] `guidelines-frontend-stacks.md` + `guidelines-ui-ux.md` cross-link new guideline
- [ ] `art-director/art-director.md` + skills updated — browser MCPs as primary tool
- [ ] `new-project-template/spec.md` + `scaffolder.md` + `upgrader.md` + `skill-audit.md` — browser-testing emission requirement encoded
- [ ] `principles-base.md §12` — 6-stage flow present (not a new section)
- [ ] `skill-change-tracking.md §4` — mark-done gate = user-triggered session-end
- [ ] No references to Hiresling or `42piratas@` / `anquadros@` / `tisuang@` in 42hq live files
- [ ] Downstream: a fresh `new-project-template` scaffold emits completion + session-end templates pre-wired with both the browser-validation section and the 6-stage flow

---

## Parent-plan status

`plan-browser-mcps-workflow-email.md` (R2) supersedes: Hiresling-scope portions delivered via hiresling-meta PR #73 (B48-01 / B48-02 / B48-03 specs). 42Agents-scope portions tracked here.
