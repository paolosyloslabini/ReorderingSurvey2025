#!/bin/bash
# demo_cusparse.sh - Demonstration of cuSPARSE multiplication setup
# 
# This script demonstrates how to use the cuSPARSE multiplication
# implementation in the ReorderingSurvey2025 framework.

set -euo pipefail

echo "=== cuSPARSE Multiplication Demo ==="
echo

# Source the environment configuration
source Programs/exp_config.sh

# Create a simple test matrix if needed
DEMO_DIR="/tmp/cusparse_demo"
mkdir -p "$DEMO_DIR/Raw_Matrices/demo"
TEST_MATRIX="$DEMO_DIR/Raw_Matrices/demo/test.mtx"

if [[ ! -f "$TEST_MATRIX" ]]; then
    echo "Creating test matrix..."
    cat > "$TEST_MATRIX" << 'EOF'
%%MatrixMarket matrix coordinate real general
8 8 8
1 1 2.0
2 2 3.0
3 3 1.5
4 4 4.0
5 5 2.5
6 6 1.0
7 7 3.5
8 8 2.0
EOF
fi

# Set up results directory
export RESULTS_DIR="$DEMO_DIR/Results"
export MATRIX_DIR="$DEMO_DIR/Raw_Matrices"
mkdir -p "$RESULTS_DIR"

echo "1. Testing CUDA environment..."
echo "   CUDA toolkit available: $(command -v nvcc && echo "YES" || echo "NO")"
echo "   GPU available: $(command -v nvidia-smi && echo "YES" || echo "NO")"
echo

echo "2. Building cuSPARSE implementation..."
cd Programs/Multiplication
if make test-env; then
    echo "   CUDA environment looks good"
    if make clean && make; then
        echo "   ✓ cuSPARSE implementation built successfully"
        CUDA_BUILD_SUCCESS=true
    else
        echo "   ✗ cuSPARSE build failed - will demonstrate error handling"
        CUDA_BUILD_SUCCESS=false
    fi
else
    echo "   ✗ CUDA environment not available - will demonstrate error handling"
    CUDA_BUILD_SUCCESS=false
fi
cd ../..

echo

echo "3. Running reordering (required for multiplication)..."
bash Programs/Reorder.sbatch "$TEST_MATRIX" identity
echo "   ✓ Reordering completed"

echo

echo "4. Testing multiplication implementations..."

# Test mock multiplication (should always work)
echo "   Testing mock multiplication..."
REORDER_CSV="$RESULTS_DIR/Reordering/test/identity_default/results.csv"
if bash Programs/Multiply.sbatch "$REORDER_CSV" mock alpha=1.5; then
    echo "   ✓ Mock multiplication successful"
    MOCK_CSV="$RESULTS_DIR/Multiplication/test/identity_default/mock/results.csv"
    if [[ -f "$MOCK_CSV" ]]; then
        echo "   Results:"
        python3 -c "
import pandas as pd
df = pd.read_csv('$MOCK_CSV')
print(f'     - Implementation: {df.loc[0, \"mult_type\"]}')
print(f'     - Parameters: {df.loc[0, \"mult_param_set\"]}')
print(f'     - Time: {df.loc[0, \"mult_time_ms\"]:.2f} ms')
print(f'     - Status: {\"SUCCESS\" if df.loc[0, \"exit_code\"] == 0 else \"FAILED\"}')
"
    fi
else
    echo "   ✗ Mock multiplication failed"
fi

echo

# Test cuSPARSE multiplication
echo "   Testing cuSPARSE multiplication..."
if bash Programs/Multiply.sbatch "$REORDER_CSV" cucsrspmm alpha=1.0 beta=0.0 num_cols_B=32; then
    echo "   ✓ cuSPARSE multiplication successful"
    CUSPARSE_CSV="$RESULTS_DIR/Multiplication/test/identity_default/cucsrspmm/results.csv"
    if [[ -f "$CUSPARSE_CSV" ]]; then
        echo "   Results:"
        python3 -c "
import pandas as pd
df = pd.read_csv('$CUSPARSE_CSV')
print(f'     - Implementation: {df.loc[0, \"mult_type\"]}')
print(f'     - Parameters: {df.loc[0, \"mult_param_set\"]}')
print(f'     - Time: {df.loc[0, \"mult_time_ms\"]:.2f} ms')
if 'gflops' in df.columns and not pd.isna(df.loc[0, 'gflops']):
    print(f'     - Performance: {df.loc[0, \"gflops\"]:.2f} GFLOPS')
print(f'     - Status: {\"SUCCESS\" if df.loc[0, \"exit_code\"] == 0 else \"FAILED\"}')
"
    fi
else
    echo "   ⚠ cuSPARSE multiplication failed (expected if CUDA not available)"
    echo "     This is normal if running without GPU support"
fi

echo

echo "5. Configuration examples..."
echo "   Available cuSPARSE parameter sets from config/multiply.yml:"
python3 -c "
import yaml
with open('config/multiply.yml', 'r') as f:
    config = yaml.safe_load(f)
for i, params in enumerate(config['cucsrspmm']['params']):
    param_str = ' '.join([f'{k}={v}' for k, v in params.items()])
    print(f'     Set {i+1}: {param_str}')
"

echo

echo "=== Demo Complete ==="
echo
echo "The cuSPARSE multiplication setup includes:"
echo "• C++/CUDA implementation (Programs/Multiplication/cusparse_spmm.cu)"
echo "• Automatic build system (Programs/Multiplication/Makefile)"
echo "• Integration wrapper (Programs/Multiplication/Techniques/operation_cucsrspmm.sh)"
echo "• Environment detection and error handling"
echo "• Performance metrics collection (timing, GFLOPS)"
echo "• Configurable parameters (alpha, beta, matrix dimensions)"
echo
echo "For clusters with CUDA/GPU support:"
echo "  sbatch Programs/Multiply.sbatch <reorder_csv> cucsrspmm alpha=1.0 num_cols_B=64"
echo
echo "For testing without GPU:"
echo "  sbatch Programs/Multiply.sbatch <reorder_csv> mock alpha=1.0"

# Cleanup
rm -rf "$DEMO_DIR"