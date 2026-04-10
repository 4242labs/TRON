# CHANGELOG

All notable changes to TRON are documented here.
One entry per sync from the private repo. Version is the source of truth in `VERSION`.

---

## [2.25] — 2026-04-10

### Changed
- Message bus: migrated from file-based bus (`bus/` directory) to SQLite (`bus.db`) — WAL mode, concurrent-safe, ordered, queryable
- Spawn mode: now role-based rather than configurable per project (engineer/architect → interactive; reviewer/analyst → headless allowed)
- Added `WATCHDOG_KILL` signal to required-action events
- `tron-local.md`: updated bus init, send, read, and poll commands to SQLite
- `skill-tg-comms.md`: updated all bus interaction to SQLite
- `tron-state.md`: updated spawn mode field, added `WATCHDOG_KILL` to notifications table
- Repo restructure: OSS repo moved from nested `oss/` to sibling `../tron/`
- Versioning: added `VERSION` file as single source of truth; sync commits now tagged with version

### Infrastructure
- `sync-oss.sh` updated to resolve OSS path as sibling (`../tron/`)
- `sync-oss.sh` now reads `VERSION` and tags commit messages
- `instance.md` Last Sync now records version synced

---

## [0.2] — 2026-03-18

### Initial OSS release
- `tron-seed.md` v0.2: one-shot seeder agent
- `templates/tron-local.md`: project-local TRON orchestrator template
- `templates/tron-state.md`: persistent state template
- `templates/skill-tg-comms.md`: agent communication skill (file-based bus)
- `templates/handover-reviewer-code.md`: reviewer scope template
- `scripts/tron-spawn.sh`: agent spawn script
- `meta/blocks/adr-v02.md`: architecture decision record
- `meta/blocks/comms-protocol.md`: communications protocol spec
