# Gap Report: Borrow from ui-ux-pro-max-skill

**Date:** 2026-04-22
**Upstream SHA:** `b7e3af80f6e331f6fb456667b82b12cade7c9d35`
**License:** MIT
**Mode:** SUPER-M user-directed
**Scope:** compare upstream UX/stack rules against Hiresling's existing docs + skills

---

## Hiresling current coverage (baseline)

| Area | Already covered | Location |
|:--|:--|:--|
| Color contrast 4.5:1 / 3:1 | ✅ | `skill-a11y-audit.md` §2 |
| Keyboard nav (Tab, Enter, Space, Esc, Arrow) + no trap | ✅ | `skill-a11y-audit.md` §3 |
| Focus indicators + no `outline:none` | ✅ | `skill-a11y-audit.md` §4, `guidelines-design.md` |
| ARIA: icon aria-label, modal aria-modal, form labels, error aria-describedby, aria-live | ✅ | `skill-a11y-audit.md` §5 |
| Heading hierarchy + skip links + landmarks | ✅ | `skill-a11y-audit.md` §5 |
| Alt text + next/image | ✅ | `skill-a11y-audit.md` §6, `skill-perf-audit.md` §6 |
| Core Web Vitals (LCP, CLS, INP) | ✅ | `skill-perf-audit.md` §2 |
| Bundle size + new dep check + server/client boundary | ✅ | `skill-perf-audit.md` §3 |
| N+1 queries, unbounded selects, streaming AI | ✅ | `skill-perf-audit.md` §4, `skill-review-code.md` §3.6 |
| next/font, priority on LCP image | ✅ | `skill-perf-audit.md` §6 |
| Semantic color tokens / no hardcoded hex | ✅ | `reviewer-branding-design.md` §1 |
| Dark/light palettes, amber brand | ✅ | `guidelines-design.md` |
| Brand voice, naming, locale overrides | ✅ | `guidelines-brand.md` |

Existing review priorities in `reviewer-branding-design.md`: 7 flat domains (Token, Voice, Locale, Hierarchy, Component, Motion, Assets) — no explicit ordering.

---

## Gap analysis

### G1. UX rules gap (genuine net-new value)

| # | Upstream rule | Hiresling state | Target | Severity |
|:--|:--|:--|:--|:--|
| G1.1 | Touch target size ≥ 44×44pt / 48dp, extend hit area if needed | Missing | `guidelines-ui-ux.md` | HIGH |
| G1.2 | Touch spacing ≥ 8px between targets | Missing | `guidelines-ui-ux.md` | HIGH |
| G1.3 | Don't rely on hover-only for primary interactions | Missing | `guidelines-ui-ux.md` | HIGH |
| G1.4 | `touch-action: manipulation` to remove 300ms tap delay | Missing | `guidelines-ui-ux.md` | MEDIUM |
| G1.5 | Visible press feedback (ripple/highlight) on tap | Missing | `guidelines-ui-ux.md` | MEDIUM |
| G1.6 | Safe-area awareness (notch, gesture bar, screen edges) | Missing | `guidelines-ui-ux.md` | MEDIUM |
| G1.7 | Line-length 35–60ch mobile / 60–75ch desktop | Missing | `guidelines-ui-ux.md` + ref from `guidelines-design.md` | MEDIUM |
| G1.8 | Body line-height 1.5–1.75 | Partial (not codified as rule) | `guidelines-ui-ux.md` | LOW |
| G1.9 | Micro-interaction duration 150–300ms; transitions ≤400ms | Partial (specific values exist, general rule missing) | `guidelines-ui-ux.md` | LOW |
| G1.10 | Animate `transform`/`opacity` only — avoid width/height/top/left | Missing | `guidelines-ui-ux.md` | MEDIUM |
| G1.11 | Exit animations 60–70% of enter duration | Missing | `guidelines-ui-ux.md` | LOW |
| G1.12 | List/grid stagger 30–50ms per item | Missing | `guidelines-ui-ux.md` | LOW |
| G1.13 | Animations interruptible — user gesture cancels | Missing | `guidelines-ui-ux.md` | MEDIUM |
| G1.14 | `prefers-reduced-motion` explicit in design guide (not just reviewer) | Missing from `guidelines-design.md` | `guidelines-design.md` §Accessibility | MEDIUM |
| G1.15 | Forms: visible labels, not placeholder-only | Missing | `guidelines-ui-ux.md` | HIGH |
| G1.16 | Forms: error near field, not top-of-form | Missing | `guidelines-ui-ux.md` | HIGH |
| G1.17 | Forms: loading button disable + spinner on async | Partial (example exists in Google button spec) | `guidelines-ui-ux.md` | MEDIUM |
| G1.18 | Forms: helper text + progressive disclosure | Missing | `guidelines-ui-ux.md` | LOW |
| G1.19 | Virtualize lists with 50+ items | Missing from perf audit | `skill-perf-audit.md` addition + `guidelines-frontend-stacks.md` | MEDIUM |
| G1.20 | Error boundaries in component tree | Missing from code review | `skill-review-code.md` addition + `guidelines-frontend-stacks.md` | MEDIUM |

