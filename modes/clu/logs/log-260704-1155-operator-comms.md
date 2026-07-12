# Log — operator comms channels (PR #6)

Date: 2026-07-04 11:55. Maintenance session on the agent — OPERATOR COMMS.

## 2026-07-04 — skill-operator-comms + TG transport (PR #6)
- Problem: operator-relevant messages drown in supervision noise; system idles while a
  question sits unread in the scroll.
- New `skills/skill-operator-comms.md`. One rule: **AskUserQuestion fires exactly when
  waiting-on-operator is the system's only remaining state; everything else signals without
  stopping** (blocking mid-fleet would freeze supervision of live workers on one block's wall).
  Channels: `.tron-flynn-attention` file (live operator queue, rewritten on change, scroll-proof,
  derived from MANIFEST click queue), Telegram at item creation, Agent View
  `agent_needs_input` notification + 42voices riding along. Walls escalate to a blocking
  question when the fleet drains.
- TG transport: `install/tg-send.sh` ported from tron-app v1 (key renamed
  `TELEGRAM_TOKEN` → `TELEGRAM_BOT_TOKEN`; `.env` at repo root, gitignored — root
  `.gitignore` added). Credentials asked at boot when missing, never hunted from other
  projects. Failure path verified (exit 4 no-env, syntax clean). Six seed TG templates in the
  skill; formats iterate on operator feedback after first-run samples.
- Wire-ins: persona (Boot step 2 comms config, skills table row, Reporting "transcript-only =
  LOST" rule), `skill-pulse` (route at creation; report is record, not signal), `skill-gates`
  (visual-gate wall routed), `skill-session-end` (delete `.tron-flynn-attention`; close line
  also to TG), `install/README.md` (TG step + attention-file tip).
- Basis: harness research — Agent View "Needs input" flips on AskUserQuestion; `Notification`
  hook matchers (`agent_needs_input`, `agent_completed`); statusline reads arbitrary state.

End of line.
