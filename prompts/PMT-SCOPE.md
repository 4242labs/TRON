[TRON]  Architect — scope {block} so it's ready to dispatch.

Anything you author goes on a branch — report the branch name (`--tag branch --branch <name>`); I gate it, then you land it on trunk yourself via the grant + `meta/scripts/land.sh` (I never land or merge — that's yours). Close the loop with `--tag reconciled --block {block}` either way — report it ready, or say exactly what's blocking the scope in the same note; there is no separate blocked/wall verb for you, `reconciled` is how a scope pass reports either outcome.
