# Log — per-project Telegram channels (PR #7)

Date: 2026-07-04 12:20. Maintenance session on the agent — TG channel routing.

## 2026-07-04 — layered TG config: one bot, one channel per project (PR #7)
- Operator runs one TRON bot (@tron_42bot) with a Telegram channel per project — a single
  shared chat id in the agent's `.env` was the wrong shape.
- `install/tg-send.sh`: layered resolution — `TELEGRAM_BOT_TOKEN` (+ optional default
  `TELEGRAM_CHAT_ID`) from the agent-root `.env`; `TELEGRAM_CHAT_ID` in
  `<project>/.tron-flynn.env` (cwd at send time) overrides. Distinct exit-5 messages for
  missing token vs missing chat id.
- `skill-operator-comms` + `install/README.md`: layered config documented; Boot asks for
  whichever value is missing and writes the right file (project chat id → `.tron-flynn.env`,
  confirmed gitignored before the first ping).
- Credential correction (untracked `.env`, no repo diff): the previously seeded token was
  bros_toad_bot (verified via `getMe`) — replaced with @tron_42bot's token (source:
  hiresling-argus install). Known channel: TRON | HireSling.ai `-5095077412` (via
  `getUpdates`); other project channels exist but need ids at boot.
- Verified: exit 5 with no chat id anywhere; real ping delivered to TRON | HireSling.ai via
  `.tron-flynn.env` override; `bash -n` clean.

End of line.
