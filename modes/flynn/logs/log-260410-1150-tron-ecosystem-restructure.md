# SUPER-M Session: 2026-04-10

**Mode:** IMPLEMENTATION (user-directed)
**Project:** TRON ecosystem (tron-42, tron/, tron.build/)

## Summary

Full restructure of the TRON repo ecosystem: private repo renamed, OSS repo extracted to sibling, versioning system implemented, OSS reviewed and cleaned to production quality, docs split into marketing README + technical ARCHITECTURE.md.

## What Was Done

### Repo Restructure
- Renamed `tron/` → `tron-42/` (private source of truth)
- Moved `tron-42/oss/` → `~/Spaceship/tron/` (OSS sibling repo)
- Moved `tron-42/tron.build/` → `~/Spaceship/tron.build/` (sibling repo)
- Updated `sync-oss.sh` to resolve OSS path as sibling (`../tron/`)
- Updated `instance.md` to reflect new structure

### Versioning System
- Created `VERSION` file in tron-42 (`2.25`) as single source of truth
- Updated `sync-oss.sh` to read VERSION, tag commits (`sync: v2.25 from private (hash)`)
- Updated `instance.md` Last Sync to record version synced
- Created `CHANGELOG.md` in OSS repo

### OSS Sync (v2.25)
- Synced 4 drifted files: `tron-seed.md`, `templates/tron-local.md`, `templates/skill-tg-comms.md`, `templates/tron-state.md`
- All contained the SQLite bus migration (file-bus → SQLite WAL), WATCHDOG_KILL signal, role-based spawn mode

### OSS Review & Cleanup (two passes)
**Pass 1:**
- `.gitignore`: removed stale `oss/` section
- `comms-protocol.md`: §1.2 updated to SQLite bus; `TRON_POLL_OFFSET` marked deprecated
- `README.md`: notification event names corrected; TG group vs channel; What Gets Created table completed; Last Updated date

**Pass 2:**
- Removed private `meta/agents/analyst-marketing-local.md` (was untracked, never committed)
- `CHANGELOG.md`: removed private-repo internal references
- `tron-spawn.sh`: removed deprecated `TRON_POLL_OFFSET` from headless spawn
- `tron-seed.md`: `shared-knowledge` made optional (warn, don't abort); `{reviewer_log_path}`, `{paths_table}`, and other placeholders explicitly documented in Step 7
- `README.md`: system requirements section added
- Added `ARCHITECTURE.md` to sync file list

### Docs Split
- Created `ARCHITECTURE.md` in tron-42 with all technical content
- Rewrote `README.md` as marketing doc
- User (marketing analyst) further revised README — headline, tagline placement, problem section with concrete costs, social proof
- All synced to OSS and pushed

### GitHub
- Set `https://tron.build` as homepage on OSS GitHub repo
- SSH remote attempt abandoned — repos use HTTPS + global insteadOf credential rewrite; touching global git config would affect all projects

## Recommendations

1. **OSS description missing on GitHub** — the repo has no description set (only homepage). A one-liner would help discoverability.
2. **GitHub topics** — adding topics (`claude`, `ai-agents`, `developer-tools`, `claude-code`) would improve OSS discoverability.
3. **TRON not in SUPER-M projects registry** — TRON is a managed project now; worth bootstrapping `super-m-local.md` if regular audits are intended.
4. **Backport discipline** — two occasions this session where edits were made directly to `tron/` (OSS) and had to be manually backported to `tron-42/`. The sync is one-way; a reminder to always edit tron-42 first would prevent this.

## Next Run
- No specific cadence established for TRON
- Recommend SUPER-M check after next major feature addition or OSS update
