# B4 — `tron.md` judgment context

**Project:** TRON deterministic rebuild · **Phase:** 4
**Read first:** `../tron-adr-001-deterministic-rebuild.md` + `B0-blueprint-contracts.md` + `B3-rails-engine.md`.
**Repo:** `tron` canon repo (`~/42labs/tron/` — `templates/tron.md`).

> Context: `tron.md` is **not** the executor — `run.sh` is the spine. `tron.md` is the prompt context the bounded judgment tools run under. This block writes it fresh, matching how B3 invokes the tools.

---

- **Goal:** write `tron.md` as the prompt context the bounded judgment tools run under.

- **Acceptance criteria:**
  - Contains the judgment calls + TRON identity/standing rules **only**.
  - **Not** an executor; does **not** duplicate the flow; names `run.sh` as the spine.
  - No backend narration; voice consistent with canon.

- **Scope:** `tron.md` (+ its template).

- **Dependencies:** B0, B3.

- **Owner:** engineer.
