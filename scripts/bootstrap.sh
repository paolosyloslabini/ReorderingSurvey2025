#!/usr/bin/env bash
# Top-level bootstrap driver for all external dependencies.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "ReorderingSurvey2025 Bootstrap Script"
echo "======================================"
echo ""
echo "This script builds all external dependencies from source, including:"
echo "  - Boost 1.58.0 (compatible with Rabbit Order)"
echo "  - libnuma 2.0.14"
echo "  - gperftools 2.10" 
echo "  - Rabbit Order (sparse matrix reordering algorithm)"
echo ""

# Build Rabbit Order and all its dependencies
"$ROOT/scripts/bootstrap_ro.sh" "$@"

echo ""
echo "Bootstrap completed successfully!"
echo "All dependencies are now available for the reordering framework."
