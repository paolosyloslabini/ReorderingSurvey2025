#!/usr/bin/env bash
# reordering_ro.sh <matrix> <out_perm> [key=value ...]
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

RO_BIN="$PROJECT_ROOT/build/rabbit_order/demo/reorder"

if [[ ! -x "$RO_BIN" ]]; then
    echo "Rabbit Order binary not found at $RO_BIN" >&2
    exit 1
fi

mode="reorder"

"$RO_BIN" "$1" | awk '{print $1+1}' > "$2"
