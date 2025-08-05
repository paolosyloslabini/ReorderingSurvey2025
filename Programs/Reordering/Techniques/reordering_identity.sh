#!/usr/bin/env bash
# reordering_identity.sh <matrix> <out_perm> [key=value ...]
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

nrows=$(awk 'NR>1 && !/^%/ {print $1; exit}' "$1")
seq 1 "$nrows" > "$2"
