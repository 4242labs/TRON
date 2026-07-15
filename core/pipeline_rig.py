#!/usr/bin/env python3
"""core/pipeline_rig.py — unit lock for the ADR-0008 stale-wall primitives
`pipeline.block_landed_closed` and `pipeline.stale_landing_wall`, PLUS
(block 01-38 T19 W1, the H1 structural fix) an end-to-end lock proving the
whole ENGINE-OBSERVED `wall_landing` pipeline — `core/casestate.py::open_case`
snapshot -> `core/architect_triage.py::enqueue_triage` job threading ->
`stale_landing_wall`'s own consumption — resists the exact silent-page-drop
attack H1 found: a genuinely NON-landing wall (e.g. credential rotation)
whose free text incidentally carries landing keywords ("land", "grant",
"refus") on a since-closed block.

WHY THE OLD `_is_landing_wall` (a substring sniff over the wall's free-text
detail) IS GONE: a worker's own prose is untrusted — it could incidentally
carry landing keywords for a genuinely non-landing ask. `wall_landing` is now
a STRUCTURAL fact `open_case` derives from the engine's own durable gate
stage at the moment the wall was raised (never from anything the wall's text
claims) — a worker CANNOT mislabel it.

Pure-unit + a light duck-typed `_Eng` for the new e2e section (no scaffold,
no real git, no processes — `open_case`/`enqueue_triage` need nothing more
than `.log`/`.dry`/`.events`/`._release_worker`, the SAME minimal shape
`core/casestate_rig.py::MiniEng` establishes, trimmed to exactly this file's
needs). `ok(name, cond, detail)`; `main()` prints `PASS (n/m)`, exits
non-zero on any fail.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_APP_ROOT, "engine"))
sys.path.insert(0, _HERE)

import pipeline   # noqa: E402 — unit under test
import gate        # noqa: E402 — core/gate.py, stage constants (read-only)
import casestate     # noqa: E402 — core/casestate.py, open_case (the W1 snapshot site)
import architect       # noqa: E402 — core/architect.py, ARCHITECT_WID + the enqueue_triage facade
import architect_triage # noqa: E402 — core/architect_triage.py, enqueue_triage/the job shape

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


_LAND = ("land.sh refused: grant minted for commit 98a1347, but worker committed "
         "8f04a86 before landing, causing content mismatch")
_CLOSED = {"gates": {"01-03": {"stage": "closed"}}}
_MERGE = {"gates": {"01-03": {"stage": "merge"}}}
_ESC = {"gates": {"01-03": {"stage": "escalated"}}}


class _Sink:
    """The `.event(type, **payload)` shape every emit-routed sink shares
    (`core/counters_rig.py`'s own established idiom)."""
    def __init__(self):
        self.log = []

    def event(self, type_, **payload):
        self.log.append({"type": type_, "payload": payload})


class _Eng:
    """The minimal duck-typed `eng` `casestate.open_case`/`architect_triage.
    enqueue_triage` need — nothing more: no git, no scaffold, no real
    process. `._page_operator` is never called by either function under
    test here (only by `architect_resolve`, out of this file's scope)."""
    def __init__(self):
        self.dry = False
        self.events = _Sink()
        self.log_lines = []
        self.released = []

    def log(self, channel, msg):
        self.log_lines.append((channel, msg))

    def _release_worker(self, wid, reason="released"):
        self.released.append((wid, reason))


def main():
    # ── block_landed_closed ────────────────────────────────────────────────
    ok("B1: block_landed_closed True iff gate stage=='closed'",
       pipeline.block_landed_closed(_CLOSED, "01-03") is True)
    ok("B2: 'merge' (in-flight) -> False", pipeline.block_landed_closed(_MERGE, "01-03") is False)
    ok("B3: 'escalated' (terminal but NOT landed) -> False — distinct from closed",
       pipeline.block_landed_closed(_ESC, "01-03") is False)
    ok("B4: missing gate -> False", pipeline.block_landed_closed({"gates": {}}, "01-03") is False)
    ok("B5: no gates key -> False", pipeline.block_landed_closed({}, "01-03") is False)
    ok("B6: no block -> False", pipeline.block_landed_closed(_CLOSED, None) is False)

    # ── stale_landing_wall — block 01-38 T19 W1: the ENGINE-OBSERVED
    #    `wall_landing` flag, never a substring sniff ─────────────────────
    ok("S1 (the T2-18 killer, OBSERVED path): worker.wall + engineer-<closed "
       "block> + wall_landing=True (engine-snapshotted) -> True",
       pipeline.stale_landing_wall(_CLOSED, "worker.wall", "engineer-01-03", True) is True)
    ok("S1b (THE H1 FIX, MUST BE GREEN): a wall with wall_landing ABSENT/False "
       "on a closed block is NEVER suppressed -> pages, REGARDLESS of what its "
       "free text says — this is the exact case the old substring sniff got "
       "wrong (a differently-worded landing refusal used to still match on "
       "text alone; now text is never consulted at all)",
       pipeline.stale_landing_wall(_CLOSED, "worker.wall", "engineer-01-03", False) is False)

    # ── stale_landing_wall — every fail-toward-page FALSE branch ────────────
    ok("S2: non-worker.wall source (sentry.cap), even with wall_landing=True "
       "-> False", pipeline.stale_landing_wall(_CLOSED, "sentry.cap", "engineer-01-03", True) is False)
    ok("S3: non-engineer worker (architect self-escalation), wall_landing=True "
       "-> False, never suppressed",
       pipeline.stale_landing_wall(_CLOSED, "worker.wall", "architect", True) is False)
    ok("S4: None worker_id, wall_landing=True -> False",
       pipeline.stale_landing_wall(_CLOSED, "worker.wall", None, True) is False)
    ok("S5: block NOT closed (merge), wall_landing=True -> False — never "
       "suppress an in-flight block",
       pipeline.stale_landing_wall(_MERGE, "worker.wall", "engineer-01-03", True) is False)
    ok("S6: block escalated (terminal-not-landed), wall_landing=True -> False",
       pipeline.stale_landing_wall(_ESC, "worker.wall", "engineer-01-03", True) is False)
    ok("S7 (MIGRATION FAIL-SAFE, absent key): closed block, worker.wall, "
       "engineer, but wall_landing is the Python default for a dict lookup "
       "on a pre-migration case/job that never carried the key at all "
       "(simulated here as None, exactly what `dict.get('wall_landing')` "
       "returns) -> False, never suppressed — 'no back-fill needed'",
       pipeline.stale_landing_wall(_CLOSED, "worker.wall", "engineer-01-03", None) is False)
    ok("S8: closed block, worker.wall, engineer, wall_landing EXPLICITLY "
       "False (the engine positively observed a non-landing gate stage at "
       "open_case time) -> False, distinct from S7's absent-key case but "
       "the same outcome",
       pipeline.stale_landing_wall(_CLOSED, "worker.wall", "engineer-01-03", False) is False)
    ok("S9: missing gate for the worker's block, wall_landing=True -> False",
       pipeline.stale_landing_wall({"gates": {}}, "worker.wall", "engineer-01-03", True) is False)

    # ══════════════════════════════════════════════════════════════════════
    # E2E — block 01-38 T19 W1: the FULL observed-flag pipeline, real
    # `casestate.open_case` -> `architect_triage.enqueue_triage` -> the job's
    # own `wall_landing` field, no shortcuts.
    # ══════════════════════════════════════════════════════════════════════

    # E1 (POSITIVE CONTROL) — a GENUINE landing wall: the raising worker's
    # block gate is at `gate.merge` (a real `land_via_grant`-calling stage)
    # the instant the wall is raised. `open_case` must snapshot
    # `wall_landing=True` on the case AND thread it onto the triage job.
    eng1 = _Eng()
    m1 = {"gates": {"01-06": {"stage": gate.STAGE_MERGE, "block": "01-06"}},
         "workers": {"engineer-01-06": {"block": "01-06"}}}
    case_id_1 = casestate.open_case(eng1, m1, "01-06", "worker.wall",
                                    "land.sh refused: grant minted for a stale commit",
                                    worker_id="engineer-01-06", kind="wall")
    case1 = (m1.get("cases") or {}).get(case_id_1) or {}
    ok("E1a: a wall raised while the block's gate is at gate.merge (a real "
       "landing stage) snapshots wall_landing=True on the OPENED CASE",
       case1.get("wall_landing") is True, f"case={case1}")
    triage1 = (m1.get("architect_queue") or [])[-1] if m1.get("architect_queue") else {}
    ok("E1b: the SAME flag is threaded onto the triage job open_case enqueues "
       "(never re-derived, never dropped)",
       triage1.get("wall_landing") is True, f"triage_job={triage1}")

    # E2 (THE CREDENTIAL-ROTATION ATTACK SHAPE, THE H1 KILLER) — a GENUINELY
    # non-landing wall (the block's gate is at gate.local — NOT a landing
    # stage) whose free text INCIDENTALLY carries every old landing keyword
    # ("land", "grant", "refus") — the exact shape that fooled the deleted
    # substring sniff. `open_case` must NOT mark this wall_landing=True.
    eng2 = _Eng()
    m2 = {"gates": {"01-07": {"stage": gate.STAGE_LOCAL, "block": "01-07"}},
         "workers": {"engineer-01-07": {"block": "01-07"}}}
    detail2 = ("credential rotation needed before I can proceed — the deploy "
              "grant login was refused; the land team rotated keys and my "
              "local .env is stale")
    case_id_2 = casestate.open_case(eng2, m2, "01-07", "worker.wall", detail2,
                                    worker_id="engineer-01-07", kind="wall")
    case2 = (m2.get("cases") or {}).get(case_id_2) or {}
    ok("E2a (THE H1 KILLER): a genuinely NON-landing wall (gate.local, not a "
       "landing stage) whose TEXT incidentally contains 'land'/'grant'/"
       "'refus' is correctly snapshotted wall_landing=False/absent — the "
       "engine never trusts the free text",
       not case2.get("wall_landing"), f"case={case2} detail={detail2!r}")

    # Now the block closes (the same durable trunk-truth condition that used
    # to let a matching-text wall get suppressed) — this attack must STILL
    # page, structurally immune now that text is never consulted.
    m2["gates"]["01-07"]["stage"] = "closed"
    still_pages = pipeline.stale_landing_wall(
        m2, case2.get("source"), case2.get("worker_id"), case2.get("wall_landing"))
    ok("E2b (THE H1 KILLER, END-TO-END — must be GREEN): the SAME "
       "credential-rotation wall, now on a CLOSED block, is STILL NOT "
       "suppressed — stale_landing_wall reads False and the operator would "
       "still be paged, structurally immune to the incidental-keyword class "
       "regardless of block-closed state (the old substring sniff would "
       "have wrongly suppressed this)",
       still_pages is False, f"still_pages={still_pages}")

    # E3 (POSITIVE CONTROL, END-TO-END) — E1's genuine landing wall, once its
    # block ALSO closes, IS correctly suppressed — proves E2b's negative
    # isn't a mechanism broken for all, only the credential-rotation case.
    m1["gates"]["01-06"]["stage"] = "closed"
    genuinely_suppressed = pipeline.stale_landing_wall(
        m1, case1.get("source"), case1.get("worker_id"), case1.get("wall_landing"))
    ok("E3 (POSITIVE CONTROL, non-vacuity): the GENUINE landing wall (E1), "
       "once its block closes, IS suppressed — proves the mechanism still "
       "works for the case it's meant to catch, not just refuses everything",
       genuinely_suppressed is True, f"genuinely_suppressed={genuinely_suppressed}")

    ok("test:<wall_landing_engine_observed_e2e> (W1/H1): open_case's "
       "engine-observed snapshot survives the full triage-job threading and "
       "correctly discriminates a genuine landing wall (E1/E3) from an "
       "incidental-keyword non-landing one (E2) purely off durable gate "
       "state, never free text",
       case1.get("wall_landing") is True and triage1.get("wall_landing") is True
       and not case2.get("wall_landing") and still_pages is False
       and genuinely_suppressed is True)

    passed = sum(1 for _, c, _ in _results if c)
    print(f"core.pipeline_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail and not c else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
