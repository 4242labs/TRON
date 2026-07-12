> ⛔ **SUPERSEDED — 2026-06-05.** This is the prompt-driven **markdown-TRON** canon (templates/tron.md as a prompt, markdown skills, state.md). Replaced by the deterministic FSM rebuild — see [`tron-adr-001-deterministic-rebuild.md`](../tron-adr-001-deterministic-rebuild.md) and [`tron-backlog.md`](../tron-backlog.md). Retained for history.

# Plan: TRON Canon Rebuild (first public release, v0.3.0)

**Date opened:** 2026-05-14
**Date locked:** 2026-05-15
**Owner:** super-m + operator
**Status:** locked, ready to execute

---

## Goal

Single canonical `tron/` repo. Per-project local instance fully encapsulated in `meta/agents/tron/` + `meta/agents/tron.md`. New wire on Claude Code Agent View (no SQLite bus, no iTerm spawn, no manifest layer). All operator-nag boilerplate codified into reusable scripts so the operator stops repeating themselves.

---

## Locked premises (23)

| # | Premise | One-liner |
|:--|:--|:--|
| 1 | Canon purity | `tron/` has zero project/machine traces |
| 2 | Local encapsulation | `meta/agents/tron/` + `tron.md` is everything; removing them = TRON gone |
| 3 | Single canon repo | `tron-42/` deleted; no OSS/private split |
| 4 | Agent View native wire | `claude --bg -n`, `--resume -p`, reads `state.json`/`roster.json` |
| 5 | Standing instructions layer | TRON injects baseline directives so operator never repeats |
| 6 | Human-editable scripts doc | `scripts.md`, one screen per situation |
| 7 | Customization at instance | All project specifics live in consumer project, never canon |
| 8 | Workflow per project | `workflow.md` (operator-authored) + canon `workflow.example.md` |
| 9 | Project profile | `project.md`, seeder-confirmed, TRON-read each session |
| 10 | Canon → local update path | `skill-update` diff/accept/reject |
| 11 | Multi-doc drift guard | `skill-validate` runs on session start |
| 12 | Stable callback | TRON writes own sessionId to `current-id` file; workers read it |
| 13 | External cron sweep | Per-project cron/launchd pings TRON every N min for fleet sweep |
| 14 | TRON owns its own edits | `skill-edit-self`; operator requests, TRON updates all docs atomically |
| 15 | Lightweight recovery | `dispatched.log` (spawn-only) + per-worker `state.json` reads; no full journal |
| 16 | Safely re-runnable seed | `skill-doctor` for ongoing audit; `seed-trace.md` logs decisions |
| 17 | Canon-agents prereq | Project must already have `meta/agents/architect.md`, `engineer.md`, `reviewer.md` |
| 18 | Declared peer consults | `workflow.md` whitelists peer pairs; consult logged for TRON to pick up on sweep |
| 19 | Selective doc reads | Per-script declared loads; session-brief precomputed at start |
| 20 | Workers never self-terminate | Session-end skill writes log, idles; only TRON kills via RELEASE + `claude stop` |
| 21 | Inbound TG poller separate | Own cron writes to file TRON reads on sweep; decoupled from TRON's loop |
| 22 | Git-activity stall override | Sweep checks worktree for uncommitted changes; silence ≠ stuck |
| 23 | TRON self-validates | When worker unresponsive: TRON checks AC, CI, PR state itself |

---

## Target file structure

### Canon `tron/`
```
tron/
├── README.md                    # revamped, public-facing
├── tron-seed.md                 # full rewrite
├── tron-scripts.md              # canon template for scripts.md
├── workflow.example.md          # starting point for workflow.md
├── project.example.md           # starting point for project.md
├── templates/
│   ├── tron.md                  # → seeded to meta/agents/tron.md
│   ├── state.md                 # → seeded to meta/agents/tron/state.md
│   ├── workflow-state.md        # → seeded to meta/agents/tron/workflow-state.md
│   ├── handover-engineer.md
│   ├── handover-architect.md
│   └── handover-reviewer.md
├── skills/
│   ├── skill-dispatch.md
│   ├── skill-checkpoint.md
│   ├── skill-session-end-tron.md
│   ├── skill-escalate.md
│   ├── skill-validate.md
│   ├── skill-update.md
│   ├── skill-doctor.md
│   ├── skill-edit-self.md
│   └── skill-recover.md
├── scripts/
│   ├── tg-send.sh
│   ├── tg-poll.sh
│   ├── sweep.sh
│   └── cron-install.sh
├── tron-avatar.jpg              # placeholder; will be replaced
├── .gitignore
└── LICENSE
```

