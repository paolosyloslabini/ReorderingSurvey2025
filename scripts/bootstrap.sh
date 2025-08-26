#!/usr/bin/env bash
# Top-level bootstrap driver for all external dependencies.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "ReorderingSurvey2025 Bootstrap Script"
echo "======================================"
echo ""
echo "This script builds all external dependencies"
echo ""

# Build Rabbit Order and all its dependencies
"$ROOT/scripts/bootstrap_ro.sh" "$@"

# Build SMAT sparse matrix multiplication library
echo ""
echo "Building SMAT..."
if "$ROOT/scripts/bootstrap_smat.sh" "$@"; then
    echo "SMAT build completed successfully!"
else
    echo "Warning: SMAT build failed. SMAT multiplication will not be available."
    echo "This is expected if CUDA is not available."
fi

echo ""
echo "Bootstrap completed successfully!"
echo "All dependencies are now available for the reordering framework."
