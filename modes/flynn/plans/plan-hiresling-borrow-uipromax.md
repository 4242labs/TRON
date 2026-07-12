# Plan: Borrow from ui-ux-pro-max-skill (lockstep: 42Agents ⇄ hiresling)

**Created:** 2026-04-22
**Revised:** 2026-04-22 (self-review + lockstep constraint)
**Mode:** SUPER-M user-directed
**Source:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill (MIT, 69k★)

---

## Goal

Extract net-new value from `ui-ux-pro-max-skill` into Hiresling's design/review layer. Shared artifacts land in `42hq/knowledge-base/`; project artifacts in `hiresling-*` reference them. No upstream install. No runtime deps. No competing SSOT.

---

## Lockstep invariant

All three repos land as one logical unit. Merged state is always consistent:

- `42hq` — knowledge-base refs (owning source)
- `hiresling-meta` — agent doc + skill updates (referencing the shared docs)
- `hiresling-app` — guideline doc updates (referencing the shared docs)

**Merge order (enforced):** 42Agents PR → hiresling-meta PR → hiresling-app PR. Shared docs must exist on `main` before any Hiresling PR is merged. If any PR is rejected or CI-red, the whole change reverts; nothing half-lands.

**42Agents uses branch+PR this time** (one-off deviation from its usual direct-to-main) specifically to make all three merges coordinate-able.

---

## Shared vs project layer

| Asset | Lives in | Hiresling references |
|:--|:--|:--|
| UX rules (99 items, rephrased, ranked by priority) | `42hq/knowledge-base/reference/guidelines-ui-ux.md` | `hiresling-app/docs/guidelines-design.md`, `reviewer-branding-design.md` |
| Stack checklists (Next.js, shadcn, React) | `42hq/knowledge-base/reference/guidelines-frontend-stacks.md` | `hiresling-meta/agents/reviewer-code.md`, `hiresling-app/docs/guidelines-design.md` |
| "When to Apply / Must Use / Skip" SKILL frontmatter pattern | `42hq/knowledge-base/templates/skill-trigger-frontmatter-template.md` | applied to fuzzy-trigger Hiresling skills (list populated at step 2) |

Priority ordering (A11y → Touch → Perf → Style → Layout → Type/Color → Animation → Forms → Nav → Charts) is embedded in `guidelines-ui-ux.md`, not a separate doc.

---

## Scope boundary

**SUPER-M may edit:**
- `42hq/knowledge-base/reference/*.md` (new files)
- `42hq/knowledge-base/templates/*.md` (new files)
- `hiresling-meta/agents/reviewer-branding-design.md`
- `hiresling-meta/agents/reviewer-code.md`
- `hiresling-meta/skills/*.md` (frontmatter additions only, per step 2 enumeration)
- `hiresling-app/docs/guidelines-design.md`
- `hiresling-app/docs/guidelines-brand.md` (read only — amended only if gap analysis shows rule duplication)

**Off-limits:**
- App code, components, design-token files, Tailwind config, infra, CI.

**Step 4 gate (explicit):** user approves each patch file individually (one-item-at-a-time per `feedback_one_item_at_a_time`). SUPER-M does not edit `hiresling-app/docs/*` without explicit per-file approval; any code-level change is handed to Engineer.

---

## Steps

### 0. Setup — branches + worktrees (prerequisite for any edit)

Three worktrees (per `feedback_always_branch_worktree`, `feedback_worktree_location`):

- [ ] 42Agents: `git -C ~/Spaceship/42hq worktree add ~/Spaceship/worktrees/42hq--chore-borrow-uipromax-260422 -b chore/borrow-uipromax-260422`
- [ ] Hiresling-meta: same pattern, worktree at `~/Spaceship/worktrees/hiresling-meta--chore-borrow-uipromax-260422`, branch from `origin/main`
- [ ] Hiresling-app: same pattern, worktree at `~/Spaceship/worktrees/hiresling-app--chore-borrow-uipromax-260422`, branch from `origin/staging`

### 1. Snapshot upstream source

- [ ] Clone shallow into `~/Spaceship/42hq/super-m/oss/ui-ux-pro-max-skill/` (local scratch, not committed)
- [ ] Capture commit SHA for attribution: `git -C ... rev-parse HEAD`
- [ ] Files of interest: `src/ui-ux-pro-max/data/ux-guidelines.csv`, `stacks/nextjs.csv`, `stacks/shadcn.csv`, `stacks/react.csv`, `.claude/skills/ui-ux-pro-max/SKILL.md`

### 2. Read Hiresling current state (full files)

- [ ] `hiresling-app/docs/guidelines-design.md`
- [ ] `hiresling-app/docs/guidelines-brand.md`
- [ ] `hiresling-meta/agents/reviewer-branding-design.md`
- [ ] `hiresling-meta/agents/reviewer-code.md`
- [ ] `ls hiresling-meta/skills/` and read each; **enumerate** which have fuzzy triggers (candidates for frontmatter upgrade). Output that list to the gap report.

### 3. Diff & gap analysis (report only, on 42Agents branch)

Write to 42Agents worktree: `super-m/logs/` (new file: `log-260422-HHMM-borrow-uipromax-gap.md`). Report sections:

- [ ] **UX rules gap** — upstream rules not covered by EITHER `guidelines-design.md` OR `guidelines-brand.md` (check both per fix 6)
- [ ] **Stack rules gap** — rules in `stacks/nextjs.csv`, `stacks/shadcn.csv`, `stacks/react.csv` not covered by `guidelines-design.md` or `reviewer-code.md`
- [ ] **Accessibility coverage gap** — explicit checklist vs. existing docs
- [ ] **Priority-ordering gap** — current audit order in `reviewer-branding-design.md` vs. upstream ladder
- [ ] **Fuzzy-trigger skill candidates** — enumerated from step 2
- [ ] **Concrete patch proposals** — one subsection per target file with proposed diff summary

Also commit to 42Agents branch at this step so the work is persisted.

### 4. User review gate (one decision at a time)

Present patches in this order, each awaiting user approval before moving on:

1. [ ] Shared: `guidelines-ui-ux.md` (new)
2. [ ] Shared: `guidelines-frontend-stacks.md` (new)
3. [ ] Shared: `skill-trigger-frontmatter-template.md` (new)
4. [ ] Hiresling-app: `guidelines-design.md` (reference additions)
5. [ ] Hiresling-app: `guidelines-brand.md` — touch Y/N based on gap report
6. [ ] Hiresling-meta: `reviewer-branding-design.md` (priority ordering)
7. [ ] Hiresling-meta: `reviewer-code.md` (stack-ref link)
8. [ ] Hiresling-meta: frontmatter upgrades — per enumerated skill, Y/N each

### 5. Apply approved patches (lockstep-ordered)

**5a. 42Agents branch (first — defines the targets Hiresling will reference):**
- [ ] Write shared files per approvals. Each file leads with one attribution block:
  ```
  > **Source:** Adapted from [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) @ {commit-sha} (MIT License). Rules rephrased in our own voice.
  ```
- [ ] Rephrase rules; do not paste upstream prose verbatim (fix 4 — MIT hygiene)
- [ ] Commit subject: lowercase, conventional (`feedback_commitlint_subject_case`). Example: `feat(shared): add ui-ux and frontend-stacks references`
- [ ] Rebase on `origin/main` (`feedback_always_rebase`); push; open PR → `main`

**5b. Hiresling-meta branch:**
- [ ] Apply reviewer-branding-design priority ordering — link to shared `guidelines-ui-ux.md`
- [ ] Apply reviewer-code stack-ref link — link to shared `guidelines-frontend-stacks.md`
- [ ] Apply frontmatter upgrades to approved skills — link to shared template
- [ ] Rebase on `origin/main`; push; open PR → `main`

**5c. Hiresling-app branch:**
- [ ] Apply guideline-design.md reference additions — link to shared docs (stack rules NOT inlined; `reviewer-code` + guideline both reference the single shared source — fix 5)
- [ ] Rebase on `origin/staging`; push; open PR → `staging` (fix 2)

### 6. Drift check (pre-merge, mandatory)

- [ ] For every `knowledge-base/...` path referenced in Hiresling PRs, confirm the file exists on 42Agents PR branch HEAD
- [ ] For every Hiresling PR reference, confirm the anchor/section name matches what's in the shared doc
- [ ] Monitor CI (`feedback_monitor_ci`) until green on all three PRs

### 7. Merge coordination

SUPER-M opens PRs but does not merge (`feedback_no_deploy_trigger`, `feedback_merge_discipline`). Report to user:
- [ ] Three PR URLs
- [ ] Merge order: 42Agents → hiresling-meta → hiresling-app
- [ ] Drift-check results

User merges. After merges, SUPER-M:
- [ ] Post-merge: `git fetch --prune` in all three; delete local branches + worktrees (per `feedback_keep_repo_clean`)

### 8. Session close

- [ ] Session log: `hiresling-meta/logs/super-m/260422-HHMM-borrow-uipromax.md` (includes links to all three PRs and merge commits)
- [ ] Update `hiresling-meta/agents/super-m-local.md` — Run History, Category dates (C4 agent doc accuracy + C5 doc drift touched this session)
- [ ] No registry drift to fix (already addressed at session start; commit `7372cca`)

---

## Explicit non-goals

- Do not install `.claude/skills/ui-ux-pro-max/` into any repo
- Do not vendor upstream CSVs
- Do not replace brand palette or typography
- Do not touch app code, components, design tokens, Tailwind config
- Do not paste upstream rule prose verbatim — rephrase

---

## Risks

| # | Risk | Mitigation |
|:--|:--|:--|
| R1 | Partial merge = drift (shared ref exists but Hiresling unmerged, or vice versa) | Step 6 drift check + step 7 enforced merge order |
| R2 | MIT attribution/copyright on verbatim prose | Rephrase + single attribution block per shared file with repo URL + commit SHA |
| R3 | Rule duplication between `guidelines-design.md`, `guidelines-brand.md`, and new shared docs | Step 3 checks both; shared = canonical, project = references only |
| R4 | Scope creep into Engineer territory | Step 4 gate; any code-level change handed off |
| R5 | Fuzzy skill frontmatter upgrade balloons into rewriting skills | Frontmatter-only; no body rewrites in this plan |
| R6 | 42Agents direct-to-main convention broken by this PR | One-off, documented in this plan; revert to direct-to-main on next 42Agents change |

---

## Exit criteria

- All three PRs opened, CI green, drift check clean
- User has merged all three in required order
- Session log written; `super-m-local.md` updated
- Branches + worktrees cleaned up
- No content inlined twice — Hiresling references shared docs only
