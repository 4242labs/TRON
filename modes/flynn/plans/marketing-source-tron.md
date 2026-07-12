# TRON — Marketing Source Doc

**Purpose:** raw material for marketing copy, website, GitHub README, launch posts. Not prose-final — these are the locked points to draw from.

---

## One-line pitch

> A canon-shaped supervisor agent for Claude Code's Agent View. One agent you talk to; it runs the rest.

---

## What TRON is

TRON is a thin, markdown-defined orchestrator that turns Claude Code Agent View into a real multi-agent workflow. You spawn TRON once per session; it spawns and supervises your fleet of worker agents — architects, engineers, reviewers — according to a workflow you author in plain markdown. You talk to TRON. TRON talks to everyone else.

---

## What TRON solves

The standing-instructions problem.

Anyone running multiple Claude Code sessions hits the same wall: every spawn requires re-typing the same baseline directives — *"no verbose,"* *"follow your skill steps,"* *"validate locally before reporting done,"* *"execute session-end."* TRON encapsulates that boilerplate, plus your project's workflow rules, into reusable scripts. You stop repeating yourself. Agents stay on rails.

---

## How TRON works (in one paragraph)

TRON ships as a single canonical repo. You run the seeder once per project; it writes a self-contained `meta/agents/tron/` folder plus a `tron.md` agent file. You launch TRON via `claude --bg -n TRON` — it appears in Agent View. TRON reads your project's workflow rules, dispatches named worker agents per block, watches their state via filesystem, and routes callbacks via `claude --resume`. Workers reach TRON via a stable file-based session ID. A Telegram bridge handles attention calls. An external cron drives periodic fleet sweeps to close the autonomous-loop gap.

---

## Architecture in one image

- **Canon repo** (`tron/`) — seed, templates, skills, scripts, workflow example, update tool. Zero project traces.
- **Local instance** (`<project>/meta/agents/tron/` + `meta/agents/tron.md`) — fully self-contained. Delete those two paths = TRON gone.
- **Wire** — Claude Code Agent View native. No custom bus, no daemon, no sidecar.

---

## The 23 design premises (skim list)

1. Canon purity — `tron/` has zero project traces
2. Local encapsulation — `meta/agents/tron/` + `tron.md` is everything
3. Single canon repo — no OSS/private split
4. Agent View native wire
5. Standing instructions layer
6. Human-editable scripts doc, one screen per situation
7. Customization at instance, never canon
8. Workflow doc per project
9. Project profile doc
10. Canon → local update path (diff/accept/reject)
11. Multi-doc drift guard (validator skill on session start)
12. Stable callback (file-based session ID)
13. External cron sweep
14. TRON owns its own edits
15. Lightweight recovery (spawn log only, no journaling)
16. Safely re-runnable seed + doctor skill
17. Canon-agents prereq (project has architect/engineer/reviewer)
18. Declared peer-consult pairs
19. Selective doc reads
20. Workers never self-terminate
21. Inbound TG poller separate from TRON loop
22. Git-activity stall override
23. TRON self-validates when worker unresponsive

---

## What ships in canon `tron/`

```
README.md
tron-seed.md
tron-scripts.md
workflow.example.md
project.example.md
templates/
skills/
scripts/
tron-avatar.jpg
LICENSE
```

## What lands in your project after seed

```
meta/agents/
├── tron.md
└── tron/
    ├── project.md
    ├── workflow.md
    ├── workflow-state.md
    ├── scripts.md
    ├── state.md
    ├── current-id
    ├── dispatched.log
    ├── seed-trace.md
    ├── tg-inbox.jsonl
    ├── skills/
    ├── templates/
    ├── scripts/
    └── logs/
```

Plus: `.env` keys (Telegram), `meta/agents/architect.md`, `engineer.md`, `reviewer.md` (canon prereq).

---

## What TRON replaces

- Manual repetition of operator directives across every agent spawn
- Custom orchestration sidecars (SQLite buses, manifest trackers, daemons)
- Ad-hoc "open 4 terminals" multi-agent workflows
- Forgetting which agent is in which block
- Bus-dead post-DONE patterns (workers stop listening once they think they're done)

---

## What TRON doesn't try to be

- A production runtime (LangGraph does that)
- A customer-facing surface (Stripe / Intercom / Customer.io / Brevo)
- A multi-machine fleet manager
- A SaaS — TRON is yours; it runs in your terminal

---

## Differentiators

- **Markdown-defined end to end.** Every rule, every script, every workflow lives in plain `.md` files you can git-diff.
- **No infra.** Runs on top of vanilla Claude Code Agent View. No daemon, no DB, no servers.
- **Operator-owned.** Open spec, open canon, no vendor lock.
- **Workflow as artifact.** Your `workflow.md` is portable across projects and teammates.
- **Removable in 2 deletes.** No project pollution.
- **Self-editing.** TRON updates its own configs atomically when you describe changes in natural language.

---

## Reliability story

The public release closes the operational failure modes from the (non-public) predecessor iteration:

- **Bus-dead post-DONE** (worker stops listening after reporting done) → workers never self-terminate; TRON owns the kill.
- **Silent stall** (worker working but idle on the wire) → sweep checks git activity, not just message timestamps.
- **TG poll gap** (operator messages dropped when CLI is busy) → TG poller runs as its own process, decoupled from TRON's loop.
- **TRON crash mid-session** → spawn log + worker state.json reads give a 2-file recovery story; no journaling overhead.
- **Worker unresponsive** → TRON self-validates AC / CI / PR state instead of blocking on a reply.

---

## Who TRON is for

- Solo founders running multi-agent workflows on Claude Code
- Small teams iterating across projects that follow a canon-shaped layout
- Anyone who has felt the *"I'm typing the same 4 things into every agent again"* pain

---

## Who TRON isn't for (yet)

- Production unattended loops — use LangGraph
- Teams of >5 sharing one orchestrator — single-operator design
- Projects that don't already have a meta/agents/ canon convention — prereq

---

## Status

- **v0.3.0** — first public release. Canon rebuild on Claude Code Agent View; 23 locked design premises.
- Pre-public iterations (SQLite-bus + iTerm-spawn era) are deprecated and not published.
- Public canon repo: `github.com/42piratas/tron`

---

## Naming + voice

- TRON / MCP voice (Tron: Legacy lineage; *Master Control Program* persona inside the codebase)
- Avatar: placeholder asset; new artwork planned
- Logo: SVG in `resources/`, due for refresh

---

## Source-of-truth links

- Plan: `super-m/plans/plan-tron-canon-consolidation.md` (this repo)
- Canon: `github.com/42piratas/tron`
- Related research:
  - `docs-reports/report-tron-as-ops-console.md`
  - `docs-reports/report-langgraph-tron.md`
  - `docs-reports/report-a2a-tron.md`
  - `docs-reports/report-adk-tron.md`
