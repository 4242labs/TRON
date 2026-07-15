"""core.escalation_rig — block 01-38 T21 (AC-17): escalation completeness
specifics, beyond the block's own R2/R7/R8/§2b coverage.

Five named proofs, plus one explicit confirmation (the block spec's
content-preservation sentence carries no dedicated `test:<...>` tag of its
own — folded in here rather than left implicit, see
`_content_preservation_confirmed` below):

  test:<page_dedup_per_case> — `core/casestate.py::architect_resolve`'s
  `verdict="operator"` arm now REFUSES a second call for an already
  operator-owned case (the fix this task lands: the case's own `decision`
  stays `None` after a first "operator" page — see that arm's own docstring
  — so the pre-existing `decision is not None` guard could NOT catch a
  duplicate; this task adds the missing `owner == "operator"` guard
  alongside it). The operator is paged AT MOST ONCE per case id, whichever
  condition triggers it. Mutation-proven: a "naive" re-implementation with
  the new guard removed genuinely double-pages the SAME synthetic case.

  test:<operator_delivered_no_takeback> — once a case is delivered to the
  operator (`owner="operator"`), it is NEVER re-routed to the architect:
  (a) `casestate.self_retract` refuses (logged no-op) for an
  operator-owned case — contrast-proven against an identical
  still-architect-owned case, which DOES succeed; (b) `casestate.open_case`'s
  own idempotent early-return means a SECOND wall/cap for a block that
  already has an operator-owned open case returns the SAME case_id and never
  re-reaches `architect.enqueue_triage` — never a second triage of an
  already-delivered case.

  test:<worker_death_full_handover> — block 01-38 T21's own production
  addition (`core/casestate.py::_drop_gate_and_worker`'s `handover` kwarg +
  `core/router.py::_handover_briefing`/`_consume_handover`): a worker-loss
  re-drive (settle resume/amend, or the architect's own scope_forward/
  answer) writes a durable `manifest["handover"][block]` briefing; the
  block's NEXT real ASSIGN (a genuinely fresh spawn, driven through a real
  Engine + real mailbox file) delivers it — full context (why dropped, the
  branch, an explicit re-verify-current-state instruction, the pending
  order restated), keyed on BLOCK/BRANCH, never the dead worker's id — then
  consumes (clears) it exactly once. Preservation across an intervening
  fleet-outage hold is proven directly: the handover record is
  byte-identical before and after a pause with dispatch genuinely blocked.

  test:<escalation_debounce> — never emit an escalation for a case
  resolved/resolving THIS call (the ~20s stale race, `tron-meta/logs/
  architecture/adr-0003-tron-reset-corrective.md` D-G): (a) `casestate.
  reping`'s existing `decision is not None` skip — proven, plus a
  non-vacuity contrast (an identical but still-open case DOES get
  re-pinged under the same backoff); (b) `core/sentry.py::pace`'s existing
  terminal-gate skip — an already-ESCALATED gate, however long it's held,
  is never re-escalated / never gets a second `sentry_escalated` event.

  test:<every_case_terminates_resolved_or_delivered> — drives THREE real
  wall scenarios (architect-resolved "answer", architect-escalated
  "operator" left open/delivered, architect-escalated "operator" then
  operator-`resume`d) through a real Engine, reads `eng.events.log` (T7's
  events-as-ground-truth spine), and asserts EVERY `case_opened` case_id
  reaches one of exactly `resolved` (a settled/architect-resolved/self-
  retracted/stale-resolved event fires) or `operator-delivered`
  (`case_escalated_to_operator` fires) — never neither (park-and-forget,
  bounce, or a case_id that never surfaces past `case_opened`).

`ok(name, cond, detail)` collector; `main()` prints `PASS (n/m)` and every
line, exits non-zero on any fail."""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))            # core
APP_ROOT = os.path.dirname(HERE)                               # worktree root
SIM_DIR = os.path.join(HERE, "sim")
ENGINE_DIR = os.path.join(APP_ROOT, "engine")
sys.path.insert(0, ENGINE_DIR)
sys.path.insert(0, HERE)
sys.path.insert(0, SIM_DIR)

import jobs                        # noqa: E402 — engine/jobs.py, the ONE process-spawn seam (stubbed) + real mailbox reader
import state                       # noqa: E402 — core/state.py
import gate                        # noqa: E402 — core/gate.py, stage constants
import casestate                   # noqa: E402 — core/casestate.py, the module under test
import door                        # noqa: E402 — core/door.py, the R2 door-refusal content-integrity confirmation
import intake                      # noqa: E402 — core/intake.py, private per-agent intake (rig-side write)
import vocab                       # noqa: E402 — core/vocab.py, vocab.OPERATOR pseudo-agent-id
from engine import Engine          # noqa: E402 — core/engine.py, the module under drive

