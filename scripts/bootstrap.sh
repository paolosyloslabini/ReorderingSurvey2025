#!/usr/bin/env bash
# Top-level bootstrap driver.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"


# Currently delegates Rabbit Order installation to bootstrap_ro.sh.
"$ROOT/scripts/bootstrap_ro.sh" "$@"
