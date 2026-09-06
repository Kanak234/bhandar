# भंडार (BHANDAR)

A helper for pushing a batch of local projects up to GitHub. It reads a project
list and drives the create-and-push steps so many repositories can be published
in one pass.

The point of the tool is the check that runs *before* the push: anything that
reaches a public GitHub repo is effectively permanent, so a project is only
published once it has been scanned for secrets.

> Detailed notes are in [`PADHO.txt`](PADHO.txt) (Hindi), and the command
> reference is in [`CLAUDE-CODE-COMMANDS.md`](CLAUDE-CODE-COMMANDS.md).

## Files

- `bhandar.sh` — the driver script
- `pariyojana.tsv` — the project list (tab-separated)
- `aujaar/raaz_jaancho.py` — secret-scan helper (checks for keys before pushing)
- `parakh.sh` — the test suite for this repo

## Run

```bash
./bhandar.sh dekho      # dry run — what would happen, changes nothing
./bhandar.sh jaancho    # secret scan across every listed project
./bhandar.sh karo       # create the repos and push (asks first)
./bhandar.sh haal       # what is committed / pushed, per project
```

Scan one project on its own:

```bash
python3 aujaar/raaz_jaancho.py ~/Desktop/some-project
```

## What the scan actually looks at

`git push` uploads what git has, not what the folder holds — and those are two
different things. The scan covers both sides of that gap:

- **Files that will be pushed.** Tracked files plus untracked ones that
  `.gitignore` does not exclude. A properly ignored `.env` is not flagged,
  because it never leaves the machine. Use `--sab` to scan the whole folder
  regardless.
- **Git history.** A key that was committed once and deleted later still ships
  with the push. Removing the file does not remove it from history.

Exit codes: `0` clean, `1` something found, `2` bad usage.

False positives (a fake key in an example, say) can be waived by putting the
offending substring in a `.raazignore` file at the project root, one per line.

## Test

```bash
./parakh.sh
```

Every case builds real git repositories in a temp directory and runs the real
scripts. What it does **not** cover is the `gh repo create` / `git push` half of
`karo`, which would need to create actual GitHub repos — verify that by hand
against a throwaway private repo.

## Requires

- `bash`, `git`, and the GitHub CLI (`gh`) authenticated; Python 3 for the
  secret-scan helper.
- A configured git identity (`user.name` and `user.email`) — `karo` checks this
  up front, because commits made with an auto-derived email are not attributed
  to your GitHub account.

## Status

Working automation script for the author's own multi-repo publishing workflow.