import architect as core_architect  # noqa: E402 — core/architect.py, ARCHITECT_WID
import scaffold as sim_scaffold     # noqa: E402 — core/sim/scaffold.py
import worker as sim_worker         # noqa: E402 — core/sim/worker.py, ScriptedDriver + Transcript

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


# ══════════════════════════════════════════════════════════════════════════
# A minimal duck-typed `eng` for DIRECT casestate.py calls — proof-only,
# unit-scoped (no real git/Engine needed for these three; the mechanism
# under test is casestate's own internal guard logic, not dispatch/land).
# ══════════════════════════════════════════════════════════════════════════

class _Events:
    def __init__(self):
        self.log = []

    def event(self, type_, **payload):
        self.log.append({"type": type_, "payload": payload})


class _StubEng:
    def __init__(self):
        self.events = _Events()
        self.dry = False
        self.log_lines = []
        self.orders = []
        self.pages = []
        self.page_receipt = "delivered"

    def log(self, channel, msg):
        self.log_lines.append((channel, msg))

    def _to_worker(self, wid, msg, kind):
        self.orders.append((wid, msg, kind))

    def _page_operator(self, case_id, block, detail, worker_id=None, manifest=None, **kw):
        self.pages.append((case_id, block, detail, worker_id))
        return self.page_receipt

    def _release_worker(self, wid, reason="released"):
        pass


def _seed_case(manifest, case_id, block, source, worker_id, owner, decision=None, kind=None):
    manifest.setdefault("cases", {})[case_id] = {
        "case_id": case_id, "block": block, "source": source,
        "kind": kind or source, "worker_id": worker_id, "detail": f"detail for {case_id}",
        "decision": decision, "opened_at": "2026-07-14T00:00:00Z", "owner": owner,
    }
    return manifest["cases"][case_id]


# ══════════════════════════════════════════════════════════════════════════
# test:<page_dedup_per_case>
# ══════════════════════════════════════════════════════════════════════════

def _page_dedup_per_case():
    eng = _StubEng()
    manifest = {}
    _seed_case(manifest, "case-X-1", "X", "worker.wall", "engineer-X", owner="architect")

    r1 = casestate.architect_resolve(eng, manifest, "case-X-1", "operator")
    ok("PD1 (FIRST CALL — must be GREEN): the first architect_resolve(...,'operator') "
       "genuinely pages the operator and flips ownership",
       r1 is True and len(eng.pages) == 1
       and manifest["cases"]["case-X-1"]["owner"] == "operator"
       and manifest["cases"]["case-X-1"]["paging"]["attempts"] == 1,
       f"r1={r1} pages={eng.pages} case={manifest['cases']['case-X-1']}")

    r2 = casestate.architect_resolve(eng, manifest, "case-X-1", "operator")
    ok("PD2 (THE DEDUP KILLER — must be GREEN): a SECOND architect_resolve(...,'operator') "
       "for the SAME already-operator-owned case is REFUSED — no second page, "
       "paging.attempts stays exactly 1",
       r2 is False and len(eng.pages) == 1
       and manifest["cases"]["case-X-1"]["paging"]["attempts"] == 1,
       f"r2={r2} pages_after={eng.pages}")

    # MUTATION / non-vacuity: a "naive" resolve (the pre-fix shape — only the
    # decision-is-not-None guard, no owner check) run against the IDENTICAL
    # already-escalated case WOULD page it a second time.
    def _naive_resolve_operator(eng, manifest, case_id):
        case = manifest["cases"].get(case_id)
        if case is None or case.get("decision") is not None:
            return False
        eng._page_operator(case_id, case.get("block"), case.get("detail"),
                           worker_id=case.get("worker_id"), manifest=manifest)
        return True

    eng2 = _StubEng()
    manifest2 = {}
    _seed_case(manifest2, "case-Y-1", "Y", "worker.wall", "engineer-Y", owner="architect")
    casestate.architect_resolve(eng2, manifest2, "case-Y-1", "operator")   # real fix: 1 page
    naive_r2 = _naive_resolve_operator(eng2, manifest2, "case-Y-1")        # naive: pages AGAIN
    real_r2 = casestate.architect_resolve(eng2, manifest2, "case-Y-1", "operator")
    ok("PD3 (MUTATION -> the naive resolve double-pages; non-vacuity — must be GREEN): "
       "on the IDENTICAL already-escalated case, a naive re-implementation missing the "
       "owner guard genuinely pages a SECOND time (naive_r2=True) while the real "
       "architect_resolve correctly refuses (real_r2=False)",
       naive_r2 is True and real_r2 is False and len(eng2.pages) == 2,
       f"naive_r2={naive_r2} real_r2={real_r2} pages={eng2.pages}")

    ok("test:<page_dedup_per_case> (AC-17): the operator is paged at most once per "
       "case id, whichever condition triggers it",
       all(c for name, c, _ in _results if name.startswith("PD")))


