# Log — portable paths (PR #8)

Date: 2026-07-04 12:40. Maintenance session on the agent — machine portability.

## 2026-07-04 — no machine-specific paths in tracked files (PR #8)
- Defect: launcher, settings snippet, and two skills hard-coded the clone location
  (`~/42labs/tron-flynn`) — the agent only worked on one machine.
- Root resolution: `~/.claude/tron-flynn.path` pointer (one line, the clone path), written at
  machine install; launcher step 1 resolves `$FLYNN_ROOT` from it, asks-and-writes once if
  missing. Skills reference `$FLYNN_ROOT/...` (tg-send, agent `.env`, run logs).
- Hook made project-local: Boot copies `pulse-guard.sh` → `<project>/.claude/tron-flynn-pulse-guard.sh`
  and the settings snippet references `"$CLAUDE_PROJECT_DIR"/.claude/tron-flynn-pulse-guard.sh` —
  `settings.json` never names a machine path, and committing both makes the project install
  portable across machines for free. Boot verifies the copy against `$FLYNN_ROOT` and
  proposes a refresh when stale.
- Scripts were already clean: `tg-send.sh` resolves from its own location + cwd;
  `pulse-guard.sh` is cwd-relative. Verified the project-local guard copy: dormant exit 0
  without flag, block exit 2 on lapsed flag.
- Historical logs keep their old-path mentions (records, not references).
- Existing installs on this machine still work (old absolute hook path remains valid);
  migrate each project to the project-local copy at its next boot — not mid-run.

End of line.
