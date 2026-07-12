# B3 — Rails / deterministic engine

**Project:** TRON deterministic rebuild · **Phase:** 3
**Read first:** `../tron-adr-001-deterministic-rebuild.md` + `B0-blueprint-contracts.md` + `B2-composition-canon-content.md`.
**Repo:** `tron` canon repo (`~/42labs/tron/` — `scripts/`, `skills/`).

> Context: the deterministic spine. `run.sh` executes the routing table and shells out to `claude -p` only for the bounded typed judgment tools, then returns. The LLM never reads the flow path. Built fresh — no reuse of v1 scripts/skills (exception: the TG connector may be carried after review).

---

- **Goal:** build the deterministic spine + bounded judgment tools + procedures.

- **Acceptance criteria:**
  - `run.sh` executes `routing.yaml`, shells to `claude -p` per typed tool, returns to the runner; LLM never reads the path.
  - Judgment tools implemented to B0 contracts (schema-validated I/O); tiered models wired (cheap classify, strong triage).
  - `render.sh` renders `render(tag, slots)` from `messages.yaml`.
  - `sweep.sh` + recover use **real `~/.claude/jobs` fields** (`state`, `updatedAt`, `timeline.jsonl`, short-id→`sessionId`); name-primary / id-fallback addressing.
  - Skills rewritten as procedures only (`dispatch`, `sweep`, `recover`, `checkpoint`, `escalate`, `edit-self`, `update`, `doctor`, `session-end`).
  - TG connector reviewed from v1 and carried only if clean; `cron-install.sh` (idempotent) implemented.
  - `pipeline: host` parse/normalize implemented to B0's accepted-format spec (R-2): read into the normalized mirror, write back less often — never free-form rewrite per tick.
  - `blueprint-lint` wired into `doctor`/`validate`; ticks atomic + idempotent.

- **Integration constraints (from B4 `tron.md` + ADR-002):**
  - Load `tron.md` (canon, `9d961b0`) as the **judgment-tool prompt context**; expect schema-only returns, never prose to the flow.
  - **System tags are B3's to produce deterministically** — `sweep.tick`, `worker.stalled`, `worker.dead`, `gate.pass`/`gate.fail`. `classify_message` only returns worker/operator tags + `unclassified`.
  - **`assess_stall` runs only on the ambiguous case** — B3 must short-circuit on any positive activity signal (lastActivity grew / worktree dirty / mtime grew) **before** the LLM call; `tron.md` is written assuming this.
  - **Invalid-output / `unclassified` → hardwired escalate** — implement the retry budget (max 2) + the hardwired escalate edge that `tron.md` promises.
  - **Spawn workers detached from any TTY** (no console-child processes) so closing the console can't SIGHUP-cascade the fleet (ADR-002 failure handling).
  - **Expose the engine as a callable** the console/conversation drives (`start` / `tick` / `stop` / `msg` entry points) — B7 builds the front on top of this.

- **Scope:** `scripts/`, `skills/`, judgment-tool wiring.

- **Watch (R-1):** keep `run.sh` small. If YAML parse / JSON validation / render grows fragile in bash+yq+jq, factor a tiny non-bash helper rather than a 600-line script.

- **Dependencies:** B0, B2.

- **Owner:** engineer.
