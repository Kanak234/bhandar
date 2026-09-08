#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Verify script syntax
bash -n "$ROOT/bhandar.sh"
echo "[✓] bhandar.sh syntax verification passed"

if [ -f "$ROOT/pariyojana.tsv" ]; then
    echo "[✓] pariyojana.tsv exists"
fi
exit 0
