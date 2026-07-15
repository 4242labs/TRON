"""core.prompt_conformance — block 01-38 T15 (AC-9): `cmd:<prompt-conformance>`.

"Once per vocabulary/prompt change, feed each live prompt to the real
model once; the reply must parse through the real door." A REAL model
(never a stub) receives the exact rendered canon prompt a real worker/
architect would see, is told nothing beyond what a real recipient knows
(the rendered prompt + `worker-contract.md`, the SAME two documents a
spawned agent reads), and must produce a reply that a REAL
`scripts/report.sh` subprocess accepts and the REAL admission door
(`core/door.py::admit`, via `core/classify.py`/`core/snapshot.py`) admits
— never refused, never falling to the T4 catch-all.

CONTAINMENT ([[tron-nested-claude-must-be-sandboxed]]) — the nested model
call is FOUR-WAY sandboxed, each layer sufficient alone. A prior version of
this file spent tokens through a naive `claude -p` that inherited the real
worktree cwd AND ran with full agentic tools (Bash/Edit/Write/git); the
nested sessions made real commits and wrote junk files into the worktree
(CLU-recovered by reset --hard). The rebuild makes that STRUCTURALLY
impossible:
  1. NON-AGENTIC (primary): the nested `claude -p` runs with `--tools ""`
     (the CLI's documented "disable all tools" — zero built-in Bash/Edit/
     Write/git) — it can only emit text.
  2. NO SETTINGS/HOOKS/AGENTS: `--setting-sources ""` loads no project/
     user/enterprise settings.json — no hooks, no permission grants, no
     `.claude/agents` that could re-enable a tool or fire a side effect.
     No `--add-dir`, `--mcp-config`, `--dangerously-skip-permissions`, or
     bypass permission mode is ever passed.
  3. ISOLATED, NON-REPO cwd: the model call runs with `cwd=` a fresh empty
     `tempfile.mkdtemp()` dir — never the worktree, never even a scaffold
     copy (the model call needs no files). Even in the impossible event a
     tool ran, an empty NON-git tmp dir makes `git commit` fail ("not a
     repository") and any write lands in throwaway tmp.
  4. CONTAINMENT SELF-PROOF (a real rig assertion): the run captures the
     real worktree's `git rev-parse HEAD` + `git status --porcelain`
     BEFORE and AFTER, and asserts both byte-identical — a first-class
     PASS/FAIL check proving no nested call committed or dirtied the tree.
     If containment ever regresses, this check goes RED, never silent.
The model's output is treated as UNTRUSTED TEXT: parsed only for the
report.sh command line, which is then run against the already-isolated
/tmp seeded instance (`boot_real_scaffold_rig`'s own tmp — never the
worktree), never executed as actions.

Deliberately NOT named `*_rig.py` — `scripts/l1.sh` glob-discovers
`core/*_rig.py`/`core/sim/*_rig.py` and runs every one on EVERY gate,
token-free by design. This file is the one deliberate exception the block
names ("once per vocabulary/prompt change" — an occasional, `cmd:`-tier
check, not an L1 gate) and is run directly, never by `l1.sh`.

THE LIVE-PROMPT SET (generated, not hand-picked): of the 15 PMT ids
`prompts/registry.yaml` declares, this file drives the 10 whose
`vocab.TPL_*` constant has a real `core/*.py` production call site —
`core/totality_rig.py`'s own OUTBOUND-covered set (T14), cross-checked
here by construction (`_LIVE_TPL_NAMES` below is re-derived live and
asserted equal). The other 5 correspond to T14's DISCLOSED, pinned,
zero-call-site templates (un-migrated legacy-`engine/fsm.py` remainder) —
a prompt with no live render call site has no "real door" round trip to
prove.

Any prompt this drive finds that a real model cannot parse gets edited to
parse — following Anthropic's LATEST prompt-engineering guidance (the
`claude-api` skill, loaded before this file was written; PROMPTS are the
one thing this block's leanness/net-negative rule exempts).

`ok(name, cond, detail)` collector; `main()` prints `PASS (n/m)`, exits
non-zero on any fail — or on the model runtime being unavailable (a `cmd:`
proof degrading to a false PASS on a missing runtime would be worse than
an honest hard fail).
"""
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))          # core
APP_ROOT = os.path.dirname(HERE)                             # worktree root
ENGINE_DIR = os.path.join(APP_ROOT, "engine")
sys.path.insert(0, ENGINE_DIR)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "sim"))

