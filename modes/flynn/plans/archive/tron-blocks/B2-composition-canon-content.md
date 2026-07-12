# B2 — Composition + canon content

**Project:** TRON deterministic rebuild · **Phase:** 2
**Read first:** `../tron-adr-001-deterministic-rebuild.md` + `B0-blueprint-contracts.md`.
**Repo:** `tron` canon repo (`~/42labs/tron/`).
**Copy source:** `../tron-messages-candidates.yaml` (message pool, landing-page voice).

> Context: B0 defines the shapes; this block authors the actual data the rails read — the default per-project composition plus the canon routing table and message registry. Tone is already set (landing-page voice); placeholder copy is acceptable to unblock B3 testing.

---

- **Goal:** author the per-project composition default and the canon data the rails read.

- **Acceptance criteria:**
  - `workflow.yaml`: composition schema instance + embedded **default composition** (steps, roles/checks, knobs) validates against B0 schema.
  - `routing.yaml`: encodes all step-primitive edges from B0; passes blueprint-lint.
  - `messages.yaml`: a template for **every tag in the closed enum** (placeholder copy acceptable per R-4); real copy in landing-page voice; **no host-runtime names**.

- **Boundary vs B0:** B0 owns the schemas/enum/edge-format; this block owns the **instances** (default composition, the actual edges, the templates).

- **Scope:** data files only (`workflow.yaml`, `routing.yaml`, `messages.yaml`); no shell.

- **Dependencies:** B0.

- **Owner:** engineer.
