# HANDOVER — TRON P-114 run, machine move (2026-07-07)

Read this first on the new machine, then `.tron-flynn-manifest.md`, then wait for the operator's go.

## Where things stand (one paragraph)
Phase 114 = 12 blocks. **4 done+merged+closed** (114-01/02/03/04). **8 never started** (114-05→12), HELD pending an independent architect's review of logs 114-01→04 + the operator's explicit go. This session did NOT advance blocks — it diagnosed and proved the merge mechanism, corrected FLYNN docs, and cleaned the env. Everything is committed and clean.

## THE session's finding — merge is permission-mode-conditional (do not regress this)
The old belief "agents can never `gh pr merge` — an auto-mode classifier blocks all agent merges, operator must click every PR" is **WRONG and empirically disproven**. Truth:
- Subagents INHERIT the parent session's permission mode (Anthropic docs).
- **`bypassPermissions`** → whole fleet inherits merge rights; `gh pr merge` is NOT special-cased; agents merge their own PRs. (Only explicit `ask` rules + root/home `rm -rf` still prompt.)
- **`auto`** → subagents inherit auto; `gh pr merge` hits the semantic classifier that needs the operator's OWN turn — no agent/relay clears it. That is the mode P-114 was stuck in.
- Proven live (meta, session in bypass): PR #1000 coordinator-merge = MERGED; PR #1001 worker-subagent-merge = MERGED, no denial. Net-zero (A adds probe, B removes) — trunk unchanged.
- Full write-up: `logs/log-260707-merge-mechanism-proof.md` (commit 0c007bd). Docs corrected: `tron-flynn.md` Boot preflight + `skills/skill-merge-close.md` (commit 5b4e1e5).
- Also killed a false "`~/.claude/settings.json` is malformed" diagnosis — it was a misread of `jq '.permissions'` output; the file is fine.

**⚠ MANIFEST IS STALE ON THIS POINT.** The manifest's RESUME STATE, "Deviations log", "MERGE CASCADE", and "Operator click queue → CASE-2" still assert the disproven classifier-wall theory. Trust the FLYNN log 0c007bd, not those sections. On resume, launch the run in **bypassPermissions** so the fleet merges its own green+challenged+reviewed PRs — no per-PR operator clicking.

## What to do on resume (blocked until operator says go)
1. Confirm the run launched in **bypassPermissions** (verify LIVE mode, not `defaultMode` in settings — startup-only). If autonomous merges are wanted, insist on `--dangerously-skip-permissions` / Shift-Tab.
2. Re-arm PULSE (skill-pulse: write `.tron-flynn-active` + `.tron-flynn-session`, background sleep 180). PULSE is currently DOWN.
3. RECONCILE + build **114-05 → 114-12** per the block stage machine. Respect:
   - **114-05** — Ask-user: Railway approval before gateway staging-soak.
   - **114-07** — must rebase onto B113-08's merged data-spend-breaker (carry `isDataSpendCeilingHit` + `band.cost>0` ceiling-skip); rebase-onto-landed, not live concurrency.
   - **114-08** — Ask-user: subprocess-AI path delete-vs-adopt.
   - **114-12** — data reviewer + Ask-user D-3/D-4/D-5.
   - Block files: `hiresling-meta/blocks/114-0*.md`.
4. **CASE-3 still open** (not code): register `env-parity` as a REQUIRED status check on `main`:
   `gh api -X POST repos/4242labs/hiresling-app/branches/main/protection/required_status_checks/contexts -f 'contexts[]=env-parity'`
   Without it, 114-01's gate is fail-open on staging→main.

## Fleet / gates config (operator-set, verbatim scope notes in manifest)
- 3 engineers (2 Sonnet + 1 Opus) + 1 Opus architect (persistent, out of pool, forward-only).
- Challenge EVERY done AND re-challenge before EVERY merge (ACs before + after). Reviewer approval required. Visual gates self-run (operator AFK).
- Merge authority DELEGATED to TRON (operator amendment 2026-07-06): may authorize iff challenge✓ + reviewer✓. With bypass mode, engineers execute their own merges.
- Two-gate flow: feature PR → `staging`; separate manual `staging → main` promotion PR. Branch protection active; PRs carry `app-ci`.

## Comms
- Telegram chat `-5095077412` — milestones (DELIVERED/DONE), walls, decisions only. No routine progress. TG the operator the moment anything needs them.

## Env state (verified clean this session)
- **Repos:** hiresling-app (staging, clean), hiresling-meta (main, clean), hiresling-litellm (main, clean), tron-flynn (clean, commits above pushed/local). 0 probe branches/worktrees anywhere.
- **One worktree left untouched by design:** `hiresling-meta/.worktrees/142-05-260707-1331` (branch `block/142-05-sim-harness-260707-1331`) belongs to ANOTHER session's Phase-142 work — NOT mine. Never prune it.
- Scratchpad emptied. path-guard allowlists `~/42labs/tron-flynn/`, the memory dir, and `~/42labs/42hq/knowledge-base`.
- Meta main carries probe commits d063adb (#1001) + e46cdb7 (#1000) — net-zero, expected history, no action.

## Canonical FLYNN files (all git-synced, will be on the new machine)
- `tron-flynn.md` — boot + invariants + stage machine.
- `skills/skill-*.md` — pulse, dispatch, gates, merge-close, session-end, succession, manifest, operator-comms, voice.
- `logs/log-260707-merge-mechanism-proof.md` — the merge finding (authoritative).
- `logs/log-260707-flynn-learnings-p114.md` — P-114 learnings journal.
- `hiresling.ai/.tron-flynn-manifest.md` — run-state (stale on merge-mechanism only; see ⚠ above).

End of line.
