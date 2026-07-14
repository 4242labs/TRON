# Context — Trivial Tip Converter

## What This Is

A single-page tip calculator and unit (distance / temperature) converter. It is the **trivial** tier
of the Orchestrator's sim target set (`tron-meta/sims/README.md`): a small, real, deployable app that
exists to prove the Orchestrator's supervision loop runs end-to-end on a pure happy path — no
ambiguous specs, no forced walls, no destructive-change checkpoints.

## Goals

- Ship a working tip calculator (bill + tip % → tip, total, per-person split).
- Ship a working unit converter (miles ↔ km, Fahrenheit ↔ Celsius).
- Keep the whole app small enough that a full build + test cycle takes seconds, so the
  Orchestrator's dispatch loop can be exercised repeatedly and cheaply.

## Constraints

- **Single repo.** App code and the Orchestrator's meta layer live in one repository (`meta/`
  alongside the app tree) — there is no separate app/meta repo split.
- **No remote.** This repo has no `git remote` (`repo.remote: none` in `meta/tron/project.yaml`) —
  a local shakeout. There is no GitHub, no PR, no CI to open or watch. A block's work lands when the
  worker who built it carves its own worktree + branch, rebases and re-validates at close, and runs
  `meta/scripts/land.sh` itself under a grant the Orchestrator mints on approval — a strict
  fast-forward, never a merge commit (`principles.md §Git & Branching`).
- **Offline-buildable.** `next build` must never require network access (no remote font import, no
  external API calls at build time).

## Stack

Next.js (App Router) + React + TypeScript + Tailwind CSS. Domain logic in pure `src/lib/` modules
(`tip.ts`, `convert.ts`), tested with Vitest. Deployable to Vercel (`vercel.json` at the repo root).
Dev/start server port comes from `$PORT` (see `.env.example`) — never a hardcoded literal port, so
concurrent replicas of this sim never collide.

## Deploy

- **Enabled:** no — this tier ships a Vercel-deployable config as evidence of deployability
  (`vercel.json`), but no block in this tier declares a live deploy check. `staging: none` in
  `meta/tron/project.yaml`.
- **Success check:** none. A block inherits this (no deploy check) unless its own `Deploy:` field
  says otherwise — no block in this tier does.

A block inherits this check; it may override or opt out via its `Deploy:` field. Merged work is not
done until it deploys clean and verifies where a deploy check applies (see `principles.md → Workflow`)
— for this tier, that clause is a no-op (no block declares one).

## Phase Overview

Titles only — live status is owned solely by `pipeline.md`. Do not restate status here.

| Phase | Title |
|-------|-------|
| Phase 1 | Tip converter |
