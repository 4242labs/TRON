# Trivial Tip Converter

A single-page tip calculator and unit (distance / temperature) converter.
The **trivial** tier of the TRON sim target set (`tron-meta/sims/README.md`) —
a pure happy-path shakeout: linear 3-block dependency chain, no forced walls,
no `await_confirm`.

## Stack

Next.js (App Router) + React + TypeScript + Tailwind CSS. Domain logic lives
in pure `src/lib/` modules (`tip.ts`, `convert.ts`) with a genuine Vitest
suite. No remote font import, so `next build` is offline-green. Deployable to
Vercel (`vercel.json`).

## Commands

```bash
npm install
npm run dev     # dev server; port from $PORT (see .env.example) — never a hardcoded default port
npm run build   # next build — offline-green
npm test        # vitest run — 9 genuine assertions
```

## Layout

- `src/lib/tip.ts` / `src/lib/convert.ts` — pure domain logic, unit tested
- `src/app/` — the single page + client form wiring the lib into the UI
- `meta/` — the TRON-readable canon (pipeline, blocks, agents, config) — see
  `meta/pipeline.md`
