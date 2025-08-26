#!/usr/bin/env bash
# Simplified bootstrap script to build essential dependencies for Rabbit Order
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
DEPS="$BUILD/deps"
LOG_FILE="$BUILD/bootstrap_minimal.log"

# Create directories
mkdir -p "$BUILD" "$DEPS"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Minimal Rabbit Order Dependencies Bootstrap ==="
echo "Started at: $(date)"
echo "Build directory: $BUILD"
echo "Dependencies directory: $DEPS"

# Dependency versions
NUMA_VERSION="2.0.14"
GPERFTOOLS_VERSION="2.10"

# URLs
NUMA_URL="https://github.com/numactl/numactl/releases/download/v${NUMA_VERSION}/numactl-${NUMA_VERSION}.tar.gz"
GPERFTOOLS_URL="https://github.com/gperftools/gperftools/releases/download/gperftools-${GPERFTOOLS_VERSION}/gperftools-${GPERFTOOLS_VERSION}.tar.gz"

# Build configuration
INSTALL_PREFIX="$DEPS"
export PREFIX="$INSTALL_PREFIX"
export PKG_CONFIG_PATH="$INSTALL_PREFIX/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="$INSTALL_PREFIX/lib:${LD_LIBRARY_PATH:-}"

# Function to download and extract
download_and_extract() {
    local url="$1"
    local name="$2"
    local dir="$3"
    
    echo "=== Building $name ==="
    cd "$BUILD"
    
    local tarball="$(basename "$url")"
    if [[ ! -f "$tarball" ]]; then
        echo "Downloading $name from $url"
        curl -L -f -o "$tarball" "$url" || {
            echo "ERROR: Failed to download $url"
            return 1
        }
    fi
    
    if [[ ! -d "$dir" ]]; then
        echo "Extracting $tarball"
        tar -xzf "$tarball" || {
            echo "ERROR: Failed to extract $tarball"
            return 1
        }
    fi
    
    cd "$dir"
}

# Function to check if library exists
lib_exists() {
    local lib_name="$1"
    [[ -f "$INSTALL_PREFIX/lib/lib${lib_name}.a" ]] || [[ -f "$INSTALL_PREFIX/lib/lib${lib_name}.so" ]]
}

# Build libnuma
build_numa() {
    if lib_exists "numa"; then
        echo "libnuma already built"
        return 0
    fi
    
    download_and_extract "$NUMA_URL" "libnuma ${NUMA_VERSION}" "numactl-${NUMA_VERSION}" || return 1
    
    echo "Building libnuma..."
    ./configure --prefix="$INSTALL_PREFIX" --enable-static --disable-shared
    make -j$(nproc)
    make install
    
    echo "libnuma built successfully"
}

# Build gperftools (for tcmalloc)
build_gperftools() {
    if lib_exists "tcmalloc_minimal"; then
        echo "gperftools already built"
        return 0
    fi
    
    download_and_extract "$GPERFTOOLS_URL" "gperftools ${GPERFTOOLS_VERSION}" "gperftools-${GPERFTOOLS_VERSION}" || return 1
    
    echo "Building gperftools..."
    ./configure --prefix="$INSTALL_PREFIX" --enable-static --disable-shared --enable-minimal
    make -j$(nproc)
    make install
    
    echo "gperftools built successfully"
}

# Build dependencies
echo "=== Phase 1: Building core dependencies ==="

build_numa || {
    echo "ERROR: Failed to build libnuma"
    exit 1
}

build_gperftools || {
    echo "ERROR: Failed to build gperftools"
    exit 1
}

echo "=== Phase 2: Attempting Rabbit Order build with system Boost ==="

# Clone Rabbit Order if not exists
RO_DIR="$BUILD/rabbit_order"
if [[ ! -d "$RO_DIR" ]]; then
    git clone --depth 1 https://github.com/araij/rabbit_order.git "$RO_DIR"
    git -C "$RO_DIR" checkout f67a79e427e2a06e72f6b528fd5464dfe8a43174
fi

# Try to use system boost if available
cd "$RO_DIR/demo"
cp Makefile Makefile.orig

