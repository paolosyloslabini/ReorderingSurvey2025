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

echo ""
echo "Bootstrap completed successfully!"
echo "All dependencies are now available for the reordering framework."