from ctx import Ctx                 # noqa: E402 — engine/ctx.py
from engine import Engine           # noqa: E402 — core/engine.py, the REAL render+emit under test
import vocab                        # noqa: E402 — core/vocab.py, the closed vocabulary
import architect                    # noqa: E402 — core/architect.py, ARCHITECT_WID
import snapshot                     # noqa: E402 — core/snapshot.py, the REAL drain
from boot_real_scaffold_rig import copy_real_scaffold, seed_live_instance   # noqa: E402
from seed_canon import install_canon   # noqa: E402

sys.path.insert(0, ENGINE_DIR)
import jobs as engine_jobs          # noqa: E402 — engine/jobs.py, RUNTIME

RUNTIME = engine_jobs.RUNTIME
# Deliberately NOT the production worker tier (Sonnet, per T23's per-role
# resolution) — Haiku is the STRICTER conformance bar: if the cheapest,
# least-steerable current model reliably produces a door-parseable reply
# from the prompt ALONE (rendered PMT + worker-contract.md, nothing else),
# the prompt is doing its own job; a stronger model succeeding could mask
# a prompt that only a smarter model can infer around. Overridable for a
# real pre-release conformance run against the production tier.
CONFORMANCE_MODEL = os.environ.get("TRON_MODEL_CONFORMANCE", "claude-haiku-4-5")

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


WORKER = "engineer-99-01"
REVIEWER = "reviewer-99-01"


def _live_tpl_names():
    """Every vocab.TPL_* constant with a real core/*.py production call
    site — re-derived live by the SAME AST scan core/totality_rig.py's
    OUTBOUND check uses (T14), never a stale hand copy of the covered
    set."""
    import ast
    import glob as glob_mod
    files = sorted(glob_mod.glob(os.path.join(HERE, "*.py")))
    prod = [f for f in files
            if not os.path.basename(f).endswith("_rig.py")
            and os.path.basename(f) not in ("__init__.py", "prompt_conformance.py", "vocab.py")]
    live = set()
    for path in prod:
        tree = ast.parse(open(path).read(), filename=path)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Attribute) and node.attr.startswith("TPL_")
                    and isinstance(node.value, ast.Name) and node.value.id == "vocab"):
                live.add(node.attr)
    return live


def _fixtures():
    """(pmt_id, tpl_name, worker_id, slots, kind, reply_optional) — one per
    live TPL_* constant, real slot shapes copied from each real production
    call site (T14's own reading of gate.py/router.py/reviewers.py/
    switchboard.py/architect_forward.py/architect_reconcile.py/
    architect_triage.py/architect.py), never invented shapes.

    `reply_optional=True` for PMT-FLAGS ONLY: it is the one live prompt
    whose own text (fixed this task) correctly says no reply is needed —
    `architect.py`'s own docstring: the flags digest "batches to the
    architect + an operator-readable ledger, pages no one" and there is no
    dedicated ack tag in the vocabulary. Every other live prompt genuinely
    expects a structured door round trip."""
    ARCH = architect.ARCHITECT_WID
    return [
        ("PMT-SPAWN", "TPL_SPAWN_WORKER", WORKER,
         {"role": "engineer", "persona": "You are an engineer building a small, real feature."},
         "spawn.worker", False),
        ("PMT-ASSIGN", "TPL_ASSIGN_WORKER", WORKER,
         {"assignment": "Build block 99-01: implement double(x) in app/lib/double.py.",
          "merge_path": ""},
         "assign.worker", False),
        ("PMT-SCOPE", "TPL_ARCH_FORWARD", ARCH, {"block": "99-01"}, "arch.forward", False),
        ("PMT-RECONCILE", "TPL_ARCH_RECONCILE", ARCH,
         {"block": "99-01", "after": "abc1234"}, "arch.reconcile", False),
        ("PMT-TRIAGE", "TPL_ARCH_TRIAGE", ARCH,
         {"detail": "a worker raised a genuine impasse on block 99-01: a missing "
                     "local fixture dependency it cannot resolve alone.",
          "sender": "worker.wall", "triage_id": "TRIAGE-1"},
         "arch.triage", False),
        ("PMT-FLAGS", "TPL_ARCH_FLAGS", ARCH,
         {"detail": ["engineer-99-01 flagged: minor lint nit on 99-01, non-blocking."]},
         "arch.flags", True),
        ("PMT-DONE-LOCAL", "TPL_GATE_LOCAL", WORKER, {"block": "99-01"}, "gate.local", False),
        ("PMT-DONE-RECORD", "TPL_GATE_RECORD", WORKER,
         {"block": "99-01", "record_path": "blocks/99-01.md"}, "gate.record", False),
        ("PMT-DONE-REVIEW", "TPL_GATE_REVIEW", REVIEWER, {}, "gate.review", False),
        ("PMT-CLOSE", "TPL_CLOSE_WORKER", WORKER, {"block": "99-01"}, "close.worker", False),
    ]