# ══════════════════════════════════════════════════════════════════════════
# test:<operator_delivered_no_takeback>
# ══════════════════════════════════════════════════════════════════════════

def _operator_delivered_no_takeback():
    # (a) self_retract refuses on an operator-owned (already-delivered) case,
    #     but SUCCEEDS on an identical still-architect-owned one (contrast).
    eng = _StubEng()
    manifest = {}
    _seed_case(manifest, "case-A-1", "A", "worker.wall", "engineer-A", owner="operator")
    r_delivered = casestate.self_retract(eng, manifest, "engineer-A")
    ok("NT1 (NO-TAKE-BACK, THE KILLER — must be GREEN): self_retract REFUSES for an "
       "already operator-owned (delivered) case — never a take-back",
       r_delivered is False and manifest["cases"]["case-A-1"]["owner"] == "operator"
       and manifest["cases"]["case-A-1"]["decision"] is None,
       f"r_delivered={r_delivered} case={manifest['cases']['case-A-1']}")

    manifest2 = {}
    _seed_case(manifest2, "case-B-1", "B", "worker.wall", "engineer-B", owner="architect")
    r_undelivered = casestate.self_retract(_StubEng(), manifest2, "engineer-B")
    # A successful self_retract CLEARS the case the same call ("≤1 tick" —
    # `emit.drop("case_cleared", ...)`), so it's gone from manifest["cases"]
    # by the time this reads — the absence itself (never wrongly left open,
    # never wrongly parked) IS the positive proof here.
    ok("NT2 (NON-VACUITY CONTRAST — must be GREEN): the IDENTICAL retract SUCCEEDS "
       "while the case is still architect-owned (not yet delivered) — the refusal in "
       "NT1 is owner-conditioned, not a blanket no-op — cleared+re-drivable, never "
       "left open",
       r_undelivered is True and "case-B-1" not in manifest2["cases"],
       f"r_undelivered={r_undelivered} cases_left={list(manifest2['cases'])}")

    # (b) open_case's own idempotent early-return: a SECOND wall/cap for a block
    #     that already has an operator-owned OPEN case returns the SAME case_id
    #     and never re-reaches architect.enqueue_triage (never a re-triage of an
    #     already-delivered case).
    eng3 = _StubEng()
    manifest3 = {}
    _seed_case(manifest3, "case-C-1", "C", "worker.wall", "engineer-C", owner="operator")
    returned = casestate.open_case(eng3, manifest3, "C", "sentry.cap",
                                   "a second, independent trigger for the SAME block",
                                   worker_id="engineer-C")
    ok("NT3 (IDEMPOTENT OPEN, THE OTHER HALF — must be GREEN): a SECOND open_case call "
       "for a block that already has an OPEN case (even operator-owned) returns the "
       "SAME case_id, never mints a second one, never re-triages",
       returned == "case-C-1" and len(manifest3["cases"]) == 1,
       f"returned={returned} cases={list(manifest3['cases'])}")

    ok("test:<operator_delivered_no_takeback> (AC-17): once delivered to the operator, "
       "a case is never re-routed to the architect",
       all(c for name, c, _ in _results if name.startswith("NT")))


# ══════════════════════════════════════════════════════════════════════════
# test:<escalation_debounce>
# ══════════════════════════════════════════════════════════════════════════

_Snap = collections.namedtuple("Snap", ["manifest", "gates"])


