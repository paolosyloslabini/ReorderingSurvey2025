#!/usr/bin/env bash
# Bootstrap script using vcpkg boost and locally built dependencies
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
DEPS="$BUILD/deps"
LOG_FILE="$BUILD/bootstrap_vcpkg.log"

# Create directories
mkdir -p "$BUILD" "$DEPS"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Rabbit Order Bootstrap with vcpkg Boost ==="
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

# vcpkg boost paths
VCPKG_ROOT="/usr/local/share/vcpkg"
BOOST_INCLUDE="$VCPKG_ROOT/installed/x64-linux/include"
BOOST_LIB="$VCPKG_ROOT/installed/x64-linux/lib"

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

# Check if vcpkg boost is available
check_vcpkg_boost() {
    if [[ ! -d "$BOOST_INCLUDE/boost" ]] || [[ ! -f "$BOOST_LIB/libboost_atomic.a" ]]; then
        echo "ERROR: vcpkg boost not found. Please install with:"
        echo "  cd $VCPKG_ROOT && ./vcpkg install boost-atomic boost-range boost-optional --triplet=x64-linux"
        return 1
    fi
    echo "Found vcpkg boost installation"
    return 0
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

# Check vcpkg boost availability
echo "=== Phase 1: Checking vcpkg boost ==="
check_vcpkg_boost || exit 1

# Build dependencies
echo "=== Phase 2: Building local dependencies ==="

build_numa || {
    echo "ERROR: Failed to build libnuma"
    exit 1
}

build_gperftools || {
    echo "ERROR: Failed to build gperftools"
    exit 1
}

echo "=== Phase 3: Building Rabbit Order ==="

# Clone Rabbit Order if not exists
RO_DIR="$BUILD/rabbit_order"
if [[ ! -d "$RO_DIR" ]]; then
    git clone --depth 1 https://github.com/araij/rabbit_order.git "$RO_DIR"
    git -C "$RO_DIR" checkout f67a79e427e2a06e72f6b528fd5464dfe8a43174
fi

# Modify Rabbit Order Makefile to use vcpkg boost and local dependencies
cd "$RO_DIR/demo"
cp Makefile Makefile.orig

# Create modified Makefile
cat > Makefile << EOF
# Modified Makefile for vcpkg boost and local dependencies
DEPS_PREFIX = $INSTALL_PREFIX
BOOST_INCLUDE = $BOOST_INCLUDE
BOOST_LIB = $BOOST_LIB

CXXFLAGS += -Wall -Wextra -Wcast-align -Wcast-qual -Wconversion -Wfloat-equal \\
            -Wformat=2 -Winit-self -Wmissing-declarations \\
            -Wmissing-include-dirs -Wpointer-arith -Wredundant-decls \\
            -Wswitch-default -Wuninitialized -Wwrite-strings \\
            -Wno-sign-conversion -Wno-unused-function \\
            -Wno-missing-declarations \\
            -fopenmp -std=c++14 -mcx16 -O3 -DNDEBUG \\
            -I\$(DEPS_PREFIX)/include -I\$(BOOST_INCLUDE)

LDFLAGS  += -L\$(DEPS_PREFIX)/lib -L\$(BOOST_LIB)
LDLIBS   += -lboost_atomic -ltcmalloc_minimal -lnuma -lpthread

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

# Build Rabbit Order
echo "Building Rabbit Order with vcpkg boost and local dependencies..."
make clean

echo "=== Compilation attempt ==="
if make 2>&1; then
    if [[ -x "./reorder" ]]; then
        echo "=== SUCCESS: Rabbit Order built successfully ==="
        echo "Binary location: $RO_DIR/demo/reorder"
        
        # Test the binary
        echo "Testing Rabbit Order binary..."
        echo -e "0 1\n1 2\n2 0" > test_graph.txt
        if timeout 10 ./reorder test_graph.txt > test_output.txt 2>&1; then
            echo "Rabbit Order binary test passed"
            echo "Test output:"
            cat test_output.txt | head -5
            rm -f test_graph.txt test_output.txt
        else
            echo "WARNING: Rabbit Order binary test failed or timed out"
            echo "Test output:"
            cat test_output.txt 2>/dev/null || echo "No output file"
            rm -f test_graph.txt test_output.txt
        fi
        
        echo "=== Build Summary ==="
        echo "Completed at: $(date)"
        echo "Dependencies used:"
        echo "  - vcpkg boost: $BOOST_INCLUDE"
        echo "  - Local deps: $INSTALL_PREFIX"
        echo "Rabbit Order binary: $RO_DIR/demo/reorder"
        echo "Log file: $LOG_FILE"
        
        echo ""
        echo "Environment variables for runtime:"
        echo "  export LD_LIBRARY_PATH=\"$INSTALL_PREFIX/lib:\$LD_LIBRARY_PATH\""
        echo "  export PKG_CONFIG_PATH=\"$INSTALL_PREFIX/lib/pkgconfig:\$PKG_CONFIG_PATH\""
        
        exit 0
    else
        echo "Build completed but binary not found"
        exit 1
    fi
else
    echo "=== BUILD FAILED ==="
    echo "Compilation failed. Check the output above for details."
    exit 1
fi