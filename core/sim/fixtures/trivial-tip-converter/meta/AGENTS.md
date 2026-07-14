# Trivial Tip Converter — meta/

Project management, agents, skills, and session logs for `trivial-tip-converter`. This is a
single-repo project (no separate app/meta split) — `meta/` sits alongside the app tree in the same
git checkout.

## Agents

| Agent | File | Purpose |
|-------|------|---------|
| Architect | `agents/architect.md` | System design, scoping, trade-off analysis |
| Engineer | `agents/engineer.md` | Build, maintain, ship |
| Code Reviewer | `agents/reviewer-code.md` | Code quality audits |

This is the **trivial** tier's agent set (`tron-meta/sims/README.md` grading index) — no security or
data reviewer is shipped, since this app has no auth, database, or PII surface.

## Skills

Single home: `principles.md §Skills Registry` (skill ↔ file ↔ trigger). Don't restate the table
here — read it there. Skill files live in `skills/`.

## Key Files

- `pipeline.md` — Single source of truth for all active work
- `pipeline-archive.md` — Completed phases + resolved tech debt
- `backlog.md` — Diverse ideas not yet roadmapped
- `context.md` — Project context: background, goals, constraints
- `principles.md` — Agent behavior rules (this project has no shared knowledge base — this file is
  the complete rule set)
- `blocks/block-template.md` — Canonical block spec template
- `tron/` — the Orchestrator's answer key (`scaffold.yaml`, `project.yaml`, `knobs.yaml`) this
  harness reads to seed and validate a replica of this sim