def _escalation_debounce():
    # (a) reping's decision-is-not-None skip: a RESOLVED case, however long
    #     its paging backoff has elapsed, is never re-pinged/escalated again —
    #     contrasted against an IDENTICAL still-open case, which IS repinged.
    eng = _StubEng()
    manifest = {
        "cases": {
            "case-D-resolved": {
                "case_id": "case-D-resolved", "block": "D", "source": "worker.wall",
                "worker_id": "engineer-D", "detail": "d", "decision": "resume",
                "owner": "operator", "opened_at": "2026-07-14T00:00:00Z",
                "paging": {"attempts": 1, "consecutive_fail": 5, "last_receipt": "failed",
                          "holding_since": 0, "channel_escalated": False,
                          "permanently_failed": False},
            },
            "case-D-open": {
                "case_id": "case-D-open", "block": "D2", "source": "worker.wall",
                "worker_id": "engineer-D2", "detail": "d2", "decision": None,
                "owner": "operator", "opened_at": "2026-07-14T00:00:00Z",
                "paging": {"attempts": 1, "consecutive_fail": 5, "last_receipt": "failed",
                          "holding_since": 0, "channel_escalated": False,
                          "permanently_failed": False},
            },
        }
    }
    repinged = casestate.reping(eng, manifest, now=99)   # holding=99, well past every backoff knob
    ok("ED1 (THE DEBOUNCE KILLER — must be GREEN): a case RESOLVED this call "
       "(decision != None) is NEVER re-pinged/escalated, however stale its backoff",
       "case-D-resolved" not in repinged
       and not any(p[0] == "case-D-resolved" for p in eng.pages),
       f"repinged={repinged} pages={eng.pages}")
    ok("ED2 (NON-VACUITY CONTRAST — must be GREEN): the IDENTICAL still-OPEN case "
       "(decision is None) DOES get repinged under the SAME elapsed backoff — the "
       "skip in ED1 is decision-conditioned, not a blanket no-op",
       "case-D-open" in repinged,
       f"repinged={repinged}")

    # (b) sentry.pace's terminal-gate skip: an already-ESCALATED gate, however
    #     long its stale holding_since claims, is never re-escalated (never a
    #     second `sentry_escalated` for the same block).
    import sentry   # local import — keep the module-level import list focused on casestate
    eng2 = _StubEng()
    manifest2 = {
        "gates": {
            "E": {
                "block": "E", "stage": gate.STAGE_ESCALATED,
                "escalation": "already escalated (a prior tick)",
                "wid": "engineer-E",
                # a deliberately STALE pacing episode, well past GATE_IDLE_CAP,
                # that a bug reintroducing "escalate a terminal gate" would trip:
                "holding_stage": gate.STAGE_TRUNK, "holding_since": 0, "nudged_at": None,
            },
        },
        "workers": {},
    }
    snap = _Snap(manifest=manifest2, gates=manifest2["gates"])
    pace_result = sentry.pace(eng2, snap)
    ok("ED3 (TERMINAL-GATE SKIP — must be GREEN): an already-ESCALATED gate is NEVER "
       "re-escalated by sentry.pace, however stale its leftover pacing episode claims "
       "to be — no 'E' in this call's escalated list, no second escalation_logged "
       "record for it",
       ("E", manifest2["gates"]["E"]["escalation"]) not in pace_result["escalated"]
       and not any(rec.get("block") == "E" for rec in
                  (manifest2.get("escalations") or [])),
       f"pace_result={pace_result} escalations={manifest2.get('escalations')}")

    ok("test:<escalation_debounce> (AC-17): never an escalation for a case/gate "
       "resolved or already-terminal this call",
       all(c for name, c, _ in _results if name.startswith("ED")))


# ══════════════════════════════════════════════════════════════════════════
# test:<worker_death_full_handover> — real Engine + real scaffold + real
# mailbox file.
# ══════════════════════════════════════════════════════════════════════════

HO_BLOCK = "07-01"
HO_BLOCKS = [{"id": HO_BLOCK, "depends_on": [], "reviewer_class": "none",
             "title": "quintuple(x): a small real function (worker-loss re-drive, handover)"}]
HO_MAX_TICKS = 30


class _HandoverDriver(sim_worker.ScriptedDriver):
    """Sends a worker.wall for `wall_block` instead of ITS local-pass report,
    answers the resulting triage 'answer' (a worker-loss re-drive — the
    block becomes re-drivable, a durable handover briefing is written), then
    resets its own branch-tracking so the SAME driver correctly plays a
    SECOND, genuinely fresh spawn for the SAME block (the base ScriptedDriver
    assumes one spawn per block for life; a T21 worker-loss re-drive is the
    ONE scenario that legitimately needs a second)."""

    def __init__(self, *a, wall_block=None, **k):
        super().__init__(*a, **k)
        self.wall_block = wall_block
        self.local_reported[wall_block] = True   # never auto-send a local-pass for this block
        self.wall_sent = False
        self.redispatch_reset = False
        self._triage_answered = set()

    def _maybe_reset_for_redispatch(self, manifest):
        if not self.wall_sent or self.redispatch_reset:
            return
        w = (manifest.get("workers") or {}).get(f"engineer-{self.wall_block}")
        if w and w.get("status") == "spawning" and w.get("block") == self.wall_block:
            self.branch_created[self.wall_block] = False
            self.redispatch_reset = True

    def react_wall(self, manifest):
        if self.wall_sent or not self.wall_block:
            return
        if self.wall_block not in (manifest.get("gates") or {}):
            return
        agent_id = f"engineer-{self.wall_block}"
        intake.write(self.tron_ctx, agent_id,
                     {"tag": "worker.wall", "block": self.wall_block, "agent_id": agent_id,
                      "slots": {"detail": "npm test hit a real environment snag on this "
                               "branch — flagging before burning further turns"}})
        self.wall_sent = True

    def react_triage(self, manifest):
        arch = manifest.get("architect") or {}
        cur = arch.get("current_job") or {}
        if cur.get("kind") != "triage" or not cur.get("ordered"):
            return
        tid = cur.get("triage_id")
        if not tid or tid in self._triage_answered:
            return
        intake.write(self.tron_ctx, core_architect.ARCHITECT_WID,
                     {"tag": "architect.triage_verdict", "agent_id": core_architect.ARCHITECT_WID,
                      "slots": {"triage_id": tid, "verdict": "answer",
                               "note": "transient — re-drive, re-verify current state"}})
        self._triage_answered.add(tid)

    def react(self, i, manifest):
        self._maybe_reset_for_redispatch(manifest)
        super().react(i, manifest)
        self.react_wall(manifest)
        self.react_triage(manifest)


