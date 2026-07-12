# Plan: TRON-as-SoT Canon Cleanup — Change Map

**Author:** SUPER-M · **Opened:** 2026-07-05 · **Status:** mapping complete; execution partial.

**Goal.** Make **TRON** (`tron/tron-app/templates/project-scaffold/`) the single source of truth
for all scaffold payload, retire the old `new-project-template` kit references fleet-wide, and
repoint everything that still cites the moved/deleted canon templates. This file maps **every**
change required — done, pending, and deferred.

**Two retired things, don't conflate:**
1. **`new-project-template/` kit** — the pre-TRON scaffold kit. **Already deleted** from 42hq; only
   *references* to it survive (dead links).
2. **`knowledge-base/templates/{hooks/,setup-repo.sh}`** — moved to TRON on 2026-07-05 (PR #108 + #133).
   `knowledge-base/` itself **stays** as the runtime canon (principles-base, skills, reference, kb).

**Status legend:** ✅ done · 🔶 pending (this migration) · 🕓 deferred (operator-driven, per-project) · 📜 history (leave as-is).

---

## Part 1 — Done (PR tron#108 + 42hq#133)

| Area | Change | PR |
|---|---|---|
| TRON `setup-repo.sh` | Ported CI + git-version guards; TRON copy is now feature-complete | tron#108 |
| TRON hooks | Adopted full canon enforcement (worktree-mandatory + `.repo-class`/`.integration-branch`) — replaced the weaker branch-only guard | tron#108 |
| 42hq canon refs | Repointed scaffold step 4b, `skill-project-audit`, `skill-project-upgrade`, `skill-git-multi-agent`, `skill-branching-strategy`, `principles-base §14` → TRON path | 42hq#133 |
| 42hq KB dupes | Deleted `knowledge-base/templates/{hooks/,setup-repo.sh}` (−245 lines) | 42hq#133 |
| Stray `42hq/kb/` | Merged 2 unique notes into `knowledge-base/kb/frameworks/`, removed folder | 42hq#133 |
| Scaffold skill sync | `ref-*.md` count 4→3; `CLAUDE.md`→`AGENTS.md` | 42hq#133 |

---

## Part 2 — 42hq remaining (this migration) 🔶

### 2a. KB docs still citing moved templates
| File:line | Current | Action |
|---|---|---|
| `knowledge-base/rollouts/2026-05-15-githooks-script-library-reframe.md:6,49,80` | "Canon source: `templates/setup-repo.sh`, `templates/hooks/…`" | 🔶 Repoint to TRON path **or** add a top banner "superseded — templates now in TRON (2026-07-05)". Rollout is a live-ish task doc, not pure history. |
| `knowledge-base/principles-base.md:283,293,296,306` | Dated changelog rows: "KIT updated: `templates/setup-repo.sh`…" | 📜 Leave — dated history. (Optional: append a 2026-07-05 row recording the TRON-SoT move.) |

**Add:** a `principles-base.md` changelog row dated 2026-07-05 recording the hooks/setup-repo → TRON SoT move (so the record is complete). 🔶

### 2b. Stale SUPER-M plans referencing the deleted `new-project-template` kit
These plans predate the kit's deletion and describe editing `new-project-template/agents/scaffolder.md`,
`upgrader.md`, `spec.md`, `skills/` — none of which exist. They are misleading if picked up.
| File | Disposition |
|---|---|
| `agents/super-m/plans/plan-browser-mcps-consultancy-propagation.md` (A7–A9, B4–B5, integration pts) | 🔶 Archive or annotate "kit retired — scaffolder/upgrader emission now lives in TRON `project-scaffold`". |
| `agents/super-m/plans/plan-browser-mcps-workflow-email.md:69,70,176,177` | 🔶 Same. |
| `agents/super-m/plans/plan-42hq-rename-restructure.md:21,37` | 📜/🔶 Historical restructure plan; annotate that `new-project-template/` no longer exists. |
| `docs-reports/SCRUB_ORCHESTRATION_FROM_PROJECTS_PLAN.md:109,124,125` | 🔶 Repoint the "Canon templates" rows to TRON `project-scaffold/templates/`. |
| `agents/super-m/super-m.md:292` | 📜 Changelog history — leave. |
| `knowledge-base/rollouts/2026-05-05-warnings-kb-rollout.md:27,111` | 📜 History — leave. |

### 2c. Move `skill-project-scaffold` out of super-m into TRON?
`tron-meta/pipeline.md:178 (P-06)` is an **open TRON roadmap item**: "Absorb `skill-project-scaffold.md`
(currently `super-m/`) into TRON." Decide whether the scaffold *procedure* also moves to TRON or stays
SUPER-M-owned (SUPER-M runs it, TRON holds the payload). **Open decision — see Part 5.**

---

## Part 3 — Projects (fleet backfill) 🕓

Per migration policy (`plan-strip-old-tron.md`, `plan-tron-canon-consolidation.md`): existing projects are
**not auto-re-scaffolded** — each is fixed deliberately via an `UPGRADE PROJECT` pass, its **own branch + PR**.
Runtime is unaffected today (hooks are self-contained copies; canon is read by humans/agents, not CI).

**On-disk projects (audited 2026-07-05):**

| Project | Dead `new-project-template` ref | Stale "canon source" citation (KB→TRON) | `canon-drift-check.sh` dead path | `CLAUDE.md`→`AGENTS.md` | `setup-repo.sh`/hooks vs TRON SoT |
|---|---|---|---|---|---|
| **ganttflow** | `ganttflow-app/services-setup.md:9` | `ganttflow-meta/skills/skill-worktree-and-branching.md:29` | — | meta root | hooks identical; setup-repo now differs from TRON SoT |
| **hiresling** | `hiresling-meta/scripts/canon-drift-check.sh:31` | `hiresling-meta/principles.md:68` | yes (l.31) | `hiresling-app/app/CLAUDE.md` | setup-repo drifted (lefthook bridge) + differs from SoT |
| **lens** | `lens-meta/context.md:212`, `README.md:5`, `canon-drift-check.sh:31` | (uses absolute KB paths broadly) | yes (l.31) | `lens-meta/CLAUDE.md` | setup-repo drifted (lens-meta, lens-my) |
| **semdigitar** | `semdigitar-meta/scripts/canon-drift-check.sh:31` | (absolute KB paths) | yes (l.31) | `semdigitar-meta/CLAUDE.md` | setup-repo drifted (meta) |
| **zovv** | `zovv-app/services-setup.md:17` | `zovv-meta/skills/skill-worktree-and-branching.md:29` | — | `zovv-meta/CLAUDE.md` | hooks + setup-repo identical (to old KB; now differ from SoT) |
| **tron-clu** | — (decoupled tooling) | — | — | — | — |

**Per-project change set (each, via UPGRADE PROJECT):**
1. 🕓 Repoint `services-setup.md` / `skill-worktree-and-branching.md` / `principles.md` "canon source" from
   `42hq/knowledge-base/templates/…` **and** any `42hq/new-project-template/…` → `tron/tron-app/templates/project-scaffold/templates/…`.
2. 🕓 Update `scripts/canon-drift-check.sh` to the repo-aware version (dead `new-project-template/templates/meta/skills`
   root → the two-repo `REPO_PATH::SKILL_SUBDIR` form; the canonical drift-check was already fixed in TRON, tron#46).
3. 🕓 Rename `CLAUDE.md` → `AGENTS.md` (workspace/meta/app roots) to match scaffold v1.3.0.
4. 🕓 Reconcile `setup-repo.sh` + hooks against the new TRON SoT (decide: adopt SoT, or keep documented project override
   like hiresling's lefthook bridge).
5. 🕓 lens only: `context.md`/`README.md` "aligned to `~/42labs/42hq/new-project/` kit" → point at TRON scaffold.

**Off-disk projects (registry, not checked out):** NordGrid, Jubs, NordLens, Outreach, 42labs.io, Alfred, Aggregator,
tron-www. Same lineage assumed — **run the same per-project change set when each is next checked out.** 🕓

---

## Part 4 — TRON's own docs referencing `new-project-template` 🔶

TRON docs still describe the structure as defined by `new-project-template` (which doesn't exist — the scaffold is in-repo).
| File:line | Action |
|---|---|
| `tron-app/README.md:81` | 🔶 "The 42labs `new-project-template` ships this" → point at in-repo `templates/project-scaffold/`. |
| `tron-app/GETTING_STARTED.md:56` | 🔶 Same repoint. |
| `tron-app/contracts/blueprint-contracts.md:290` | 🔶 Same. |
| `tron-meta/pipeline.md:178 (P-06)` | 🔶 Open roadmap item — resolve per Part 2c decision; note `4242labs/new-project-template` does not and will not exist. |
| `tron-meta/pipeline-archive.md`, `blocks/archive/01-05`, `agents/super-m-local.md:25` | 📜 History — leave. |

---

## Part 5 — Open decisions (for USER — tasks 2/3)
1. **Rollout/changelog leftovers (2a):** repoint the 2026-05-15 rollout doc, or banner-supersede it? Add a 2026-07-05 changelog row?
2. **Stale plans (2b):** archive the dead `new-project-template` plans, or annotate-in-place?
3. **P-06 (2c):** does `skill-project-scaffold` move into TRON, or stay SUPER-M-owned (payload in TRON, procedure in SUPER-M)?
4. **Project backfill (Part 3):** batch it now across the 5 on-disk projects, or lazily on next touch per project?
5. **setup-repo/hooks overrides:** is hiresling's lefthook bridge a sanctioned per-project override of the SoT, or should it converge?

---

## Execution notes
- 42hq/KB/TRON-doc edits (Parts 2, 4) = SUPER-M canon work → `chore/super-m-YYYYMMDD-<slug>` worktree + PR.
- Project edits (Part 3) = **each project's own branch + PR**, never bundled — per project Git rules.
- No project runtime breaks from any of this today; it is citation/hygiene + future-scaffold correctness.
