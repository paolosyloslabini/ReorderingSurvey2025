#!/usr/bin/env bash
# reordering_ro.sh <matrix> <out_perm> [key=value ...]
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

RO_BIN="$PROJECT_ROOT/build/rabbit_order/demo/reorder"

if [[ ! -x "$RO_BIN" ]]; then
    echo "Rabbit Order binary not found at $RO_BIN" >&2
    echo "Run './scripts/bootstrap_ro.sh' to build Rabbit Order" >&2
    exit 1
fi

# Convert Matrix Market to edge list format for Rabbit Order
MATRIX="$1"
TEMP_EDGES=$(mktemp)

python3 -c "
import scipy.io
import numpy as np
import sys

# Read Matrix Market file
try:
    A = scipy.io.mmread('$MATRIX')
    A = A.tocoo()  # Convert to coordinate format
    
    # Convert to edge list format with zero-based indexing
    with open('$TEMP_EDGES', 'w') as f:
        for i, j in zip(A.row, A.col):
            if i != j:  # Skip diagonal entries for reordering
                f.write(f'{i} {j}\n')
except Exception as e:
    print(f'Error converting matrix: {e}', file=sys.stderr)
    sys.exit(1)
"

# Check if conversion succeeded and produced edges
if [[ ! -s "$TEMP_EDGES" ]]; then
    echo "Error: No edges found in matrix (matrix may be diagonal)" >&2
    rm -f "$TEMP_EDGES"
    exit 1
fi

# Run Rabbit Order and convert output to 1-based indexing
"$RO_BIN" "$TEMP_EDGES" | awk '{print $1+1}' > "$2"

# Clean up temporary file
rm -f "$TEMP_EDGES"