# Check if we can find boost headers in common locations
BOOST_INCLUDE=""
for dir in /usr/include /usr/local/include; do
    if [[ -d "$dir/boost" ]]; then
        BOOST_INCLUDE="-I$dir"
        echo "Found system boost headers in $dir"
        break
    fi
done

# Create modified Makefile with local dependency paths and optional boost
cat > Makefile << EOF
# Modified Makefile for local dependencies and optional system boost
DEPS_PREFIX = $INSTALL_PREFIX
CXXFLAGS += -Wall -Wextra -Wcast-align -Wcast-qual -Wconversion -Wfloat-equal \\
            -Wformat=2 -Winit-self -Wmissing-declarations \\
            -Wmissing-include-dirs -Wpointer-arith -Wredundant-decls \\
            -Wswitch-default -Wuninitialized -Wwrite-strings \\
            -Wno-sign-conversion -Wno-unused-function \\
            -Wno-missing-declarations \\
            -fopenmp -std=c++14 -mcx16 -O3 -DNDEBUG \\
            -I\$(DEPS_PREFIX)/include $BOOST_INCLUDE
LDFLAGS  += -L\$(DEPS_PREFIX)/lib
LDLIBS   += -ltcmalloc_minimal -lnuma
TARGETS   = reorder

\$(TARGETS): %: %.cc
	\$(LINK.cc) -MD -o \$@ \$< \$(LDLIBS)
	@cp \$*.d .\$*.P; \\
	  sed -e 's/#.*//' -e 's/^[^:]*: *//' -e 's/ *\\\\\$\$//' \\
	      -e '/^\$\$/ d' -e 's/\$\$/ :/' < \$*.d >> .\$*.P; \\
	  rm -f \$*.d

.PHONY: clean
clean:
	\$(RM) \$(TARGETS) \$(TARGETS:%=.\%.P)

-include .*.P
EOF

# Try to build Rabbit Order
echo "Building Rabbit Order with available dependencies..."
make clean

echo "=== Build attempt with current setup ==="
if make 2>&1; then
    if [[ -x "./reorder" ]]; then
        echo "=== SUCCESS: Rabbit Order built successfully ==="
        echo "Binary location: $RO_DIR/demo/reorder"
        
        # Test the binary
        echo "Testing Rabbit Order binary..."
        echo -e "0 1\n1 2\n2 0" > test_graph.txt
        if ./reorder test_graph.txt > /dev/null 2>&1; then
            echo "Rabbit Order binary test passed"
            rm -f test_graph.txt
        else
            echo "WARNING: Rabbit Order binary test failed, but binary exists"
        fi
        
        echo "=== Build Summary ==="
        echo "Completed at: $(date)"
        echo "Dependencies installed in: $INSTALL_PREFIX"
        echo "Rabbit Order binary: $RO_DIR/demo/reorder"
        echo "Log file: $LOG_FILE"
        exit 0
    else
        echo "Build completed but binary not found"
    fi
else
    echo "=== BUILD FAILED ==="
    echo "The build failed. This is expected if boost libraries are not available system-wide."
    echo "Dependencies that were successfully built:"
    ls -la "$INSTALL_PREFIX/lib/"
    echo ""
    echo "To complete the build, boost libraries (≥1.58.0) need to be available."
    echo "You can either:"
    echo "1. Install boost system-wide if you have sudo access"  
    echo "2. Build boost from source and modify this script"
    echo "3. Use a different approach for the rabbit order functionality"
fi

echo "=== Partial Build Summary ==="
echo "Completed at: $(date)"
echo "Working dependencies installed in: $INSTALL_PREFIX"
echo "Log file: $LOG_FILE"
echo ""
echo "Environment variables for dependency use:"
echo "  export LD_LIBRARY_PATH=\"$INSTALL_PREFIX/lib:\$LD_LIBRARY_PATH\""
echo "  export PKG_CONFIG_PATH=\"$INSTALL_PREFIX/lib/pkgconfig:\$PKG_CONFIG_PATH\""

exit 1