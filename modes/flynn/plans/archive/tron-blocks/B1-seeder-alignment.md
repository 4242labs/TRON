# B1 — Seeder alignment to structured config

**Project:** TRON deterministic rebuild · **Phase:** 1 (Seeder review/adjust)
**Read first:** `../tron-adr-001-deterministic-rebuild.md` + `B0-blueprint-contracts.md`.
**Repo:** `tron` canon repo (`~/42labs/tron/` — `tron-seed.md`, `*.example.md`, `templates/`).

> Context: the v2 seeder is kept (not rebuilt) but currently writes md-style instances. This block retargets it to the new structured file tree and config outputs defined in B0. The seeder writes per-project config only; it never authors canon FSM logic.

---

- **Goal:** retarget the kept v2 seeder from md-style instances to the new structured tree + config outputs.

- **Acceptance criteria:**
  - Step-1 R1–R8 conflict walk becomes **knob-setting** against the `workflow.yaml` composition (not prose `workflow.md`).
  - Seeder authors **only** `project.yaml` + `workflow.yaml`. It never writes `routing.yaml` (canon, copied verbatim). Host **specs stay `.md`** (host-owned, never rewritten); the internal ledger stays **`pipeline.md`** (md, gitignored) — only project/workflow config converts to yaml.
  - Install drops canon `routing.yaml`, `messages.yaml`, scripts, skills per the ADR file tree; `chmod +x` scripts.
  - A seed run produces a **lint-clean, FSM-ready** instance (B0 lint passes).
  - No host scaffolding; two-pointer model preserved.

- **Scope:** seeder + its templates/examples; no rails engine.

- **Dependencies:** B0.

- **Owner:** engineer.
