r"""block_01_35_test — restore the operator bootup journey: model question + AIDE
recommendations (block 01-35, ADR-0003 D-D — an explicit amendment of ADR-0002 D4).

Context: block 01-33 (ADR-0002 D4, "fleet as config") removed the 01-30 bootup model
question + recommendation — an operator-journey step never re-authorized removed.
ADR-0003 D-D restores it: (T1) the model question + recommendation, per role,
01-30-parity; (T2) write-boundary-safe persistence — the answer lives ONLY in a
TRON-owned session store (this instance's own MANIFEST live_config, under
meta/agents/tron/), NEVER in the project-authored meta/tron/roles.yaml — with the
session answer layered over `role.model` (session wins for the session; else
role.model; boot-fatal only if neither resolves); (T3) AIDE recommendations at bootup
— which block to pick, which models — recommendation only, the operator decides.

Standalone runner convention (exit 0 = pass, no tokens, no network, no real `claude`).

Covers this block's own acceptance criteria
(blocks/01-35-restore-operator-bootup-journey.md):
  AC-1 test:<bootup_model_question_restored> — interactive bootup asks the model
       question (01-30 parity); the headless path (a harness calling eng.start()
       directly, exactly cmd_start's own shape) auto-answers from staged knobs and
       never prompts / never hangs.
  AC-2 test:<model_answer_write_boundary> — the answer persists ONLY under
       meta/agents/tron/ (this instance's own MANIFEST); roles.yaml is never touched
       (byte-identical, mtime-identical) and no engine write during bootup lands
       outside TRON's own sealed instance dir.
  AC-3 test:<model_precedence_fail_closed> — session answer wins for the session over
       a stale role.model; absent a session answer, role.model resolves as before;
       absent BOTH, boot is fatal (loud, named); a session answer alone can rescue an
       otherwise-boot-fatal missing roles.yaml model.
  AC-4 test:<aide_bootup_recommendations> — AIDE recommends (a) which block to pick
       and (b) which models, recommendation-only; the operator's own choice always
       wins over the recommendation in both cases.
AC-5 (journey-frozen byte-diff of scope/worker_count/ask-before-merging) is
`manual_by:engineer`, verified in the PR body, not exercised here. AC-6 is
`manual_by:operator` (live smoke).

01-30 parity mechanics (the restored question's own per-role ask/default/override
shape) are covered in block_01_30_test.py; this file covers the NEW contract 01-35
itself adds.

Run: python3 engine/block_01_35_test.py   (exit 0 = pass).
"""
import io
import os
import sys
import copy
import contextlib
import builtins

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

os.environ["TRON_DRY"] = "1"

import util                      # noqa: E402
import console                   # noqa: E402
import roles as roles_mod        # noqa: E402
from fsm import Engine           # noqa: E402
from state import State          # noqa: E402
from sentry_test import build, started, TRIVIAL_ROLES  # noqa: E402

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))


def _drive_bootup(ctx, answers, staged_model=None):
    orig_input = builtins.input
    it = iter(answers)
    builtins.input = lambda prompt="": next(it)
    try:
        console.Console(ctx).bootup(staged_model=staged_model)
    finally:
        builtins.input = orig_input


# ══════════════════════════════════════════════════════════════════════════
# AC-1 test:<bootup_model_question_restored>
# ══════════════════════════════════════════════════════════════════════════

def test_bootup_model_question_restored_interactive_and_headless():
    # (a) interactive: the question IS asked, with a recommended default shown.
    ctx, _ = build()
    seen = []
    orig_input = builtins.input

    def fake_input(prompt=""):
        seen.append(prompt)
        if prompt.startswith("Model for"):
            return ""     # accept every recommended default
        if prompt.startswith("  [1]"):
            return "1"
        if "worker_count" in prompt:
            return "1"
        if "Inform you" in prompt:
            return "n"
        return ""

    builtins.input = fake_input
    try:
        console.Console(ctx).bootup()
    finally:
        builtins.input = orig_input
    ok("AC-1 the interactive bootup DOES ask a model question (01-30 parity restored)",
       any(p.startswith("Model for") for p in seen), f"seen={seen}")
    ok("AC-1 ...with a recommended default shown in the prompt (bracketed)",
       any("[test-model]" in p for p in seen), f"seen={seen}")

    # (b) headless: a harness calling eng.start() directly (bypassing console entirely
    # — exactly cmd_start's own shape) with the model pre-staged in the session store
    # never prompts and never hangs.
    ctx2, _ = build()
    eng = Engine(ctx2)
    eng.st.live_config["worker_model"] = {"engineer": "staged-engineer",
                                          "reviewer-code": "staged-reviewer",
                                          "architect": "staged-architect"}

    def poison_input(prompt=""):
        raise AssertionError(f"the headless path must never prompt: {prompt!r}")

    orig_input2 = builtins.input
    builtins.input = poison_input
    try:
        eng.start(1)
    finally:
        builtins.input = orig_input2
    ok("AC-1 the headless path (direct eng.start(), no console) auto-answers from "
       "staged knobs with ZERO prompts and does not hang",
       bool(eng.st.data.get("session", {}).get("started_at")))


