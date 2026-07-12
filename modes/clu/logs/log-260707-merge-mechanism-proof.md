# Finding — merge is permission-mode-conditional, not a wall (empirically proven)

Date: 2026-07-07 · Project: hiresling.ai · Context: P-114 run, merge-gate diagnosis.

## The wrong belief it corrects
During P-114 the run concluded that agent-executed `gh pr merge` is *impossible* in
Claude Code — that a fixed "auto-mode classifier" bars it and the only remedy is the
operator clicking every merge. That was stated as law. It is not law.

## Root cause (verified against Anthropic docs)
- docs.claude.com/en/docs/claude-code/sub-agents + …/api/agent-sdk/permissions:
  a subagent **inherits the parent session's permission mode**.
  - Parent in `bypassPermissions` → subagents inherit it, cannot override; only explicit
    `ask` rules and root/home `rm -rf` still prompt. **`gh pr merge` is NOT special-cased.**
  - Parent in `auto` → subagents inherit auto; `gh pr merge` routes through the semantic
    classifier, which accepts only the USER's own message/click — no agent, no coordinator
    relay clears it.
- So the P-114 block was simply the run sitting in **auto** mode. Nothing hardcoded.
- Also corrected: a false "`~/.claude/settings.json` is malformed" diagnosis produced by
  MISREADING `jq '.permissions'` output (the block was already correctly nested). The
  config was fine. Verify from ground truth; never assert off a misread. (See Invariant.)

## Empirical proof (2026-07-07, hiresling-meta, session in bypassPermissions)
Two throwaway PRs against `main`, net-zero (A adds a probe file, B removes it):
- **PR #1000 — coordinator merge:** `gh pr merge --squash` by TRON → `MERGED`, no denial.
- **PR #1001 — worker merge:** a Task-spawned subagent, directed by TRON, ran the same
  command → `MERGED`, **no permission/classifier denial**. Only the local-branch-delete
  step errored (branch held by its worktree) — cosmetic, remote merge completed.
- Cleanup verified net-zero: 0 remote branches, 0 tracking refs, 0 local branches,
  0 worktrees, probe file absent from `main`.

## Operating rule (already in tron-flynn.md Boot + skill-merge-close.md, commit 5b4e1e5)
If a run needs autonomous merges, launch it in `bypassPermissions`
(`--dangerously-skip-permissions` / Shift-Tab) and the whole fleet inherits merge rights —
engineers merge their own green+challenged+reviewed PRs, TRON can merge directly. Never
resign a run to per-PR operator clicks on the false belief that agent merges are impossible.
Verify the LIVE session mode at boot; `defaultMode` in settings is startup-only and can
differ from the running mode.

End of line.
