#!/usr/bin/env bash
# Clone and compile third-party reordering libraries
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
mkdir -p "$BUILD"

# Rabbit Order ---------------------------------------------------------------
RO_DIR="$BUILD/rabbit_order"
if [[ ! -d "$RO_DIR" ]]; then
    git clone --depth 1 https://github.com/araij/rabbit_order.git "$RO_DIR"
    git -C "$RO_DIR" checkout f67a79e427e2a06e72f6b528fd5464dfe8a43174
fi
make -C "$RO_DIR/demo"