# ══════════════════════════════════════════════════════════════════════════
# AC-2 test:<model_answer_write_boundary>
# ══════════════════════════════════════════════════════════════════════════

def test_model_answer_write_boundary():
    ctx, repo = build()
    roles_path = os.path.join(repo, "meta", "tron", "roles.yaml")
    with open(roles_path, "rb") as f:
        before_bytes = f.read()
    before_mtime = os.path.getmtime(roles_path)

    written_paths = []
    orig_atomic = util.atomic_write
    orig_append = util.append_jsonl

    def spy_atomic(path, text):
        written_paths.append(os.path.abspath(path))
        return orig_atomic(path, text)

    def spy_append(path, obj):
        written_paths.append(os.path.abspath(path))
        return orig_append(path, obj)

    util.atomic_write = spy_atomic
    util.append_jsonl = spy_append
    try:
        _drive_bootup(ctx, answers=["1", "2", "n"],
                      staged_model={"engineer": "override-eng", "reviewer-code": "override-rev",
                                    "architect": "override-arch"})
    finally:
        util.atomic_write = orig_atomic
        util.append_jsonl = orig_append

    with open(roles_path, "rb") as f:
        after_bytes = f.read()
    after_mtime = os.path.getmtime(roles_path)
    ok("AC-2 roles.yaml content is byte-for-byte unchanged after a full bootup + "
       "model-answer run", before_bytes == after_bytes)
    ok("AC-2 roles.yaml was never even reopened for write (mtime unchanged)",
       before_mtime == after_mtime)
    ok("AC-2 no engine write during bootup ever targeted roles.yaml's path",
       os.path.abspath(roles_path) not in written_paths, f"written={written_paths}")

    ctx_dir = os.path.abspath(ctx.dir)
    outside = [p for p in written_paths
               if not (p == ctx_dir or p.startswith(ctx_dir + os.sep))]
    ok("AC-2 every write during bootup landed under TRON's own sealed instance dir "
       "(the meta/agents/tron/ equivalent — ctx.dir), none in the project repo",
       outside == [], f"outside={outside}")

    live = State(ctx).live_config
    ok("AC-2 the session model answer DID persist — into the TRON-owned MANIFEST "
       "(ctx.state, under ctx.dir) — proving it went somewhere real, just never "
       "roles.yaml",
       live.get("worker_model") == {"engineer": "override-eng", "reviewer-code": "override-rev",
                                    "architect": "override-arch"},
       f"worker_model={live.get('worker_model')}")
    ok("AC-2 the durable store IS ctx.state (manifest.yaml) — TRON's own instance dir",
       os.path.abspath(ctx.state).startswith(ctx_dir))


# ══════════════════════════════════════════════════════════════════════════
# AC-3 test:<model_precedence_fail_closed>
# ══════════════════════════════════════════════════════════════════════════

def test_model_precedence_fail_closed():
    ctx, _ = build()
    eng = Engine(ctx); started(eng)
    # (a) session answer overrides a stale role.model, for the session.
    eng.st.live_config["worker_model"] = {"engineer": "session-wins"}
    ok("AC-3 a session answer overrides roles.yaml's role.model for the session",
       eng._model_for_role("engineer") == "session-wins")
    # (b) no session answer -> falls through to role.model, exactly as before.
    eng.st.live_config["worker_model"] = {}
    ok("AC-3 with no session answer, the dispatcher reads role.model as today",
       eng._model_for_role("engineer") == eng.roles.model_for("engineer") == "test-model")

    # (c) neither a session answer nor a config model -> boot-fatal (fail-closed).
    ctx2, repo2 = build()
    doc = copy.deepcopy(TRIVIAL_ROLES)
    doc["roles"]["engineer"]["model"] = ""
    util.save_yaml(os.path.join(repo2, "meta", "tron", "roles.yaml"), doc)
    eng2 = Engine(ctx2)
    eng2.st.live_config["worker_count"] = 1
    raised, msg = False, ""
    try:
        eng2.start(1)
    except roles_mod.RolesError as e:
        raised, msg = True, str(e)
    ok("AC-3 neither a session answer nor a resolvable roles.yaml model is boot-fatal "
       "(D4's fail-closed preserved) — loud, named",
       raised and "engineer" in msg, f"raised={raised} msg={msg}")

    # (d) ...but a session answer alone RESCUES that same missing config — boots clean.
    ctx3, repo3 = build()
    util.save_yaml(os.path.join(repo3, "meta", "tron", "roles.yaml"), doc)
    eng3 = Engine(ctx3)
    eng3.st.live_config["worker_count"] = 1
    eng3.st.live_config["worker_model"] = {"engineer": "rescued-by-session"}
    rescued_ok = True
    try:
        eng3.start(1)
    except roles_mod.RolesError as e:
        rescued_ok = False
    ok("AC-3 a session answer rescues an otherwise-boot-fatal missing config model",
       rescued_ok)
    ok("AC-3 ...and the rescued session value is what actually resolves",
       eng3._model_for_role("engineer") == "rescued-by-session")

    # (e) sanity: RolesConfig constructed with NO session context still requires
    # roles.yaml's own model (unconditional backstop — validate_models(None)).
    rc = roles_mod.RolesConfig(doc["roles"], repo2)
    no_session_raised = False
    try:
        rc.validate_models()
    except roles_mod.RolesError:
        no_session_raised = True
    ok("AC-3 RolesConfig.validate_models with no session override matches pre-D-D "
       "behavior exactly (roles.yaml alone must supply every role's model)",
       no_session_raised)