### Consumer project (after seed)
```
<project>/meta/agents/
├── tron.md                      # the live TRON agent
└── tron/
    ├── project.md               # paths, .env keys, conventions
    ├── workflow.md              # orchestration rules (operator-authored)
    ├── workflow-state.md        # live counters (TRON-managed)
    ├── scripts.md               # message templates (operator-extensible)
    ├── state.md                 # persistent memory (counters, config)
    ├── current-id               # TRON's live session ID (single line)
    ├── dispatched.log           # spawn history (append-only, single session)
    ├── seed-trace.md            # log of seeder decisions
    ├── tg-inbox.jsonl           # inbound TG messages (written by tg-poll)
    ├── skills/                  # copied from canon, project-customizable
    │   └── ...
    ├── templates/               # handover templates
    │   └── ...
    ├── scripts/                 # shell helpers
    │   └── ...
    └── logs/
        └── log-YYMMDD-HHMM-{slug}.md
```

**Outside `meta/agents/tron/` (project-wide):**
- `<project>/.env` — `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (gitignored)
- `<project>/meta/agents/architect.md`, `engineer.md`, `reviewer.md` — Premise 17, must exist already

---

## Implementation checklist

### Phase 1 — Build canon `tron/`

**Repo state:**
- [x] Branch `chore/canon-rewrite-260514` created in `tron/`
- [x] All previous content `git rm`'d, staged
- [x] Commit the wipe (commit `f6fdffa`)

**Authoring (order of dependency):**
- [x] `project.example.md` — fields the seeder collects
- [x] `workflow.example.md` — operator's default workflow (5 rules captured)
- [x] `tron-scripts.md` — situation→script index
- [x] `templates/state.md` — counters + notification subs (purged)
- [x] `templates/workflow-state.md` — schema for live counters
- [x] `templates/tron.md` — the live agent prompt
- [x] `templates/handover-engineer.md`, `handover-architect.md`, `handover-reviewer.md`
- [x] `skills/skill-dispatch.md`
- [x] `skills/skill-checkpoint.md`
- [x] `skills/skill-session-end-tron.md`
- [x] `skills/skill-escalate.md`
- [x] `skills/skill-validate.md`
- [x] `skills/skill-update.md`
- [x] `skills/skill-doctor.md`
- [x] `skills/skill-edit-self.md`
- [x] `skills/skill-recover.md`
- [x] `scripts/tg-send.sh`
- [x] `scripts/tg-poll.sh`
- [x] `scripts/sweep.sh`
- [x] `scripts/cron-install.sh`
- [x] `tron-seed.md`
- [x] `README.md` — public-facing pitch + quickstart
- [x] `.gitignore` (preserved)
- [x] `LICENSE` (preserved)

Commit `a05d1bd`: 24 files, 1702 insertions. Pushed to origin.

### Phase 2 — Final polish (last super-m responsibility)

- [ ] In-depth review of `project.example.md` + `workflow.example.md` together with operator
- [ ] Apply any revisions from review
- [ ] Open PR on `42piratas/tron` for `chore/canon-rewrite-260514`
- [ ] Merge to canon `main`
- [ ] Tag `v0.3.0` (first public release)

**Manual tests** (operator runs against any project of choice once canon is live):
- `claude --bg -n TRON "..."` boots cleanly in Agent View
- `claude --resume <id> -p "/compact"` works (operator-tested)
- `claude --resume <id> -p "msg"` worker→TRON callback works
- `sweep.sh` reads all worker `state.json`s correctly
- `tg-send.sh` posts to Telegram via project `.env`

These tests fall on the operator's first real seed, not on super-m.

---

## Out of super-m scope (operator-driven, post-canon)

Once Phase 2 ships, the following are operator workflows, project-by-project, not part of this plan:

- Seeding TRON into any consumer project via `tron-seed.md`
- Retrofitting existing projects to the new canon (if/when desired)
- Decommissioning `tron-42/`
- End-to-end multi-block operator validation
- Per-project `.env`, cron, peer pairs, workflow tweaks

---

## Out of scope (canon design, explicit deferrals)

- A2A inbound to TRON
- Multi-machine fleet aggregation
- LangGraph integration (separate effort)
- Multi-operator support
- Cross-worker direct messaging beyond declared peer pairs

---

## Open questions (carry into operator's first seed; not blockers for canon merge)

- `/compact` via `--resume -p`: behavior unknown until operator-tested
- Token count visibility: programmatic read API exists?
- Telegram pattern variations across consumer projects (e.g. shared bot vs per-project bot)

---

## Branches

- Plan (this branch): `chore/super-m-20260514-agent-system` → PR #51 on 42hq
- `tron/` canon rewrite: `chore/canon-rewrite-260514` → pushed; PR + merge pending Phase 2 review
