#!/usr/bin/env bash
# Complete bootstrap script with boost building for Rabbit Order
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
DEPS="$BUILD/deps"
LOG_FILE="$BUILD/bootstrap_complete.log"

# Create directories
mkdir -p "$BUILD" "$DEPS"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Complete Rabbit Order Dependencies Bootstrap ==="
echo "Started at: $(date)"
echo "Build directory: $BUILD"
echo "Dependencies directory: $DEPS"

# Dependency versions
BOOST_VERSION="1.73.0"
BOOST_UNDERSCORED="$(echo "$BOOST_VERSION" | tr '.' '_')"
NUMA_VERSION="2.0.14"
GPERFTOOLS_VERSION="2.10"

# URLs for boost mirrors - using multiple sources for reliability
BOOST_URLS=(
    "https://archives.boost.io/release/${BOOST_VERSION}/source/boost_${BOOST_UNDERSCORED}.tar.gz"
    "https://boostorg.jfrog.io/artifactory/main/release/${BOOST_VERSION}/source/boost_${BOOST_UNDERSCORED}.tar.gz"
    "https://sourceforge.net/projects/boost/files/boost/${BOOST_VERSION}/boost_${BOOST_UNDERSCORED}.tar.gz/download"
)
NUMA_URL="https://github.com/numactl/numactl/releases/download/v${NUMA_VERSION}/numactl-${NUMA_VERSION}.tar.gz"
GPERFTOOLS_URL="https://github.com/gperftools/gperftools/releases/download/gperftools-${GPERFTOOLS_VERSION}/gperftools-${GPERFTOOLS_VERSION}.tar.gz"

# Build configuration
INSTALL_PREFIX="$DEPS"
export PREFIX="$INSTALL_PREFIX"
export PKG_CONFIG_PATH="$INSTALL_PREFIX/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="$INSTALL_PREFIX/lib:${LD_LIBRARY_PATH:-}"

# Function to try downloading from multiple URLs
download_with_fallback() {
    local name="$1"
    local target_file="$2"
    shift 2
    local urls=("$@")
    
    for url in "${urls[@]}"; do
        echo "Trying to download $name from: $url"
        if curl -L -f -o "$target_file" "$url"; then
            echo "Successfully downloaded $name"
            return 0
        else
            echo "Failed to download from $url, trying next..."
        fi
    done
    
    echo "ERROR: Failed to download $name from all sources"
    return 1
}

# Function to download and extract tarball
download_and_extract() {
    local name="$2"
    local dir="$3"
    shift 3
    local urls=("$@")
    
    echo "=== Building $name ==="
    cd "$BUILD"
    
    local tarball="boost_${BOOST_UNDERSCORED}.tar.gz"
    if [[ "$name" == *numa* ]]; then
        tarball="numactl-${NUMA_VERSION}.tar.gz"
    elif [[ "$name" == *gperf* ]]; then
        tarball="gperftools-${GPERFTOOLS_VERSION}.tar.gz"
    fi
    
    if [[ ! -f "$tarball" ]]; then
        echo "Downloading $name (${#urls[@]} sources available)"
        if [[ ${#urls[@]} -gt 1 ]]; then
            download_with_fallback "$name" "$tarball" "${urls[@]}" || return 1
        else
            curl -L -f -o "$tarball" "${urls[0]}" || {
                echo "ERROR: Failed to download ${urls[0]}"
                return 1
            }
        fi
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

# Build Boost with minimal required libraries
build_boost() {
    if [[ -d "$INSTALL_PREFIX/include/boost" ]] && lib_exists "boost_atomic"; then
        echo "Boost already built"
        return 0
    fi
    
    download_and_extract "" "Boost ${BOOST_VERSION}" "boost_${BOOST_UNDERSCORED}" "${BOOST_URLS[@]}" || return 1
    
    echo "Configuring Boost..."
    ./bootstrap.sh --prefix="$INSTALL_PREFIX" --with-libraries=atomic
    
    echo "Building Boost (this may take a while)..."
    # Build only what we need - atomic library and headers
    ./b2 --prefix="$INSTALL_PREFIX" --with-atomic link=static threading=multi variant=release -j$(nproc) install
    
    echo "Boost built successfully"
}

# Build libnuma
build_numa() {
    if lib_exists "numa"; then
        echo "libnuma already built"
        return 0
    fi
    
    download_and_extract "" "libnuma ${NUMA_VERSION}" "numactl-${NUMA_VERSION}" "$NUMA_URL" || return 1
    
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
    
    download_and_extract "" "gperftools ${GPERFTOOLS_VERSION}" "gperftools-${GPERFTOOLS_VERSION}" "$GPERFTOOLS_URL" || return 1
    
    echo "Building gperftools..."
    ./configure --prefix="$INSTALL_PREFIX" --enable-static --disable-shared --enable-minimal
    make -j$(nproc)
    make install
    
    echo "gperftools built successfully"
}

# Build dependencies
echo "=== Phase 1: Building dependencies ==="

# Build numa and gperftools first (faster)
build_numa || {
    echo "ERROR: Failed to build libnuma"
    exit 1
}

build_gperftools || {
    echo "ERROR: Failed to build gperftools"
    exit 1
}

# Build boost last (slowest)
build_boost || {
    echo "ERROR: Failed to build Boost"
    exit 1
}

echo "=== Phase 2: Building Rabbit Order ==="

# Clone Rabbit Order if not exists
RO_DIR="$BUILD/rabbit_order"
if [[ ! -d "$RO_DIR" ]]; then
    git clone --depth 1 https://github.com/araij/rabbit_order.git "$RO_DIR"
    git -C "$RO_DIR" checkout f67a79e427e2a06e72f6b528fd5464dfe8a43174
fi

# Modify Rabbit Order Makefile to use our local dependencies
cd "$RO_DIR/demo"
cp Makefile Makefile.orig

# Create modified Makefile with all local dependency paths
cat > Makefile << EOF
# Modified Makefile for complete local dependencies
DEPS_PREFIX = $INSTALL_PREFIX
CXXFLAGS += -Wall -Wextra -Wcast-align -Wcast-qual -Wconversion -Wfloat-equal \\
            -Wformat=2 -Winit-self -Wmissing-declarations \\
            -Wmissing-include-dirs -Wpointer-arith -Wredundant-decls \\
            -Wswitch-default -Wuninitialized -Wwrite-strings \\
            -Wno-sign-conversion -Wno-unused-function \\
            -Wno-missing-declarations \\
            -fopenmp -std=c++14 -mcx16 -O3 -DNDEBUG \\
            -I\$(DEPS_PREFIX)/include
LDFLAGS  += -L\$(DEPS_PREFIX)/lib
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
echo "Building Rabbit Order with local dependencies..."
make clean
make

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
else
    echo "ERROR: Rabbit Order binary not created"
    exit 1
fi

echo "=== Build Summary ==="
echo "Completed at: $(date)"
echo "Dependencies installed in: $INSTALL_PREFIX"
echo "Rabbit Order binary: $RO_DIR/demo/reorder"
echo "Log file: $LOG_FILE"

echo ""
echo "To use Rabbit Order, ensure the following environment variables are set:"
echo "  export LD_LIBRARY_PATH=\"$INSTALL_PREFIX/lib:\$LD_LIBRARY_PATH\""
echo "  export PKG_CONFIG_PATH=\"$INSTALL_PREFIX/lib/pkgconfig:\$PKG_CONFIG_PATH\""

echo ""
echo "Dependency sizes:"
du -sh "$INSTALL_PREFIX/lib"/* | sort -h