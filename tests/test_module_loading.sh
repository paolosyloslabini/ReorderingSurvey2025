#!/usr/bin/env bash
# Test script for module loading functionality
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PROJECT_ROOT

echo "Testing module loading functionality..."

# Test 1: Load modules for rcm (should use python_scipy)
echo "Test 1: Loading modules for reorder/rcm"
source "$PROJECT_ROOT/Programs/load_modules.sh" "reorder" "rcm"

# Test 2: Load modules for identity (should use basic)
echo -e "\nTest 2: Loading modules for reorder/identity"
source "$PROJECT_ROOT/Programs/load_modules.sh" "reorder" "identity"

# Test 3: Load modules for cucsrspmm (should use cuda_cusparse)
echo -e "\nTest 3: Loading modules for multiply/cucsrspmm"
source "$PROJECT_ROOT/Programs/load_modules.sh" "multiply" "cucsrspmm"

# Test 4: Load modules for mock (should use basic)
echo -e "\nTest 4: Loading modules for multiply/mock"
source "$PROJECT_ROOT/Programs/load_modules.sh" "multiply" "mock"

# Test 5: Test with non-existent technique (should fallback to basic)
echo -e "\nTest 5: Loading modules for non-existent technique"
source "$PROJECT_ROOT/Programs/load_modules.sh" "reorder" "nonexistent"

echo -e "\nAll module loading tests completed successfully!"