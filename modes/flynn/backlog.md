# TRON-FLYNN: Backlog

**Open work lives in Linear, not here.** As of 2026-07-12 every pending item is a card in team
`42labs`, labeled `tron-flynn` (this agent's persona label) + `🤖 beep-boop`. See
`skill-linear-cards.md` for the card contract. This file keeps only what Linear can't hold:
operator-only actions and the closed-item history.

Carried over to Linear on 2026-07-12:

| Was # | Item | Card |
|:--|:-----|:-----|
| 1 | TRON operating modes: SCAFFOLD · NEW · ADVISOR (FLYNN absorbs TRON-FLYNN) | 42L-937 |
| 2 | Agents persist their persona into memory (compaction survival) | 42L-938 |
| 3 | Stronger enforcement for concise, purposeful agent speech | 42L-939 |
| 4 | Kill the session-start mode menu | 42L-940 |

## Operator Actions (user-only — cannot be automated)

| Item | Since |
|:-----|:------|
| **Set `CANON_READ_TOKEN` secret** in `ganttflow-meta` + `zovv-meta` repos (fine-grained PAT, `contents: read` on `42piratas/42hq`). The other 3 projects already have it. Unblocks canon-drift CI on those two. | 2026-07-05 |

## Closed

| # | Item | Closed |
|:--|:-----|:------|
| — | **Supervisor persona renamed `tron-flynn` → `tron-clu`** (repo `4242labs/tron-clu`, persona doc, install kit, all 9 skills, sidecars `.tron-clu-*`, slash command `/tron-clu`). Frees the FLYNN name for the advisor persona. Live installs, canon docs, and agent memories repointed; dated logs, retros, and experiment fixtures left as historical record. Card 42L-944. | 2026-07-12 |
| — | **Merged Analyst-Marketing + Analyst-SEO-GEO into a single agent — Emily** (`agents/emily/`). Lean 8-mode consultant (positioning · funnel · content · pricing · launch · channel · SEO · GEO). Boundaries set: Emily = punctual consultant, PESSOA = deployed operator, Finance sets prices. Old dirs removed; fleet cross-refs repointed. | 2026-07-06 |
| — | Skill vendoring isn't DRY — codified **reference, not copy** in `REGISTRY-frontmatter.md`; `canon_version` pins to the canonical file's last-change SHA (not repo HEAD), aligning schema with the per-file drift script + C1. Copies are now an offline-only exception. | 2026-06-16 |
| — | Knowledge-base path single-sourced — `principles.md §Configuration` defines `{shared_knowledge_path}` once, resolved at session start (scaffold tron #52). | 2026-06-16 |
| — | Kit `flynn-local.md` reconciled — kit ships the canonical merged template; `flynn.md` + `skill-bootstrap.md` defer to it (tron #51 / 42hq #105). | 2026-06-16 |
| — | Kit `meta/logs/` role subdirs shipped as `.gitkeep` structure; scaffolder mkdir block dropped (tron #50 / 42hq #104). | 2026-06-16 |