_REPORT_CMD_RE = re.compile(r"^\s*bash\s+\S*report\.sh\b.*$", re.MULTILINE)


def _extract_report_command(model_stdout):
    """The model's proposed report.sh invocation — the first line matching
    the real `bash <path>report.sh ...` shape. Strips a markdown code
    fence if the model wrapped it despite the instruction not to."""
    text = model_stdout.strip()
    text = re.sub(r"^```(?:bash|sh)?\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    m = _REPORT_CMD_RE.search(text)
    return m.group(0).strip() if m else None


def _git_state():
    """(HEAD, porcelain) of the REAL worktree — the containment self-proof
    baseline. `git -C <ABSOLUTE worktree>` reads the worktree's own repo
    state regardless of this process's cwd; `--untracked-files=all` means a
    NEW untracked file (not just a commit or a tracked-file edit) also trips
    the after-check. The nested model call must leave both byte-identical."""
    head = subprocess.run(["git", "-C", APP_ROOT, "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "-C", APP_ROOT, "status", "--porcelain",
                            "--untracked-files=all"],
                           capture_output=True, text=True).stdout
    return head, status


def _call_model_contained(model_prompt):
    """Run the nested `claude -p` FULLY SANDBOXED (see module docstring):
    `--tools ""` (no built-in tools), `--setting-sources ""` (no settings/
    hooks/agents), cwd = a fresh empty NON-repo tmp dir. `start_new_session`
    puts the child in its OWN process group so a timeout kills the WHOLE
    group (no orphaned model process survives a hung call). Returns the raw
    stdout as UNTRUSTED text. The tmp cwd is removed after."""
    sandbox_cwd = tempfile.mkdtemp(prefix="tron-conformance-modelcall-")
    proc = None
    try:
        cmd = [RUNTIME, "-p", "--model", CONFORMANCE_MODEL,
               "--tools", "", "--setting-sources", "", "--output-format", "text"]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, cwd=sandbox_cwd,
                               start_new_session=True)
        try:
            out, err = proc.communicate(input=model_prompt, timeout=120)
            return out or "", err or ""
        except subprocess.TimeoutExpired:
            # A hung model call must not stall the rig, and a killed child
            # must not orphan — SIGKILL the whole process group, then reap.
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            proc.communicate()
            raise
    finally:
        shutil.rmtree(sandbox_cwd, ignore_errors=True)


