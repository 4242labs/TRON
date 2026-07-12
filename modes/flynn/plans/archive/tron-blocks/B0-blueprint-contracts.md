# B0 — Blueprint contracts

**Project:** TRON deterministic rebuild · **Phase:** 0 (Foundations)
**Read first:** `../tron-adr-001-deterministic-rebuild.md` (the architecture decision this block implements).
**Repo:** lands schema stubs + contracts in the `tron` canon repo (`~/42labs/tron/`).

> Context: TRON is a script-driven FSM supervisor. A deterministic runner (`run.sh`) executes a routing table and calls the LLM only for bounded, typed judgment tools. This block locks every contract **before** any code, so the rails (B3) have a fixed target and the lint has rules to check.

---

- **Goal:** lock every FSM/LLM contract as design artifacts before any code, so the rails have a fixed target and the lint has rules to check.

- **Acceptance criteria:**
  - Step-primitive library defined: `dispatch(role)`, `review(role)`, `gate(kind)`, `escalate`, `findings-triage` — each with enter/exit edges and the judgment tool it calls.
  - Composition schema (`workflow.yaml`) defined: ordered steps + roles/checks + knobs (threshold, git on/off, peer-consult pairs).
  - File schemas defined: `project.yaml`, `workflow.yaml`, `routing.yaml`, `messages.yaml`.
  - Situation-tag vocabulary locked as a **closed enum**; reserved `unclassified` tag with a mandatory escalate-to-operator edge (G-1).
  - Judgment-tool contracts (schema-in/schema-out) for `classify_message`, `triage`, `assess_wall`, `assess_stall`, `scope_fix`.
  - Invalid-output policy: bounded retry budget → escalate via `unclassified` edge (G-2).
  - Tick model: one wake = bounded sweep → advance → persist → exit; atomic state writes + idempotent ticks (G-3).
  - Copy scope: `messages.yaml` = runtime copy only; seeder voice separate; override-vs-coexist decided (G-4).
  - Blueprint-lint rules: over canon primitives (reachability, total tag-enum coverage, no dead transitions) **and** over each composition (exit edges land, no orphans, terminal reachable).
  - **`pipeline: host` accepted-format spec** (R-2): the tightly-constrained MD table TRON will accept, plus the normalized-mirror strategy (so the rails don't parse/rewrite a free-form host file every tick).
  - **Ledger-tracking decision recorded** (R-3): internal `pipeline.md` stays gitignored — trade-off (no version-controlled block-status history) stated explicitly so a later block can't reverse it silently.

- **Boundary vs B2:** B0 defines the **shapes** (schemas, primitive-edge format, tag enum, tool contracts, lint rules). B2 authors the **instances** (default composition, the actual `routing.yaml` edges, `messages.yaml` templates). No file content beyond schema stubs is authored here.

- **Scope:** design/contracts only — no executable `run.sh`, no real copy. Output is a contracts doc set (+ schema stubs) landed in the `tron` repo.

- **Dependencies:** none. **Note:** largest block by far (~11 deliverables, all tightly interdependent — routing schema needs the primitives, lint needs the tag enum). Kept as one block deliberately; if it stalls, split along the *shapes / policies / lint* seam.

- **Owner:** architect.