# ══════════════════════════════════════════════════════════════════════════
# AC-4 test:<aide_bootup_recommendations>
# ══════════════════════════════════════════════════════════════════════════

def test_aide_bootup_recommendations():
    # (a) which block to pick — advisory, printed before the scope question, never
    # itself decides scope.
    ctx, _ = build()
    eng = Engine(ctx)
    eng.st.data["pipeline"] = [
        {"id": "A-01", "status": "to-do", "depends_on": [], "order": 1, "has_block_file": True},
        {"id": "A-02", "status": "to-do", "depends_on": ["A-01"], "order": 2, "has_block_file": True},
    ]
    c = console.Console(ctx)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        c._aide_recommend_block(eng)
    out = buf.getvalue()
    ok("AC-4 AIDE recommends block A-01 (deps satisfied, still open, first in order)",
       "A-01" in out, f"out={out!r}")

    # a block with unmet deps is never recommended over one whose deps ARE satisfied.
    ctx2, _ = build()
    eng2 = Engine(ctx2)
    eng2.st.data["pipeline"] = [
        {"id": "A-01", "status": "to-do", "depends_on": ["A-00"], "order": 1, "has_block_file": True},
        {"id": "A-02", "status": "to-do", "depends_on": [], "order": 2, "has_block_file": True},
    ]
    c2 = console.Console(ctx2)
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        c2._aide_recommend_block(eng2)
    out2 = buf2.getvalue()
    ok("AC-4 AIDE skips a block whose deps aren't satisfied and recommends the next "
       "eligible one instead", "A-02" in out2 and "A-01" not in out2, f"out2={out2!r}")

    # a brand-new instance (no cached pipeline yet) degrades to a neutral note —
    # never crashes, never fabricates a block id.
    ctx0, _ = build()
    eng0 = Engine(ctx0)
    c0 = console.Console(ctx0)
    buf0 = io.StringIO()
    with contextlib.redirect_stdout(buf0):
        c0._aide_recommend_block(eng0)
    ok("AC-4 no cached pipeline yet -> a neutral advisory note, never a crash",
       "AIDE" in buf0.getvalue())

    # the operator's OWN scope choice always wins — the recommendation never sets it.
    seen = []
    orig_input = builtins.input

    def fake_input(prompt=""):
        seen.append(prompt)
        if prompt.startswith("  [1]"):
            return "3"           # explicitly choose a RANGE, ignoring any recommendation
        if "First block" in prompt:
            return "A-02"
        if "Last block" in prompt:
            return "A-02"
        if "worker_count" in prompt:
            return "1"
        if "Inform you" in prompt:
            return "n"
        if prompt.startswith("Model for"):
            return ""
        return ""

    builtins.input = fake_input
    try:
        console.Console(ctx2).bootup()
    finally:
        builtins.input = orig_input
    scope = State(ctx2).scope
    ok("AC-4 the operator's own scope answer wins regardless of any recommendation "
       "(recommendation-only, never decides)",
       scope.get("mode") == "range" and scope.get("value") == ["A-02", "A-02"],
       f"scope={scope}")

    # (b) which models — the shown recommendation IS _recommended_model's own value,
    # and the operator's override still wins over it (same law as the block pick).
    eng3 = Engine(ctx); started(eng3)
    c3 = console.Console(ctx)
    rec = c3._recommended_model(eng3, "engineer")
    ok("AC-4 the model recommendation for a role matches roles.yaml's own declared "
       "model when set (the recommended default an operator sees)", rec == "test-model")
    seen2 = []
    orig_input2 = builtins.input

    def fake_input2(prompt=""):
        seen2.append(prompt)
        if prompt.startswith("Model for engineer"):
            return "operator-override"      # explicit override beats the recommendation
        if prompt.startswith("Model for"):
            return ""
        if prompt.startswith("  [1]"):
            return "1"
        if "worker_count" in prompt:
            return "1"
        if "Inform you" in prompt:
            return "n"
        return ""

    builtins.input = fake_input2
    try:
        console.Console(ctx).bootup()
    finally:
        builtins.input = orig_input2
    live = State(ctx).live_config
    ok("AC-4 an operator's explicit model override wins over the recommendation shown",
       live.get("worker_model", {}).get("engineer") == "operator-override",
       f"worker_model={live.get('worker_model')}")


def main():
    for fn in sorted(k for k in globals() if k.startswith("test_")):
        globals()[fn]()
    bad = [(n, d) for n, c, d in _results if not c]
    for n, c, d in _results:
        print(("PASS" if c else "FAIL"), n, (f" [{d}]" if d and not c else ""))
    print(f"{len(_results) - len(bad)}/{len(_results)} passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
