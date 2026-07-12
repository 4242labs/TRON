# B5 — End-to-end streamline review

**Project:** TRON deterministic rebuild · **Phase:** 5
**Read first:** `../tron-adr-001-deterministic-rebuild.md` and blocks B1–B4 (this is the join).
**Repo:** `tron` canon repo (`~/42labs/tron/`).

> Context: the convergence block. Walk the full path end-to-end and prove the rails are complete and clean — every transition routed, every line templated, zero backend narration leaking to the terminal. Findings route back as fix blocks per canon (reviewer logs → architect scopes → fresh engineer).

---

- **Goal:** walk the full path and prove the rails are complete and clean.

- **Acceptance criteria:**
  - Path walked: seeding → session start → dispatch → block-done → review → findings → escalation → session end.
  - Every transition has a `routing.yaml` entry; every emitted line has a `messages.yaml` entry.
  - **Zero backend narration** reaches the terminal; blueprint-lint green.

- **Scope:** review + remediation routing back to the relevant block; no new subsystems.

- **Dependencies:** B1, B2, B3, B4.

- **Owner:** reviewer (findings → architect → fix blocks).