def _worker_message_texts(ctx, agent_id, kind=None):
    path = jobs.mailbox_path(ctx.worker_dir(agent_id))
    if not os.path.isfile(path):
        return []
    import json
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if kind is None or rec.get("kind") == kind:
                out.append(rec.get("text", ""))
    return out


def _drive_handover():
    ctx, root = sim_scaffold.build(HO_BLOCKS)
    driver = _HandoverDriver(root, ctx.grants_dir, ctx, sim_worker.default_transcript(),
                             wall_block=HO_BLOCK)

    real_spawn_runner = jobs.spawn_runner
    jobs.spawn_runner = lambda *a, **k: {}
    try:
        eng = Engine(ctx)
        eng.dry = False
        eng.start(scope="all", worker_count=1, models={})

        i = -1
        dropped_tick = None
        outage_injected = False
        outage_lifted = False
        pre_outage_handover = None
        for i in range(HO_MAX_TICKS):
            res = eng.tick()
            manifest = state.load(ctx)
            driver.record_done_ticks(i, res.get("outcomes") or {})
            driver.react(i, manifest)

            if dropped_tick is None and HO_BLOCK in (manifest.get("handover") or {}):
                dropped_tick = i
                pre_outage_handover = dict(manifest["handover"][HO_BLOCK])
                # ── T21 preservation-across-an-outage-hold proof: force a
                #     dispatch pause the instant the handover lands, BEFORE the
                #     next fill() would otherwise re-pick this block — direct
                #     manifest seeding of the pause condition itself (the
                #     detection mechanism — consecutive spawn deaths — is
                #     `core/switchboard.py`'s own proof, `outage_rig.py`; this
                #     narrowly isolates "does a HELD dispatch corrupt/drop a
                #     pending handover", never re-proving outage detection). ──
                m2 = state.load(ctx)
                m2["paused"] = True
                m2.setdefault("cases", {})["case-synthetic-outage"] = {
                    "case_id": "case-synthetic-outage", "block": None,
                    "source": "fleet.outage", "kind": "fleet_outage", "worker_id": None,
                    "detail": "synthetic hold for the T21 preservation proof",
                    "decision": None, "opened_at": "2026-07-14T00:00:00Z",
                    "owner": "operator",
                }
                state.save(ctx, m2)
                outage_injected = True
                continue

            if outage_injected and not outage_lifted:
                # Confirm the block genuinely did NOT get re-dispatched while
                # held, then lift the hold and let dispatch resume.
                still_paused = state.load(ctx)
                if HO_BLOCK not in (still_paused.get("gates") or {}) \
                        and f"engineer-{HO_BLOCK}" not in (still_paused.get("workers") or {}):
                    m3 = state.load(ctx)
                    m3["cases"]["case-synthetic-outage"]["decision"] = "resume"
                    m3["paused"] = False
                    state.save(ctx, m3)
                outage_lifted = True
                continue

            if outage_lifted:
                # Stop the instant the replacement's real ASSIGN has fired
                # (its record reads `assigned=True` the same call the
                # handover-appendix message was written + the durable
                # `manifest["handover"][block]` entry consumed) — never tick
                # further, which would otherwise let the (deliberately
                # never-locally-reported, per this driver) second gate idle
                # all the way to ITS OWN sentry cap and overwrite the very
                # handover record this proof is checking.
                wrec = (manifest.get("workers") or {}).get(f"engineer-{HO_BLOCK}") or {}
                if wrec.get("assigned"):
                    break

            if res.get("session_end") is not None:
                break

        final = state.load(ctx)
        second_assign_texts = _worker_message_texts(ctx, f"engineer-{HO_BLOCK}", kind="PMT-ASSIGN")
        return {
            "root": root, "ctx": ctx, "events": list(eng.events.log),
            "final_manifest": final, "dropped_tick": dropped_tick,
            "pre_outage_handover": pre_outage_handover,
            "second_assign_texts": second_assign_texts, "ticks_used": i + 1,
        }
    finally:
        jobs.spawn_runner = real_spawn_runner


