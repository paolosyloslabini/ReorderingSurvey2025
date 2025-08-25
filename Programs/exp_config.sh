#!/usr/bin/env bash
# Cluster-wide environment and path definitions

# Determine the absolute project root (one level up from this file)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PROJECT_ROOT

# Allow overriding dataset and result locations.  By default both
# directories live inside the repository, but large deployments can
# point them elsewhere before sourcing this file.
export MATRIX_DIR="${MATRIX_DIR:-$PROJECT_ROOT/Raw_Matrices}"
export RESULTS_DIR="${RESULTS_DIR:-$PROJECT_ROOT/Results}"

# TODO: add module loads and other environment variables below