### G2. Stack rules gap (Next.js 15 / shadcn / React)

| # | Upstream rule | Hiresling state | Target | Severity |
|:--|:--|:--|:--|:--|
| G2.1 | Next.js 15 changed fetch default to uncached — set `cache: 'force-cache'` explicitly for static data | Missing (version-sensitive gap) | `guidelines-frontend-stacks.md` + `skill-review-code.md` | HIGH |
| G2.2 | Server Actions for mutations (vs API route for every mutation) | Missing | `guidelines-frontend-stacks.md` | MEDIUM |
| G2.3 | `revalidatePath` / `revalidateTag` after mutations | Missing | `guidelines-frontend-stacks.md` | MEDIUM |
| G2.4 | `generateMetadata` for dynamic pages + OpenGraph images | Missing | `guidelines-frontend-stacks.md` | MEDIUM |
| G2.5 | `loading.tsx` / `error.tsx` route boundaries | Missing | `guidelines-frontend-stacks.md` | MEDIUM |
| G2.6 | Push Client Components down — keep as leaf nodes | Missing (Hiresling perf audit covers unnecessary `use client`, but not the "push-down" discipline) | `guidelines-frontend-stacks.md` | MEDIUM |
| G2.7 | shadcn Form + FormField + FormLabel + FormControl + FormMessage + Zod resolver pattern | Unclear — need to verify current Hiresling forms | `guidelines-frontend-stacks.md` | MEDIUM |
| G2.8 | shadcn component selection rules: Dialog (modals) / Sheet (side panels) / Popover (floating) / DropdownMenu (actions) / Sonner (toasts) | Missing | `guidelines-frontend-stacks.md` | LOW |
| G2.9 | shadcn: one `TooltipProvider` at app root | Unclear — verify | `guidelines-frontend-stacks.md` | LOW |
| G2.10 | React: memoize context values with `useMemo` (prevents unnecessary re-renders) | Missing | `guidelines-frontend-stacks.md` + `skill-review-code.md` §3.6 | HIGH |
| G2.11 | React: `useDeferredValue` / debounce for search/filter inputs | Missing | `guidelines-frontend-stacks.md` | MEDIUM |

### G3. Accessibility coverage gap

Hiresling's a11y coverage is strong. Two minor promotions:

| # | Rule | State | Target |
|:--|:--|:--|:--|
| G3.1 | `prefers-reduced-motion` respected with explicit fallback | In reviewer §6 Motion only; not in guidelines-design.md | Promote to `guidelines-design.md` §Accessibility |
| G3.2 | Dynamic type / system text scaling respect | Missing (mobile) | `guidelines-ui-ux.md` (part of G1 touch/mobile section) |

### G4. Priority-ordering gap

`reviewer-branding-design.md` lists 7 domains flat. Upstream's ordering (Priority 1→10: A11y → Touch → Perf → Style → Layout → Type/Color → Animation → Forms → Nav → Charts) is a better audit sequence — violations lower on the list don't matter if higher ones fail.

Proposed order for Hiresling's design review (mapped to Hiresling's 7 domains):

1. **Brand Assets** (BLOCKER class — logo, favicon) — kept first because brand-breaking issues dominate
2. **Design Token Compliance** — a11y contrast enforcement lives here via tokens
3. **Visual Hierarchy & Layout** — mobile viewport, CTA dominance
4. **Brand Voice & Copy** — content correctness
5. **Locale Copy Consistency** — i18n coverage
6. **Component Consistency** — reuse discipline
7. **Motion & Micro-interactions** — animation rules

Swap vs current: Brand Assets moved from #7 to #1; Visual Hierarchy moved up from #4 to #3. Rationale: severity-led ordering matches the SUPER-M principle "catch compound problems earliest."