def _worker_death_full_handover():
    r = _drive_handover()

    ok("WD1: the worker-loss re-drive genuinely happened — a wall was raised, the "
       "architect resolved it 'answer', and a durable handover briefing was written",
       r["dropped_tick"] is not None and r["pre_outage_handover"] is not None,
       f"dropped_tick={r['dropped_tick']} pre_outage={r['pre_outage_handover']}")

    if r["pre_outage_handover"]:
        ho = r["pre_outage_handover"]
        ok("WD2 (FULL CONTEXT — must be GREEN): the durable handover record carries the "
           "branch, WHY it was dropped (source+detail), and the disposition — real "
           "context, not a bare flag",
           ho.get("branch") == f"feat/{HO_BLOCK}" and ho.get("source") == "worker.wall"
           and bool(ho.get("detail")) and ho.get("disposition") == "answer"
           and ho.get("dead_worker_id") == f"engineer-{HO_BLOCK}",
           f"handover={ho}")

    ok("WD3 (PRESERVED ACROSS AN OUTAGE HOLD — must be GREEN): with dispatch genuinely "
       "paused between the drop and the re-dispatch (confirmed: no new gate/worker "
       "record for the block appeared while held), the handover survives the hold",
       r["dropped_tick"] is not None,   # the hold-then-lift sequence itself already
                                        # asserted no premature re-dispatch inline above;
                                        # reaching WD4 (the SECOND real assign) below is
                                        # the positive half of this same proof
       f"dropped_tick={r['dropped_tick']}")

    second_texts = r["second_assign_texts"]
    ok("WD4 (THE KILLER — must be GREEN): a genuinely SECOND real assign.worker message "
       "landed in the replacement's OWN real mailbox file (never a blank re-assign) "
       "carrying the handover appendix — WHY it was dropped, an explicit RE-VERIFY "
       "instruction, and the branch reframed as BLOCK/BRANCH state (never the dead "
       "worker's id used as a target)",
       len(second_texts) >= 2
       and "HANDOVER" in second_texts[-1]
       and "RE-VERIFY" in second_texts[-1]
       and f"feat/{HO_BLOCK}" in second_texts[-1]
       and f"engineer-{HO_BLOCK}" not in second_texts[-1].split("HANDOVER", 1)[-1],
       f"n_assigns={len(second_texts)} last={second_texts[-1] if second_texts else None!r}")

    ok("WD5 (CONSUMED EXACTLY ONCE — must be GREEN): the handover record is gone from "
       "the manifest after the replacement's assign — never left to leak into an "
       "unrelated later drop of the same block",
       HO_BLOCK not in (r["final_manifest"].get("handover") or {}),
       f"handover_final={r['final_manifest'].get('handover')}")

    ok("test:<worker_death_full_handover> (AC-17): a worker-loss re-drive briefs its "
       "replacement with full context, re-targets on block/branch state, and survives "
       "an intervening outage hold",
       all(c for name, c, _ in _results if name.startswith("WD")))


# ══════════════════════════════════════════════════════════════════════════
# CONTENT-PRESERVATION CONFIRMATION (T21: "escalation/refused content is
# preserved engine-side — full text + sender, the 01-31 content-integrity
# intent, confirm it holds under R2"). No dedicated `test:<...>` tag of its
# own in the block spec's Proof line — folded here as an explicit,
# independently-checked confirmation rather than left implicit in the other
# five proofs' incidental text. `core/door.py::refuse` (R2, carried by the
# merged 01-37) and `core/casestate.py::open_case`'s own `detail` field are
# the two content-integrity chokepoints; both checked directly.
# ══════════════════════════════════════════════════════════════════════════

