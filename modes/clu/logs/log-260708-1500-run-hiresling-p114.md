# Run log — hiresling.ai (Phase P-114, resumed post machine-move)

Started 2026-07-07 ~14:00 -03 (boot on new machine, handover `handover-260707-p114-resume.md`) / ended 2026-07-08 ~15:00 -03. Operator: Ânderson. Fleet: up to 3 concurrent engineers (Sonnet ×2 + Opus) + persistent Opus architect (out of pool) + per-block reviewers. Session in bypassPermissions (verified from transcript ground truth after a flagged relaunch — Shift-Tab and plain resume both failed to carry the flag).

## Outcome
Phase P-114 **COMPLETE 12/12**, header flipped on meta main (`5ae737c`). This session built+closed 8 blocks (4 inherited closed from the pre-handover half):
- 114-06 migration-cli-ci-guards — app#1126@`24e8c108` + rename #1127@`76b66076`; close meta#1004.
- 114-08 subprocess-ai-path-decision — operator DELETE; app#1128@`31717c8d` (−1081 LOC); close meta#1006; live staging batch-cycle proof.
- 114-07 pipeline-decomposition — app#1129@`8b98ff73` (prospect.ts 2905→590 + 12 modules, opencorporates deleted per ARCH ruling); close meta#1008.
- 114-09 generated-db-types — app#1130@`efc26467`; close meta#1009. Found: dead b97-01 script vs dropped table; GDPR erase-tool audit write silently failing since B97 (user_email never existed) — fixed+proven live.
- 114-05 gateway-staging-soak — litellm#14@`de40f238` (docs-only; prod redeploy watched green); operator "Cheaper" = ephemeral model; kill-test executed with prod-isolation overlap proofs; evidence in meta artifacts; close meta#1011.
- 114-11 test-taxonomy — app#1131@`8fb0d53e` + shell-pin #1132; staging E2E flipped GREEN (fixed 4 stale assertions; glob expansion exposed 10 never-run suites hiding 3 real bugs); close meta#1013.
- 114-12 review-triad-remediation — app#1133@`fe117a4d` (14 defects) + D-4 lock #1134@`d94e3e74`; operator rulings D-5 (no prod action pre-promotion), D-4 (yes), D-3 (keep per PP §8); closes meta#1019/#1020/#1021.
- 114-10 ci-tooling-pass — app#1135@`bea636fe` (Biome + knip + audit + test split + lockfile unification to npm + carries); close meta#1022 with phase flip.
Also: `migration-guard`/`env-parity` required checks registered by operator (CASE-8/CASE-3); 12 residual remote close-branches pruned with per-branch merged proofs. Nothing promoted to prod (operator posture: batch promotion later); promotion checklist carried in pipeline.md watch-items.

## Problems faced
- **Transcript loss killed 4 resumable agents** (ENG-2, ENG-3, ARCH-1 unresumable after the bypass relaunch; ENG-10 after a host restart) → successions ENG-4/ENG-6/ARCH-2 with zero work lost (state in git + MANIFEST held).
- **P-114 manifest did not survive the machine move** (on-disk file was the ended P-113 one) — rebuilt from the git-synced handover at boot.
- **Bypass acquisition took 3 attempts** (Shift-Tab unavailable; plain resume dropped the flag; only `--dangerously-skip-permissions --resume` worked; verified live from transcript each time).
- **Account limits froze the fleet twice** (session limit ~90 min; one "weekly limit" kill that turned out transient on resume).
- **Global gitconfig identity flipped to `tron-ci <ci@tron.local>` at least twice** (writer never found; broke Vercel on #1133/#1135 both times; restored twice; OPEN fleet finding).
- **Staging collision**: 114-11's local suite teardown deleted the shared E2E persona mid-114-09-post-merge-run → transient red, cleared on rerun → new fleet law: TRON-granted staging windows for ALL staging-touching runs.
- Gate rejections that were the system working: REV-6 REQUEST-CHANGES on 114-05 (missing runbook caveat + undurable evidence — both real); challenge rounds caught unexecuted evidence (114-12 T2), a no-op format hook (114-10), a paths-filter/required-check wedge (114-06), a GDPR-fix FK bug (114-09).
- ENG-8 opened fix PR #1132 before walling the red it fixed (deviation, acknowledged); ENG-1's green-PR-idle pattern appeared ~4 times (fixed by active pings per skill-pulse).
- Vercel-only CI failures ×3, all environment classes: npm/pnpm lockfile skew (2.104.1 vs 2.101.1), commit-author mapping (the gitconfig flips).

## Self-enhancement feedback
1. **Transcript loss on relaunch/restart is a structural killer.** What happened: 4 agent handles died with "No transcript found" after host-side restarts. File: `tron-flynn.md` §Invariants + `skills/skill-succession.md`. Change: add "assume ALL agent handles die on any host restart; before any planned restart, checkpoint each in-flight worker's state into the MANIFEST (worktree, branch, SHA, stage, next order) so successions are one-dispatch cheap."
2. **Boot preflight should include `git config --global user.email` verification.** What happened: a polluted global git identity broke Vercel deploys twice, costing 2 CI cycles. File: `install/README.md` + `tron-flynn.md` §Boot. Change: boot step "verify host git identity matches trunk history; engineers set explicit `--author` when the host is shared."
3. **Staging is a serialized resource — make it law, not a lesson.** What happened: two workers' staging runs collided via the shared E2E persona. File: `skills/skill-dispatch.md`. Change: standing TERM in every dispatch: "no staging-touching execution without a TRON window grant" (this run had to invent it mid-flight).
4. **Ambiguous operator words are not approvals.** What happened: I misread "proser" as "proceed" and marked a GO cleared; later treated an exploratory "it's working data" as a final D-3 ruling and dispatched it — operator called both back. File: `skills/skill-operator-comms.md`. Change: add "an approval is only the literal asked-for token ('go', 'yes', the offered word); anything else gets one clarifying line first." (Also saved to project memory.)
5. **Ball-status closer works.** What happened: operator mandated every message end with "nothing on you"/the explicit ask; question-fatigue vanished. File: `skills/skill-operator-comms.md`. Change: adopt as a standing rule in the communication contract, not per-operator improvisation.
6. **Reviewer-fix fold-ins pre-merge beat forward-scoping.** What happened: every reviewer WARN fixable in-flight (114-06 script edges, 114-07 widened-preservation, 114-08 lost test coverage) was folded before merge at trivial cost; none became debt. File: `skills/skill-merge-close.md`. Change: note "reviewer findings below BLOCK default to fold-in-now when the PR is still open, forward-scope only if the fix belongs to another block's ownership."
7. **The `gh pr checks`-idle pattern needs a mechanical rule.** What happened: engineers with armed "watchers" sat silent on green/terminal checks 4+ times; every stall cleared on one ping. File: `skills/skill-pulse.md` (extends the existing active-ping rule). Change: "a worker that reported 'watching CI' gets an automatic status ping the first tick after TRON observes the checks terminal — don't wait for the 2-tick silence rule."
8. **Long operator-idle stretches burn PULSE turns.** What happened: ~2h parked on CASE-7 at 180s cadence ≈ 40 near-empty turns. File: `skills/skill-pulse.md`. Change: when the ONLY open item is operator-owned and the fleet is idle, lengthen the timer to 15–30 min (precedent: freeze handling this run) — the attention file + TG already carry the signal.

End of line.
