# Log — agent changelog backfill (birth → session-scoped guard)

Date: 2026-07-03 10:38. Backfills all agent changes since creation; future changes get their own log.

## 2026-07-02 — agent created (42hq PR #124, merged `d08c6a2`)
- Persona `tron-flynn.md` (lean: identity, boot, 9 invariants, 7-stage block machine, skills registry) + 6 skills (pulse, dispatch, gates, merge-close, succession, manifest) split per Anthropic progressive-disclosure practice.
- Install kit: `pulse-guard.sh` Stop hook (blocks turn end on lapsed `.tron-flynn-active` flag), `settings-snippet.json`, launcher command, README.

## 2026-07-03 — phase-2 hardening (42hq PR #125, closed superseded; content carried into this repo)
Seven fixes from the zovv Phase-2 LLM-as-TRON run evidence:
1. `bgIsolation: "none"` mandatory in settings snippet + launcher/README checks (duplicate-worktree breakage, 2 occurrences).
2. Operator's own port(s) reserved at boot, recorded in MANIFEST, never assigned/killed (repeated :3000 collisions).
3. Live PR-state check (`gh pr list`) before any merge/close/phase-flip dispatch; orders name only authorized PRs.
4. `manual_by:operator` ACs exempt from worker evidence — routed to visual-gate checklist.
5. Post-rebase: full-suite green trumps ownership list; sibling-test fixes in-scope, logged as deviations.
6. Thrash escalation: 3+ failed attempts at the same gate → wall to operator.
7. Architect guidance fallible: contradicts observed behavior → deviation report, never silent follow.

## 2026-07-03 — extraction to standalone repo (`4242labs/tron-flynn`, initial commit `c5cf27e`)
- Moved out of `42hq/agents/TRON-flynn/` (removal: 42hq PR #126). Folder name stays `tron-flynn` to avoid conflict with deterministic `tron/`.
- Paths rebased to `~/42labs/tron-flynn`; launcher command settled as `/tron` (`install/tron-command.md`); root README with experimental notice.

## 2026-07-03 — skill-voice (PR #1, merged `8f85e0b`)
- Voice palette seeded from `tron-www` landing-page terminal mockups, grouped by situation; loaded once at Boot (step 5), held all run.
- Hard limits: one flourish per operator report max; never in worker orders / challenge scripts / MANIFEST; facts never bent; walls driest register; "End of line." fixed closer.

## 2026-07-03 — session-scoped PULSE guard (PR #2)
- Defect found live: Stop hooks fire in every session of a project — a parallel session tripped flynn's guard and deleted the shared flag mid-run.
- Fix: optional `.tron-flynn-session` sidecar; guard exits 0 for sessions not named in it. Backward compatible (no sidecar = legacy behavior). Boot writes the sidecar (launcher step 4, skill-pulse); run end deletes it. Verified in 5 states (legacy-lapsed, mismatch, match-lapsed, match-fresh, loop guard).

End of line.
