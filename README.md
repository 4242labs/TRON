# TRON — Session Orchestrator

**Structured, repeatable multi-agent workflows for Claude Code.**

TRON coordinates parallel AI agent sessions so you don't have to. While your Engineer builds, a Reviewer audits in the background. Context carries forward automatically. Code review never drifts. You stay in control.

---

## The Problem

Running multiple AI agents on a real project is messy. Context gets lost between sessions. Code review is skipped or forgotten. Agents go off-script. You end up doing coordination work instead of actual work.

TRON fixes this.

---

## What TRON Does

- **Orchestrates parallel sessions** — Engineer foreground, Reviewer background, both running simultaneously
- **Carries context forward** — a structured handover file replaces manual status updates between sessions
- **Enforces code review** — every session end triggers a git-scoped review; findings feed directly into the next session
- **Validates before closing** — TRON doesn't accept "done" at face value; it runs a structured verification loop before signing off
- **Keeps you informed remotely** — Telegram notifications at key milestones; reply from your phone to unblock a stalled agent
- **Never acts without confirmation** — every session starts with a plan you approve before anything runs

---

## How It Works

```
You say: "Execute Session Start"
              │
              ▼
     TRON reads project state
     presents SESSION PLAN
     waits for your go-ahead
              │
        ┌─────┴──────┐
        ▼            ▼
   Engineer      Reviewer
   [foreground]  [background]
   builds        audits commits
        │            │
        └─────┬──────┘
              ▼
     TRON collects returns
     resolves findings
     updates handover
     closes session
```

One command to start. TRON handles the rest.

---

## Key Features

**Persistent context** — the engineer handover file is the system's memory. It carries task state, blockers, and next steps across every session automatically.

**Git-scoped reviews** — the Reviewer always works from committed state, scoped to commits since the last review. No guesswork, no missed files.

**Active supervision** — TRON monitors heartbeats, detects stalls, and escalates to you if an agent goes dark. Sessions don't hang silently.

**SQLite message bus** — agents communicate through a WAL-mode SQLite bus. Ordered, concurrent-safe, queryable. No file collisions.

**Project-local instances** — each project gets its own `tron.md` tailored to its structure. One seeder, many projects, zero coupling.

**No infrastructure** — runs entirely from your local machine. No servers, no cloud dependencies, no paid services beyond Claude and Telegram.

---

## Quick Start

**1. Seed your project** (one-time):

```
You are tron/tron-seed.md.
The target project is {project-root}/.
Execute the Seeding Procedure.
```

**2. Run First Run** (orientation only):

```
You are {project}/meta/agents/tron.md. Execute First Run.
```

**3. Every session from then on:**

```
You are {project}/meta/agents/tron.md. Execute Session Start.
```

That's it.

---

## Requirements

- macOS (interactive spawn) or any Unix (headless)
- [iTerm2](https://iterm2.com) — for interactive agent windows
- [Claude Code CLI](https://claude.ai/code) — installed and authenticated
- `sqlite3`, `python3`, `curl` — pre-installed on macOS

---

## Technical Details

Architecture, session flow, message bus, supervisor validation protocol, seeding reference, and Telegram setup → **[ARCHITECTURE.md](ARCHITECTURE.md)**

---

## License

[Creative Commons Attribution-NonCommercial 4.0](LICENSE) — free to use, not for commercial purposes.

---

*Built for developers who want AI agents that work like a team, not a prompt.*
