# TRON-FLYNN install

```zsh
modes/install.sh              # /tron-flynn in every project + the terminal shortcut
modes/install.sh ~/path/proj  # /tron-flynn in one project only
modes/install.sh --no-path    # skip the shell-rc PATH line
```

That is the whole install, fresh machine included. `install.sh` writes the slash command with
FLYNN's absolute path baked in, and adds one PATH line to your shell rc for the `tron-flynn`
shortcut. **No pointer files, no environment variables, no other machine state.**

`tron-flynn` opens the REPL already booted as FLYNN; `tron-flynn "audit tron"` passes the task
straight through.

FLYNN needs no hooks, no run flags, and no project-side install — it reads and advises, and writes
only when the operator directs it to.
