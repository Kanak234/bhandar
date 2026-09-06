# भंडार (BHANDAR)

A helper for pushing a batch of local projects up to GitHub. It reads a project
list and drives the create-and-push steps so many repositories can be published
in one pass.

> Detailed notes are in [`PADHO.txt`](PADHO.txt) (Hindi), and the command
> reference is in [`CLAUDE-CODE-COMMANDS.md`](CLAUDE-CODE-COMMANDS.md).

## Files

- `bhandar.sh` — the driver script
- `pariyojana.tsv` — the project list (tab-separated)
- `aujaar/raaz_jaancho.py` — secret-scan helper (checks for keys before pushing)

## Run

```bash
bash bhandar.sh        # see PADHO.txt / CLAUDE-CODE-COMMANDS.md first
```

## Requires

- `bash`, `git`, and the GitHub CLI (`gh`) authenticated; Python 3 for the
  secret-scan helper.

## Status

Working automation script for the author's own multi-repo publishing workflow.
