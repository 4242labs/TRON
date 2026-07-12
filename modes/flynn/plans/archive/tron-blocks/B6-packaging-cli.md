# B6 — Packaging CLI *(deferred)*

**Project:** TRON deterministic rebuild · **Phase:** 6
**Read first:** `../tron-adr-001-deterministic-rebuild.md` + `B5-e2e-streamline-review.md`.
**Repo:** `tron` canon repo (`~/42labs/tron/`).
**Status note:** deferred — do not dispatch until B5 is green and the operator greenlights packaging.

> Context: the last block. A CLI installer handles deterministic install / update / version-pin, then hands off to the interactive seeder session for per-project config.

---

- **Goal:** CLI installer for deterministic install / update / version-pin, then hand off to the seeder session.

- **Acceptance criteria:** install/update/pin work headless; hands off cleanly to interactive seeding.

- **Scope:** packaging only.

- **Dependencies:** B5.

- **Owner:** engineer.
