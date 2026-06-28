[TRON]  {worker_id}, you're on {block}.

Create and name your own branch + worktree off trunk (project convention, e.g. `{branch}`) — it's yours and yours alone, no one else commits to it. Tell me the name you chose; I track your PR and CI by it, I never assume one.

- Read the block file in full; build exactly what its tasks and acceptance criteria specify, nothing more.
- Pull/rebase on trunk before you push (the root hook will reject a stale or direct-to-trunk push). Work on your branch only — never commit to a protected branch.
- Validate locally against the block's acceptance criteria BEFORE you report DONE. "Done" without evidence is not done — I will challenge it.
- Hit a blocker you cannot clear? Consult your declared peer first; if it stays walled, say so plainly and I will raise it.
- Do not self-terminate. When the work is in, report and wait. I close the process — you don't.
