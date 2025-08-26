#!/usr/bin/env bash
# Build SMAT (SMaT) sparse matrix multiplication library
# Clones from https://github.com/spcl/smat and builds the hgemm binary
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
SMAT_DIR="$BUILD/smat"

SMAT_REPO="https://github.com/spcl/smat.git"
SMAT_COMMIT="HEAD"  # Use latest commit, can be pinned later

mkdir -p "$BUILD"

echo "Building SMAT sparse matrix multiplication library"
echo "================================================="

# Check for CUDA availability
if ! command -v nvcc &> /dev/null; then
    echo "Warning: nvcc not found. SMAT requires CUDA for GPU operations."
    echo "Please install CUDA Toolkit before building SMAT."
    exit 1
fi

# Check for required dependencies
echo "Checking dependencies..."
if ! pkg-config --exists gflags; then
    echo "Error: gflags library not found. Please install with:"
    echo "  sudo apt-get install libgflags-dev"
    exit 1
fi

# Clone SMAT if not already present
if [[ ! -d "$SMAT_DIR" ]]; then
    echo "Cloning SMAT repository..."
    git clone "$SMAT_REPO" "$SMAT_DIR"
fi

cd "$SMAT_DIR"

# Checkout specific commit if specified
if [[ "$SMAT_COMMIT" != "HEAD" ]]; then
    git checkout "$SMAT_COMMIT"
fi

# Determine GPU architecture automatically
echo "Detecting GPU architecture..."
GPU_ARCH=""
if command -v nvidia-ml-py &> /dev/null; then
    # Try to use nvidia-ml-py if available
    GPU_ARCH=$(python3 -c "
import pynvml
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)
major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
print(f'{major}{minor}')
" 2>/dev/null || echo "")
fi

# Fallback to common architectures if detection fails
if [[ -z "$GPU_ARCH" ]]; then
    echo "Could not detect GPU architecture automatically."
    echo "Using default architecture 86 (RTX 30xx series)."
    echo "Override with: ./bootstrap_smat.sh <architecture>"
    GPU_ARCH="${1:-86}"
fi

echo "Building SMAT for GPU architecture: $GPU_ARCH"

# Build SMAT
cd "$SMAT_DIR/src/cuda_hgemm"

# Make build script executable if not already
chmod +x build.sh

# Build SMAT
if ./build.sh -a "$GPU_ARCH" -t Release -b OFF; then
    echo "SMAT built successfully!"
    echo "Binary location: $SMAT_DIR/output/bin/hgemm"
    
    # Make sure the binary is executable
    chmod +x "$SMAT_DIR/output/bin/hgemm" 2>/dev/null || true
    
    # Add to PATH suggestion
    echo ""
    echo "To use SMAT, add to your environment:"
    echo "  export PATH=\"\$PATH:$SMAT_DIR/output/bin\""
    echo "Or:"
    echo "  export SMAT_HOME=\"$SMAT_DIR/output\""
    
else
    echo "Error: SMAT build failed"
    echo "Check CUDA installation and GPU architecture setting"
    exit 1
fi