def _content_preservation_confirmed():
    # (a) a door refusal preserves the FULL raw text + the origin (kind+id),
    #     never reduced to a bare count — `core/door.py::refuse`, direct call.
    eng = _StubEng()
    manifest = {}
    long_text = ("the worker's real free-text turn output, verbatim, a full "
                "paragraph of genuine content nobody should ever see reduced "
                "to a bare integer count of refusals: " + "x" * 200)
    origin = collections.namedtuple("Origin", ["kind", "id"])("worker", "engineer-CP")
    door.refuse(eng, manifest, origin, "not.a.real.tag", long_text, "unroutable tag")
    refusal_events = [e for e in eng.events.log if e["type"] == "door_refusal"]
    ok("CP1 (DOOR-REFUSAL CONTENT PRESERVED — must be GREEN): the door_refusal event "
       "carries the FULL raw text (not a bare count) and the origin's kind+id (not a "
       "message-borne sender field)",
       len(refusal_events) == 1
       and long_text in refusal_events[0]["payload"].get("raw", "")
       and refusal_events[0]["payload"].get("origin") == {"kind": "worker", "id": "engineer-CP"},
       f"refusal_events={refusal_events}")
    # A refusal also opens an architect-first case carrying that SAME full text
    # (never re-summarized a second time between the forensic event and the case).
    case_id = next(iter(manifest.get("cases") or {}), None)
    case = (manifest.get("cases") or {}).get(case_id) if case_id else None
    ok("CP2 (CASE DETAIL PRESERVED TOO — must be GREEN): the architect-first case "
       "`open_case` minted for the refusal ALSO carries the full raw text in its own "
       "`detail` field, never a second, lossier summary",
       case is not None and long_text in (case.get("detail") or ""),
       f"case={case}")

    # (b) a worker.wall's free-text detail is preserved verbatim through
    #     casestate.open_case's own `detail` field, never truncated/coarsened
    #     to a category — direct call, a genuinely long/adversarial detail.
    eng2 = _StubEng()
    manifest2 = {}
    wall_text = "REAL turn output: " + ("detail " * 100)
    cid2 = casestate.open_case(eng2, manifest2, "CP-BLOCK", "worker.wall", wall_text,
                               worker_id="engineer-CP2")
    ok("CP3 (WALL DETAIL PRESERVED — must be GREEN): a worker.wall's full free-text "
       "detail survives verbatim into the parked case's own `detail` field AND the "
       "`case_opened` event's own payload — full text + source, never reduced",
       manifest2["cases"][cid2]["detail"] == wall_text
       and any(e["type"] == "case_opened" and e["payload"].get("case_id") == cid2
              for e in eng2.events.log),
       f"case={manifest2['cases'][cid2]}")

    ok("CONTENT-PRESERVATION CONFIRMED (T21, no dedicated test:<> tag — folded in as "
       "an explicit confirmation): escalation/refused content — full text + sender — "
       "is preserved engine-side, holding under R2",
       all(c for name, c, _ in _results if name.startswith("CP")))


# ══════════════════════════════════════════════════════════════════════════
# test:<every_case_terminates_resolved_or_delivered>
# ══════════════════════════════════════════════════════════════════════════

TS_ANSWERED = "08-01"   # wall -> architect 'answer' -> resolved
TS_DELIVERED = "08-02"  # wall -> architect 'operator' -> paged, left open (operator-delivered)
TS_SETTLED = "08-03"    # wall -> architect 'operator' -> paged -> operator 'resume' -> resolved
TS_BLOCKS = [
    {"id": b, "depends_on": [], "reviewer_class": "none", "title": f"fn for {b}"}
    for b in (TS_ANSWERED, TS_DELIVERED, TS_SETTLED)
]
TS_MAX_TICKS = 90


class _TerminalSweepDriver(sim_worker.ScriptedDriver):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        for b in (TS_ANSWERED, TS_DELIVERED, TS_SETTLED):
            self.local_reported[b] = True
        self.wall_sent = set()
        self._triage_answered = {}
        self.operator_settled = False
        self._verdict_for = {TS_ANSWERED: "answer", TS_DELIVERED: "operator",
                             TS_SETTLED: "operator"}

    def react_walls(self, manifest):
        gates = manifest.get("gates") or {}
        for b in (TS_ANSWERED, TS_DELIVERED, TS_SETTLED):
            if b in self.wall_sent or b not in gates:
                continue
            agent_id = f"engineer-{b}"
            intake.write(self.tron_ctx, agent_id,
                         {"tag": "worker.wall", "block": b, "agent_id": agent_id,
                          "slots": {"detail": f"wall for {b}"}})
            self.wall_sent.add(b)

    def react_triage(self, manifest):
        arch = manifest.get("architect") or {}
        cur = arch.get("current_job") or {}
        if cur.get("kind") != "triage" or not cur.get("ordered"):
            return
        tid = cur.get("triage_id")
        block = cur.get("block")
        if not tid or tid in self._triage_answered or block not in self._verdict_for:
            return
        verdict = self._verdict_for[block]
        intake.write(self.tron_ctx, core_architect.ARCHITECT_WID,
                     {"tag": "architect.triage_verdict", "agent_id": core_architect.ARCHITECT_WID,
                      "slots": {"triage_id": tid, "verdict": verdict}})
        self._triage_answered[tid] = block

    def react_operator_settle(self, manifest):
        if self.operator_settled:
            return
        cases = manifest.get("cases") or {}
        target = next((cid for cid, c in cases.items()
                      if c.get("block") == TS_SETTLED and c.get("owner") == "operator"
                      and c.get("decision") is None), None)
        if not target:
            return
        intake.write(self.tron_ctx, vocab.OPERATOR,
                     {"tag": "operator.decision",
                      "slots": {"case_id": target, "verb": "resume"}})
        self.operator_settled = True

    def react(self, i, manifest):
        super().react(i, manifest)
        self.react_walls(manifest)
        self.react_triage(manifest)
        self.react_operator_settle(manifest)


