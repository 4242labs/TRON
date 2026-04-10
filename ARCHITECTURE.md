# TRON — Architecture & Technical Reference

---

## Two-Layer System

TRON is built in two layers:

1. **`tron-seed.md`** (this repo) — a one-shot agent that plants a project-local TRON instance. Runs once per project, never again.
2. **`{project}/meta/agents/tron.md`** — the live, project-specific orchestrator that runs every session.

The seeder discovers your project's structure, confirms a plan with you, and writes only TRON-specific files. Nothing is created without explicit approval.

---

## Session Flow

```
User: "You are meta/agents/tron.md. Execute Session Start."
         │
         ▼
    TRON reads handover-engineer.md + pipeline.md
    Checks for open HIGH debt items
    Finds last code review timestamp
         │
         ▼
    Presents SESSION PLAN to user
    Waits for explicit confirmation
         │
         ├──────────────────────────────────┐
         ▼                                  ▼
  [FOREGROUND]                        [BACKGROUND]
  Spawn Engineer                      Spawn Reviewer
  "Execute Session Start"             "Execute Session Start"
         │                                  │
         ▼                                  ▼
  Engineer works,                    Reviewer audits all commits
  completes tasks,                   since last review log,
  returns ENGINEER RETURN            returns REVIEWER RETURN
         │                                  │
         └──────────────┬───────────────────┘
                        ▼
               TRON collects both returns
               Updates handover-engineer.md
               Appends reviewer findings if any
               Writes TRON session log
               Presents final summary to user
```

---

## Agent Roles

| Agent    | Mode       | Blocks TRON?          | Returns         |
| :------- | :--------- | :-------------------- | :-------------- |
| Engineer | Foreground | Yes — TRON waits      | ENGINEER RETURN |
| Reviewer | Background | No — runs in parallel | REVIEWER RETURN |

**Spawn mode is role-based:**
- Engineer / Architect → interactive only (complex dev requires intervention)
- Reviewer / Analyst → interactive or headless (read-only, scoped tasks)

Practical ceiling: 3–4 parallel agents before coordination overhead outweighs benefit.

---

## Message Bus

Agents communicate through a **SQLite message bus** at `meta/logs/tron/bus.db`. WAL mode enabled for concurrent access.

- Agents write to the bus; TRON reads and forwards to Telegram
- Messages tagged with agent ID (`[ENG-1]`, `[REV-1]`, `[TRON]`)
- Cursor table tracks each reader's last-read position — no polling collisions
- If the bus is unavailable: agents print to terminal only, work is never blocked

---

## Handover Files

| File | Written by | Read by |
| :--- | :--------- | :------ |
| `meta/blocks/handover-engineer.md` | Engineer (session end) | Engineer (deletes at start), TRON (read-only), Architect/Analysts (read-only) |
| `meta/blocks/handover-reviewer-code.md` | TRON (before spawning reviewer) | Reviewer (read-only) |

**The engineer handover is the system's memory.** It carries task state, system health, blockers, and next steps between sessions. Only the Engineer writes it — everyone else reads.

---

## Reviewer Scope

Always git-based — commits since the timestamp of the last review log in `meta/logs/code-review/`. TRON extracts this automatically. The Reviewer never reads working tree files — committed state only.

---

## Supervisor Validation Protocol

| Phase | Trigger | What TRON does |
| :---- | :------ | :------------- |
| SV-01 | Agent sends `DONE` | Verifies all tasks complete; sends agent back if not |
| SV-02 | SV-01 passed | Enforces session-end skill execution |
| SV-03 | Agent's first message | Sends critical directives (conciseness, branch hygiene) |
| SV-04 | Reviewer sends `DONE` | Checks reviewer covered all changed files |

---

## Notification Events

| Tier | Events |
| :--- | :----- |
| 🔴 Always on | `BLOCKER`, `QUESTION`, `ERROR`, `STALL`, `UNRESPONSIVE`, `WATCHDOG_KILL`, `SESSION_ABORTED` |
| ℹ️ Configurable | `SESSION_START`, `SPAWNED`, `SV-PASS`, `SESSION_COMPLETE`, `PIPELINE_EXHAUSTED` |

---

## Repo Structure

```
tron/
├── README.md               ← project overview
├── ARCHITECTURE.md         ← this file
├── tron-seed.md            ← one-shot seeder agent
├── VERSION                 ← version source of truth
├── CHANGELOG.md            ← release history
├── templates/              ← project-local file templates
│   ├── tron-local.md       ← project-local orchestrator template
│   ├── tron-state.md       ← TRON state template
│   ├── skill-tg-comms.md   ← agent communication skill template
│   └── handover-reviewer-code.md
├── scripts/
│   └── tron-spawn.sh       ← agent spawn wrapper (macOS/iTerm + headless)
├── meta/
│   ├── blocks/
│   │   ├── adr-v02.md      ← ADR: SQLite message bus & active supervision
│   │   └── comms-protocol.md ← message format, heartbeat, validation specs
│   └── logs/               ← cross-project seed logs
└── tron-avatar.jpg
```

