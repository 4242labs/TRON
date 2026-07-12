# Log — channel wiring + sweettooth deployment (no repo changes)

Date: 2026-07-04 13:10. Operations session — everything below is untracked config or remote-machine
state; repo content unchanged since PR #8 (`11eed4d`). Logged for the record.

## 2026-07-04 — TG channels wired (both machines, untracked files)
- TRON | ZOVV channel id captured via `getUpdates` after an operator post (`-5261425093`) —
  written to `zovv/.tron-flynn.env`; TRON | HireSling.ai (`-5095077412`) written to
  `hiresling.ai/.tron-flynn.env`. Both machines. Delivery verified live from each machine
  (mac → both channels; sweettooth → TRON | ZOVV).
- zovv workspace root is not a git repo — its `.tron-flynn.env` is inherently untracked.

## 2026-07-04 — mac updated to PR #8 scheme
- Launcher re-copied to `~/.claude/commands/tron.md`; `~/.claude/tron-flynn.path` pointer
  written. Existing project installs still on the pre-#8 absolute hook path — migrate each at
  its next boot, never mid-run.

## 2026-07-04 — sweettooth (Windows/WSL2) deployed as second flynn machine
- Found `~/42labs` mirror with double-nested clones (`tron-flynn/tron-flynn`, `42hq/42hq`) —
  both verified clean, flattened to convention. flynn pulled `8bc7337` → `11eed4d`.
- Machine install: launcher + pointer (`/home/anderson/42labs/tron-flynn`) — first real
  exercise of the PR #8 portable-paths scheme on a different home layout.
- Secrets over ssh (tailscale): flynn `.env` (bot token, chmod 600) + zovv/hiresling chat-id
  files. Verified: test ping from sweettooth's zovv root delivered to TRON | ZOVV.
- Ready there: `gh` authed (42piratas), git identity set. Pending: per-project
  `settings.json` installs (Boot proposes on first run); `hiresling-argus/.env` absent
  (ARGUS scope, not flynn's).

End of line.