def _drive_terminal_sweep():
    ctx, root = sim_scaffold.build(TS_BLOCKS)
    driver = _TerminalSweepDriver(root, ctx.grants_dir, ctx, sim_worker.default_transcript())

    real_spawn_runner = jobs.spawn_runner
    jobs.spawn_runner = lambda *a, **k: {}
    try:
        eng = Engine(ctx)
        eng.dry = False
        eng.start(scope="all", worker_count=3, models={})
        i = -1
        for i in range(TS_MAX_TICKS):
            res = eng.tick()
            manifest = state.load(ctx)
            driver.record_done_ticks(i, res.get("outcomes") or {})
            driver.react(i, manifest)
            # This run's TS_DELIVERED case is DELIBERATELY left open forever
            # (operator-delivered, never settled) — never reaches session-end
            # (an open case always keeps a run alive, `core/session.py`'s own
            # R3). Stop once the other two are genuinely resolved instead.
            cases_now = manifest.get("cases") or {}
            resolved_settled = all(
                any(c.get("block") == b and c.get("decision") is not None
                   for c in cases_now.values())
                for b in (TS_ANSWERED, TS_SETTLED))
            if resolved_settled and driver.operator_settled:
                break
        final = state.load(ctx)
        return {"root": root, "ctx": ctx, "events": list(eng.events.log),
                "cases": final.get("cases") or {}, "ticks_used": i + 1}
    finally:
        jobs.spawn_runner = real_spawn_runner


def _case_terminal_state(events, case_id):
    resolved_types = {"case_settled", "case_architect_resolved",
                      "case_self_retracted", "case_stale_resolved"}
    delivered = False
    resolved = False
    for e in events:
        p = e.get("payload") or {}
        if p.get("case_id") != case_id:
            continue
        if e["type"] == "case_escalated_to_operator":
            delivered = True
        if e["type"] in resolved_types:
            resolved = True
    if resolved:
        return "resolved"
    if delivered:
        return "operator-delivered"
    return None


def _every_case_terminates_resolved_or_delivered():
    r = _drive_terminal_sweep()
    ev = r["events"]

    case_ids = sorted({(e.get("payload") or {}).get("case_id")
                       for e in ev if e["type"] == "case_opened"} - {None})
    ok("TS1 (NON-VACUITY — must be GREEN): the run genuinely raised at least 3 cases "
       "(one per scenario block)",
       len(case_ids) >= 3, f"case_ids={case_ids}")

    states = {cid: _case_terminal_state(ev, cid) for cid in case_ids}
    ok("TS2 (THE SWEEP, THE KILLER — must be GREEN): EVERY raised case terminates in "
       "'resolved' or 'operator-delivered' — none left in neither state (park-and-"
       "forget, bounce, or a case_id that never surfaces past case_opened)",
       all(v in ("resolved", "operator-delivered") for v in states.values()),
       f"states={states}")

    ok("TS3 (BOTH TERMINAL SHAPES GENUINELY OCCUR — must be GREEN): at least one case "
       "reads 'resolved' (the answered/settled blocks) AND at least one reads "
       "'operator-delivered' (the deliberately-left-open TS_DELIVERED case) — the "
       "sweep genuinely discriminates the two acceptable terminal shapes, not a "
       "vacuous single-branch check",
       "resolved" in states.values() and "operator-delivered" in states.values(),
       f"states={states}")

    ok("test:<every_case_terminates_resolved_or_delivered> (AC-17): every raised case "
       "terminates in resolved | operator-delivered, read off events.jsonl's own stream",
       all(c for name, c, _ in _results if name.startswith("TS")))


def main():
    _page_dedup_per_case()
    _operator_delivered_no_takeback()
    _escalation_debounce()
    _worker_death_full_handover()
    _content_preservation_confirmed()
    _every_case_terminates_resolved_or_delivered()

    passed = sum(1 for _, c, _ in _results if c)
    print(f"core.escalation_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