Project-local files created by seeding:

```
{project}/meta/
├── agents/
│   └── tron.md                     ← live orchestrator
├── skills/
│   └── skill-tg-comms.md           ← agent communication skill
├── blocks/
│   ├── handover-engineer.md        ← engineer inter-session state
│   └── handover-reviewer-code.md   ← reviewer scope
├── .env                            ← TG credentials (gitignored)
└── logs/
    └── tron/
        ├── bus.db                  ← SQLite message bus
        ├── tron-state.md           ← persistent TRON state
        └── log-YYMMDD-HHMM-{desc}.md
```

---

## Requirements

- **macOS** — interactive spawn uses iTerm2 via AppleScript. Headless spawn works on any Unix system.
- **iTerm2** — required for interactive agent spawning
- **Claude Code CLI** (`claude`) — must be installed and authenticated
- **`sqlite3`** — message bus. Pre-installed on macOS.
- **`python3`** — Telegram response parsing. Pre-installed on macOS.
- **`curl`** — Telegram API calls. Pre-installed on macOS.

---

## Seeding a New Project

### Prerequisites

The target project must have:

- `meta/agents/` — at least `engineer.md` and `reviewer-code.md`
- `meta/blocks/` — for handover files
- `meta/logs/` — for log folders
- `meta/pipeline.md` — TRON reads this every session

**Optional:** a `shared-knowledge/` sibling directory with shared agent behavioral guidelines. TRON works without it — TRON-SEED will warn if absent but will not abort.

### Steps

**1. Invoke TRON-SEED:**

```
You are tron/tron-seed.md.
The target project is {project-root}/.
Execute the Seeding Procedure.
```

**2. TRON-SEED will** scan the project, present a full plan, wait for your confirmation, then create all TRON-specific files.

**3. Run First Run:**

```
You are {project}/meta/agents/tron.md. Execute First Run.
```

TRON reads the agent docs, asks questions until fully oriented, then confirms readiness. First Run is orientation only — no orchestration.

**4. Every session from then on:**

```
You are {project}/meta/agents/tron.md. Execute Session Start.
```

### What Gets Created

| Action | Path | Note |
| :----- | :--- | :--- |
| CREATE | `meta/agents/tron.md` | Project-local orchestrator |
| CREATE | `meta/logs/tron/` | TRON session log folder |
| CREATE | `meta/logs/tron/bus.db` | SQLite message bus (WAL mode) |
| CREATE | `meta/logs/tron/tron-state.md` | TRON persistent state |
| CREATE | `meta/blocks/handover-reviewer-code.md` | Reviewer scope file |
| CREATE | `meta/skills/skill-tg-comms.md` | Agent communication skill |
| CREATE | `meta/.env` | TG credentials (gitignored) |
| RENAME | `meta/blocks/session-handover.md` → `handover-engineer.md` | If it exists |
| UPDATE | `meta/agents/engineer.md` | Handover path + Engineer Return format |
| UPDATE | `meta/agents/reviewer-code.md` | Handover path + git scope + Reviewer Return format |
| UPDATE | `meta/agents/architect.md` | Handover path (read-only reference) |
| SWEEP | All files referencing `session-handover.md` | Zero remaining references guaranteed |

---

## Telegram Setup

1. Create a dedicated Telegram **group** for the project (groups only — channels not supported)
2. Add your bot to the group
3. Create `{meta_path}/.env`:
   ```
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_TRON_CHAT_ID=...
   ```
4. Ensure `{meta_path}/.gitignore` includes `.env`

TRON-SEED handles this during seeding. No server required — notifications go via `curl` directly to the Telegram Bot API.

If `.env` is missing: notifications are skipped silently. Work is never blocked by a failed notification.

---

## Expanding TRON

To add a new agent to a running instance:

1. Add it to the Agent Roster table in `tron.md`
2. Create a handover file in `meta/blocks/` if needed
3. Define its return format in `tron.md` §Return Message Formats
4. Add a spawn step to `tron.md` §Execution Phase 1
5. Add return-handling to §Execution

No rearchitecting required.

---

## Known Limitations

- Parallelism is terminal-level, not context-level — "background" means the user opens the Reviewer in a separate terminal tab. TRON coordinates handoffs, not literal concurrent execution.
- First Run is a one-time orientation. Once a project is seeded, it cannot be repeated without re-seeding.

---

**Canonical source:** `tron/tron-seed.md`
**Last Updated:** 2026-04-10