### G5. Fuzzy-trigger skill candidates

Reviewed: `skill-a11y-audit.md`, `skill-perf-audit.md`, `skill-review-code.md`, `skill-block-completion.md`, `skill-review-cycle.md`, `skill-compliance-audit.md`, `skill-security-scan.md`, `skill-migration-safety.md`.

Most already have explicit trigger language ("Run when...", "Skip if..."). The "When to Apply / Must Use / Recommended / Skip" frontmatter is a minor consistency win, not a gap. **Recommendation: DROP the frontmatter-standardization item from the plan** — low ROI, not worth a multi-file edit. Only `skill-review-code.md` lacks an upfront trigger block; a single one-line trigger addition there is sufficient, no shared template needed.

---

## Concrete patch proposals

### P1. NEW: `the-consultancy/shared-knowledge/reference/guidelines-ui-ux.md`

- Attribution blockquote at top (upstream repo + SHA + MIT notice)
- Section 1: Priority ordering (upstream 10-level ladder, rephrased)
- Section 2: Touch & mobile interaction (G1.1–G1.6) — 6 rules
- Section 3: Typography discipline (G1.7–G1.8) — 2 rules
- Section 4: Animation principles (G1.9–G1.13 + G3.1 reduced-motion) — 6 rules
- Section 5: Form UX (G1.15–G1.18) — 4 rules
- Section 6: Cross-platform notes (G3.2 dynamic type)

Est. ~120 lines.

### P2. NEW: `the-consultancy/shared-knowledge/reference/guidelines-frontend-stacks.md`

- Attribution blockquote at top
- Section 1: Next.js 15 caching + mutations (G2.1–G2.5) — 5 rules
- Section 2: Server/Client component discipline (G2.6)
- Section 3: shadcn composition (G2.7–G2.9) — 3 rules with component selection matrix
- Section 4: React patterns beyond lint (G2.10–G2.11, G1.19–G1.20) — 4 rules

Est. ~100 lines.

### P3. DROP: `the-consultancy/shared-knowledge/templates/skill-trigger-frontmatter-template.md`

Skip per G5. Low ROI vs. 8-skill audit.

### P4. `hiresling-app/docs/guidelines-design.md` — reference additions

- New §Mobile Interaction subsection → links to `shared-knowledge/reference/guidelines-ui-ux.md` §Touch & mobile
- §Accessibility expanded: add `prefers-reduced-motion` respect rule + link to shared doc (G3.1, G3.2)
- §Typography: add line-length + line-height rules (G1.7–G1.8)
- New §Animation Principles subsection (existing §Background Effects stays; new section covers general rules) → links to shared doc §Animation

No rule inlined — all references shared doc. Hiresling's brand-specific animations (scale zoom, floating balls, etc.) stay in place.

### P5. `hiresling-app/docs/guidelines-brand.md` — NO CHANGES

Gap analysis found no rule duplication with brand doc. Leave untouched.

### P6. `hiresling-meta/agents/reviewer-branding-design.md` — priority ordering

- Reorder §Audit Checklist domains per G4 (Brand Assets #1, Visual Hierarchy #3)
- Add a "Priority rationale" note pointing to `shared-knowledge/reference/guidelines-ui-ux.md` §Priority ordering

### P7. `hiresling-meta/agents/reviewer-code.md` — stack-ref link

- Add a Prerequisites bullet: `shared-knowledge/reference/guidelines-frontend-stacks.md` — Next.js/shadcn/React rules
- No inline rule content

### P8. `hiresling-meta/skills/skill-review-code.md` — targeted additions

- §3.4 Frontend: add G2.10 context-value memoization rule
- §3.6 Performance: add G2.1 Next.js 15 cache default rule + G1.19 virtualize 50+ items + G1.20 error boundary
- Attribution footnote linking to shared doc

### P9. `hiresling-meta/skills/skill-perf-audit.md` — one addition

- §5 or new §7: virtualize 50+ item lists (G1.19)
- Keep shared-doc reference

---

## Summary

- **Genuine gaps found:** 20 UX + 11 stack = 31 net-new rules worth borrowing
- **Already covered:** most accessibility, most performance, most code-review categories
- **Dropped from v2 plan:** skill-frontmatter template (low ROI)
- **Brand doc untouched** (no overlap)
- **Two new shared files** to create, five existing files to amend
- **Lockstep merge order** still required: consultancy → hiresling-meta → hiresling-app

Ready for user review gate (step 4).
