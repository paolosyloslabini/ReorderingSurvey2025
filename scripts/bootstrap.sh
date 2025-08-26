#!/usr/bin/env bash
# Top-level bootstrap driver.
# Currently delegates Rabbit Order installation to bootstrap_ro.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

"$ROOT/scripts/bootstrap_ro.sh" "$@"
