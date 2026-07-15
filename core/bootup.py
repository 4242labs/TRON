"""core.bootup — the operator's interactive bootup front to `core.engine.
Engine` (block 01-38 T23, consolidates 01-30 + 01-35 + 01-33's regression;
ADR-0003 D-D).

The new `core/*` engine had NO bootup/console surface at all before this
task — the operator journey lived only in the retiring `engine/console.py`
(read in full for T23's own frozen shape; see that module's docstring +
ADR-0003 D-D for the corrective history). This module restores it against
`core.engine.Engine` instead of the legacy `fsm.Engine`.

THE FROZEN SEQUENCE (byte-for-byte — no question/option/recommendation may
change without explicit operator sign-off, [[journey-frozen]]; this module
RESTORES the journey, it does not redesign it):

  1. scope            [1] all / [2] a phase / [3] a range of blocks
  2. worker_count      "worker_count (build + review workers; the
                        persistent spec-owner role is extra)? "
  3. ask-before-merging "Inform you before each merge to trunk? [y/N] "
  4. model, PER ROLE    "Model for {role label} [{recommended default}]? "
                        — recommends the role's OWN declared roles.yaml
                        model when present, else a per-tier default
                        (architect/spec-owner = a strong tier, every other
                        role = a fast tier) — 01-30 parity, restored per
                        ADR-0003 D-D after 01-33 stripped it.

Every prompt string below is copied verbatim from `engine/console.py`
(`_ask_scope`, the `worker_count` loop, the ask-before-merging line,
`_ask_role_models`/`_recommended_model`/`_role_label`) — this is the check
against which `test:<bootup_journey_sequence_frozen>` holds the sequence.

NOT in this module (deliberately, by task split):
  - The AIDE advisory calls (`_ask_aide_model`/`_aide_advise_scope`/
    `_aide_advise_counts` in the legacy console) — block 01-38 T24's job
    ("T24 wires the AIDE lane"); T23's own proof list names no AIDE test.
  - The REPL / fleet-view / attach / run-control commands — not named by
    any T23-25 acceptance criterion; only the BOOTUP JOURNEY is in scope
    here. Restoring the full interactive shell is not requested by this
    block and would be scope creep past what T23-25's ACs test.
  - Persisting the ask-before-merging / worker-model answers into the
    session-store manifest so a LATER tick (a fresh `Engine(ctx)`
    instance) still sees them — block 01-38 T25's own job
    (`test:<journey_persist_session_store_only>`). This module stashes
    both on itself (`self.ask_before_merging`, `self.worker_models`) so
    T25 has something to persist without re-deriving the answers; the
    worker-model answers ARE already effective for THIS boot's own spawns
    (the persistent architect + the first dispatch pass), since they are
    threaded straight into the SAME `Engine.start(models=...)` in-memory
    override `core/engine.py` already implements — only a SECOND, later
    `Engine` instance (e.g. a fresh wake-tick process) needs T25's durable
    layer.

FAIL-CLOSED MODEL RESOLUTION (AC-19): enforced at the root, inside
`core.engine.Engine.start()` itself (see that module's own T23 comment) —
not re-implemented here — so BOTH this interactive journey and a headless
caller that bypasses this module entirely (`eng.start(...)` directly, the
harness's own documented shape) get the identical fail-closed guarantee. A
`roles.RolesError` raised there propagates straight up through `bootup()`
uncaught, exactly like `engine.BootupError` already does.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import emit               # noqa: E402 — core/emit.py, the one emit API (the scope-fallback event)
import pipeline            # noqa: E402 — core/pipeline.py, the trunk-pinned view (scope resolution)
from engine import Engine, BootupError   # noqa: E402 — core/engine.py, the module this fronts

DIM, RST, BOLD = "\033[2m", "\033[0m", "\033[1m"

# ADR-0003 D-D — the bootup model question's RECOMMENDED fallback tier when
# a role's own roles.yaml declares no model: a strong tier for the
# persistent spec-owner role, a fast tier for everyone else. Shown as a
# confirm/override suggestion ONLY (never itself a silent resolution path —
# `core.engine.Engine.start`'s fail-closed `validate_models` call owns
# that). Byte-for-byte copy of `engine/console.py`'s own
# `ROLE_MODEL_RECOMMENDED`/`ROLE_MODEL_LABEL` — the frozen recommendation.
ROLE_MODEL_RECOMMENDED = {"architect": "claude-opus-4-8", "other": "claude-sonnet-4-5"}
ROLE_MODEL_LABEL = {"architect": "the persistent architect/spec-owner", "other": "engineers/reviewers"}


class Bootup:
    """The frozen operator bootup journey, ported into `core/*` against
    `core.engine.Engine`. Construct with a live `ctx` (`engine/ctx.py::Ctx`,
    the same runtime-context resolver `core.engine.Engine` itself takes),
    call `.bootup(staged_model=...)` once."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.ask_before_merging = None   # set by bootup() — T25 persists this
        self.worker_models = None        # set by bootup() — T25 persists this
        self.engine = None                # the booted Engine instance, post-bootup

    # ── 1. scope: [1] all / [2] a phase / [3] a range of blocks ──
    def _ask_scope(self, eng):
        """Byte-for-byte copy of `engine/console.py::_ask_scope`'s own
        prompt wording/options — the operator NEVER sees a different
        question here than the legacy engine asked. Returns the value
        `core.engine.Engine.start(scope=...)` expects: `"all"` or an
        explicit list of trunk block ids.

        Judgment call (disclosed, T23 WORK LOG): `core.engine.Engine.
        start()` resolves scope ONCE at boot as an explicit id list (see
        that module's own docstring: "never a re-derivation of a question
        this brick doesn't own") — unlike the legacy engine, which stores
        `{mode, value}` and re-filters every tick. The QUESTION and its
        THREE OPTIONS are unchanged (frozen); only the mechanical
        translation into core's boot-time id-list shape is new, and it
        reuses the legacy engine's OWN phase/range matching semantics
        (`engine/fsm.py::_in_scope_rows`, read for shape only) so the
        operator-visible RESULT of picking a phase/range is identical."""
        choice = input("  [1] all  ·  [2] a phase  ·  [3] a range of blocks  → ").strip()
        if choice == "2":
            phase = input("  Which phase (name or number, e.g. 'Phase 2' or '2')? ").strip()
            return self._resolve_phase_scope(eng, phase)
        if choice == "3":
            lo = input("  First block ID? ").strip()
            hi = input("  Last block ID? ").strip()
            return self._resolve_range_scope(eng, lo, hi)
        return "all"

    def _resolve_phase_scope(self, eng, phase):
        """`engine/fsm.py::_in_scope_rows`'s `mode == "phase"` arm,
        re-expressed against a fresh trunk-pinned read (`core.pipeline.
        read_view`) instead of a re-filter of `self.st.pipeline` every
        tick: substring, case-insensitive, over each row's own `phase`
        field. An empty phase answer (or one matching nothing on the
        trunk) is legitimate and unrestricted — never a typo/error at this
        step (the legacy engine's own `_bootup_gateway` only flags a
        NON-EMPTY unmatched phase as `scope-typo`, and even then merely
        holds the bootup gateway rather than raising; core's `Engine.
        start` already fails loud on an explicitly-named unknown block id,
        so an unmatched non-empty phase answer here safely degrades to
        "all" rather than duplicating that gateway)."""
        view, _sha = pipeline.read_view(eng)
        want = str(phase or "").strip().lower()
        if not want:
            return "all"
        ids = [row["id"] for row in view if want in str(row.get("phase") or "").lower()]
        if not ids:
            self._fallback_to_all(eng, "phase", phase,
                                  f"no trunk block's phase field matches {phase!r}")
            return "all"
        return ids

    def _resolve_range_scope(self, eng, lo, hi):
        """`engine/fsm.py::_in_scope_rows`'s `mode == "range"` arm: the
        inclusive slice of the trunk-pinned pipeline's own id ORDER
        between the two named endpoints (order swapped if given
        backwards). An unresolvable endpoint falls back to "all" — the
        exact legacy fallback (`except (ValueError, IndexError, TypeError):
        return rows`, i.e. every row, unrestricted)."""
        view, _sha = pipeline.read_view(eng)
        ids = [row["id"] for row in view]
        try:
            i, j = ids.index(lo), ids.index(hi)
        except ValueError:
            self._fallback_to_all(eng, "range", [lo, hi],
                                  f"endpoint {lo!r} or {hi!r} not found on the trunk-pinned "
                                  f"pipeline view")
            return "all"
        i, j = min(i, j), max(i, j)
        return ids[i:j + 1]

    def _fallback_to_all(self, eng, mode, value, reason):
        """A phase/range scope answer that resolves to NO trunk block ids
        (or an unresolvable endpoint) silently-widening to "all" is a known
        TRON silent-defaults killer — made observable two ways, never a
        quiet swallow: (1) a forensic `bootup_scope_fallback` event on
        `eng.events` (readable from `events.jsonl`, ground truth, even
        though no manifest exists yet at this pre-`Engine.start` point —
        see `core/emit.py`'s own registration comment); (2) a loud
        (non-DIM) operator-visible print, distinct from every other DIM
        informational line in this journey, so an interactive operator
        cannot miss that their answer was WIDENED rather than honored."""
        print(f"{BOLD}  ! scope {mode}={value!r} matched nothing on trunk ({reason}) — "
              f"widening to 'all'.{RST}")
        emit.record(eng, "bootup_scope_fallback", requested_mode=mode,
                   requested_value=value, reason=reason, resolved="all")

    # ── 2. worker_count ──
    def _ask_worker_count(self):
        """Byte-for-byte copy of `engine/console.py`'s own worker_count
        loop — identical prompt text, identical validation (a positive
        integer, re-asked until satisfied)."""
        worker_count = None
        while worker_count is None:
            v = input("worker_count (build + review workers; the persistent spec-owner "
                      "role is extra)? ").strip()
            if v.isdigit() and int(v) > 0:
                worker_count = int(v)
            else:
                print(f"{DIM}  (a positive integer){RST}")
        return worker_count

    # ── 3. ask-before-merging ──
    def _ask_before_merging_q(self):
        """Byte-for-byte copy of `engine/console.py`'s own ask-before-
        merging prompt. NOT wired into any downstream gating behavior by
        this task (no `core/*.py` module reads an `ask_before_merging`
        knob today) — restoring the ANSWER + its later session-store
        persistence is T23/T25's job; wiring the answer into the landing
        path is out of scope for this task (not named by any T23-25 AC)."""
        ans = input("Inform you before each merge to trunk? [y/N] ").strip().lower()
        return ans in ("y", "yes")

    # ── 4. model, per role ──
    def _role_label(self, role, cfg):
        tier = "architect" if (cfg.get("spec_owner") or cfg.get("persistent")) else "other"
        return f"{role} ({ROLE_MODEL_LABEL[tier]})"

    def _recommended_model(self, eng, role):
        """The default OFFERED at the bootup model prompt for `role` —
        never itself the resolution path (`core.engine.Engine.start`'s
        `validate_models` call owns that). Prefers the role's OWN declared
        roles.yaml `model:` field; falls back to the per-tier suggestion
        only when roles.yaml itself declares none for this role. Byte-for-
        byte copy of `engine/console.py::_recommended_model`."""
        rc = eng._roles_config()
        cfg = rc.roles.get(role) or {}
        declared = rc.model_for(role)
        if declared:
            return declared
        tier = "architect" if (cfg.get("spec_owner") or cfg.get("persistent")) else "other"
        return ROLE_MODEL_RECOMMENDED[tier]

    def _ask_role_models(self, eng, staged=None):
        """Ask the worker model PER ROLE — every role roles.yaml declares
        gets its own question, each showing a recommended default the
        operator confirms (Enter) or overrides. `staged` (01-30 T3
        parity) supplies the answers programmatically with NO prompt at
        all — a non-interactive call must never block on `input()`. A
        staged role with no answer (missing/blank) is left UNRESOLVED
        here (never silently given the recommended default) —
        `core.engine.Engine.start`'s `validate_models` call is the
        fail-closed guard for that; this method's own job is only to
        report whatever was actually decided, never to paper over an
        absent one. Byte-for-byte copy of `engine/console.py::
        _ask_role_models`'s own logic (retargeted at `core.engine.Engine`
        via `eng._roles_config()` instead of `eng.roles`)."""
        rc = eng._roles_config()
        answers = {}
        for role in sorted(rc.roles.keys()):
            if staged is not None:
                answers[role] = (staged.get(role) or "").strip() or None
                continue
            cfg = rc.roles.get(role) or {}
            default = self._recommended_model(eng, role)
            label = self._role_label(role, cfg)
            v = input(f"Model for {label} [{default}]? ").strip() or default
            answers[role] = v or None
        return answers

    # ── the whole journey ──
    def bootup(self, staged_model=None):
        """Run the frozen sequence, then boot the real engine.

        `staged_model` (01-30 T3 parity): an optional {role: model} dict
        supplied programmatically so the MODEL question never calls
        `input()` — a non-interactive bootup must never hang on a prompt.
        Interactive callers pass nothing and get asked, per role, exactly
        as the legacy console behaved. Scope/worker_count/ask-before-
        merging still prompt regardless (unchanged from the legacy
        engine's own `staged_model` scope, `engine/console.py:119-123`) —
        a caller that wants those non-interactive too seeds `input` itself
        (the same convention `tron-meta/sims/autopilot/bootstrap.py`'s
        live-boot launcher already uses against the legacy console).

        Returns `(engine, spawned)` — the booted `core.engine.Engine`
        instance and the list of freshly spawned agent-ids `Engine.start`
        itself returns."""
        print(f"{BOLD}== TRON bootup =={RST}")
        eng = Engine(self.ctx)

        scope = self._ask_scope(eng)
        worker_count = self._ask_worker_count()
        self.ask_before_merging = self._ask_before_merging_q()
        self.worker_models = self._ask_role_models(eng, staged=staged_model)

        spawned = eng.start(scope=scope, worker_count=worker_count, models=self.worker_models)
        self.engine = eng
        print()
        print(f"{DIM}  TRON is live. (session-store persistence of ask-before-merging / "
              f"per-role model answers past this boot is block 01-38 T25.){RST}\n")
        return eng, spawned