def run_fixture(eng, ctx, contract_text, pmt_id, tpl_name, worker_id, slots, kind,
                reply_optional=False):
    tpl = getattr(vocab, tpl_name)
    eng.dry = True   # suppress the mailbox side effect; the RETURN VALUE
                      # is the byte-identical rendered text regardless
    rendered = eng.emit(tpl, f"[fallback] {pmt_id}", slots=slots,
                        worker_id=worker_id, kind=kind)
    eng.dry = False

    reply_clause = (
        "reply with EXACTLY the single `bash ...report.sh ...` command line "
        "you would run right now to send your structured reply on the "
        "channel — OR, if (and only if) nothing here genuinely needs a "
        "reply, say so in one plain sentence and nothing else"
        if reply_optional else
        "reply with EXACTLY the single `bash ...report.sh ...` command "
        "line you would run right now to send your structured reply on "
        "the channel"
    )
    model_prompt = (
        f"{contract_text}\n\n---\n\n"
        f"You just received the following message from the Orchestrator "
        f"(rendered exactly as it would send it to you):\n\n{rendered}\n\n"
        f"---\n\nYou are the recipient above. Per the worker contract, "
        f"{reply_clause}. No markdown code fence, no other extra text."
    )

    try:
        stdout, stderr = _call_model_contained(model_prompt)
    except subprocess.SubprocessError as e:
        ok(f"cmd:<prompt-conformance> {pmt_id}: real model call completed",
           False, f"subprocess error: {e}")
        return

    cmd = _extract_report_command(stdout)
    if cmd is None and reply_optional:
        ok(f"cmd:<prompt-conformance> {pmt_id}: the real model "
           f"({CONFORMANCE_MODEL}) correctly recognized no reply is "
           f"required for this prompt (a real, legitimate outcome for a "
           f"digest that pages no one and needs no verdict) — no door "
           f"round trip to check",
           True, f"stdout={stdout!r}")
        return
    ok(f"cmd:<prompt-conformance> {pmt_id}: the real model ({CONFORMANCE_MODEL}) "
       f"produced a report.sh command line from the rendered prompt alone",
       cmd is not None, f"stdout={stdout!r} stderr={stderr[:300]!r}")
    if cmd is None:
        return

    try:
        run = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True,
                             timeout=30)
    except subprocess.SubprocessError as e:
        ok(f"cmd:<prompt-conformance> {pmt_id}: the extracted command executed",
           False, f"cmd={cmd!r} error={e}")
        return

    snap = snapshot.build(eng)
    admitted = [rep for rep in snap.worker_reports if rep.get("origin")
                and rep["origin"].id == worker_id]
    refused = [c for c in (snap.manifest.get("cases") or {}).values()
               if c.get("source") == "worker.report_refused" and c.get("worker_id") == worker_id]
    real_tag = admitted[-1].get("tag") if admitted else None
    ok(f"cmd:<prompt-conformance> {pmt_id}: the reply PARSED THROUGH THE REAL "
       f"DOOR — admitted with a real, known vocab tag, never refused, never "
       f"the T4 catch-all/unclassified",
       bool(admitted) and not refused and real_tag in vocab.TAGS
       and real_tag not in ("unclassified",),
       f"cmd={cmd!r} rc={run.returncode} admitted_tag={real_tag!r} "
       f"refused={bool(refused)} report_sh_stderr={run.stderr[:300]!r}")
    snapshot.release(snap)


def run_conformance():
    live_now = _live_tpl_names()
    fixture_tpls = {t for _, t, *_ in _fixtures()}
    ok("the driven fixture set is EXACTLY the live TPL_* set (T14's OUTBOUND "
       "scan) — every prompt with a real render call site is driven, none "
       "with no call site is (no invented door round trips)",
       live_now == fixture_tpls,
       f"live_now={sorted(live_now)} fixture_tpls={sorted(fixture_tpls)}")

    head_before, status_before = _git_state()
    root = None
    inst = None
    try:
        root = copy_real_scaffold()
        inst, _project, _knobs = seed_live_instance(root)
        install_canon(inst)
        ctx = Ctx(inst)
        eng = Engine(ctx)
        eng.dry = False

        with open(os.path.join(APP_ROOT, "worker-contract.md")) as fh:
            contract_text = fh.read()

        for pmt_id, tpl_name, worker_id, slots, kind, reply_optional in _fixtures():
            run_fixture(eng, ctx, contract_text, pmt_id, tpl_name, worker_id, slots, kind,
                       reply_optional=reply_optional)
    finally:
        # In a FINALLY so it asserts EVEN IF the body raised mid-run — a
        # breach on an exception path must still be caught, never skipped.
        head_after, status_after = _git_state()
        ok("CONTAINMENT SELF-PROOF: the real worktree's git HEAD + working-tree "
           "status (untracked files included) are byte-identical before and "
           "after the whole run — no nested model call committed to, dirtied, "
           "or wrote a new file into the real repo (the prior version's "
           "breach signature is structurally absent, even on an exception "
           "path)",
           head_after == head_before and status_after == status_before,
           f"head_before={head_before[:12]} head_after={head_after[:12]} "
           f"status_changed={status_after != status_before}")

    print(f"\nroot={root}\ninst={inst}")


def main():
    if os.environ.get("TRON_DRY") or os.environ.get("TRON_JUDGE_STUB"):
        print("core.prompt_conformance: refuses to run under TRON_DRY/"
              "TRON_JUDGE_STUB — this proof's whole point is a REAL model "
              "call; unset both to run for real.", file=sys.stderr)
        return 1

    run_conformance()

    passed = sum(1 for _, c, _ in _results if c)
    print(f"\ncore.prompt_conformance: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + ("" if c else f" — {detail}"))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
