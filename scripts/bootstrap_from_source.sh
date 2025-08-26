#!/usr/bin/env bash
# Build Rabbit Order and dependencies entirely from source tarballs (no sudo access required)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
DEPS="$BUILD/deps"
LOG_FILE="$BUILD/bootstrap.log"

# Create directories
mkdir -p "$BUILD" "$DEPS"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Building Rabbit Order dependencies from source ==="
echo "Started at: $(date)"
echo "Build directory: $BUILD"
echo "Dependencies directory: $DEPS"

# Dependency versions (minimum required versions that work)
BOOST_VERSION="1.73.0"
BOOST_UNDERSCORED="$(echo "$BOOST_VERSION" | tr '.' '_')"
NUMA_VERSION="2.0.14"
GPERFTOOLS_VERSION="2.10"

# URLs for source tarballs - multiple mirrors for reliability
BOOST_URLS=(
    "https://sourceforge.net/projects/boost/files/boost/${BOOST_VERSION}/boost_${BOOST_UNDERSCORED}.tar.gz/download"
    "https://archive.org/download/boost_${BOOST_UNDERSCORED}/boost_${BOOST_UNDERSCORED}.tar.gz"
)
NUMA_URL="https://github.com/numactl/numactl/releases/download/v${NUMA_VERSION}/numactl-${NUMA_VERSION}.tar.gz"
GPERFTOOLS_URL="https://github.com/gperftools/gperftools/releases/download/gperftools-${GPERFTOOLS_VERSION}/gperftools-${GPERFTOOLS_VERSION}.tar.gz"

# Build configuration
INSTALL_PREFIX="$DEPS"
export PREFIX="$INSTALL_PREFIX"
export PKG_CONFIG_PATH="$INSTALL_PREFIX/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="$INSTALL_PREFIX/lib:${LD_LIBRARY_PATH:-}"

# Function to download with multiple URLs
download_with_fallback() {
    local urls=("$@")
    local name="${urls[-2]}"
    local target_file="${urls[-1]}"
    unset 'urls[-1]' 'urls[-1]'  # Remove last two elements
    
    for url in "${urls[@]}"; do
        echo "Trying to download from: $url"
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
    local url_or_urls="$1"
    local name="$2"
    local dir="$3"
    
    echo "=== Building $name ==="
    cd "$BUILD"
    
    local tarball
    if [[ "$url_or_urls" == *" "* ]]; then
        # Multiple URLs provided
        tarball="$(basename "${url_or_urls%% *}" | sed 's|/download$||')"
        if [[ ! -f "$tarball" ]]; then
            echo "Downloading $name (multiple sources available)"
            IFS=' ' read -ra urls <<< "$url_or_urls"
            download_with_fallback "${urls[@]}" "$name" "$tarball" || return 1
        fi
    else
        # Single URL provided
        tarball="$(basename "$url_or_urls" | sed 's|/download$||')"
        if [[ ! -f "$tarball" ]]; then
            echo "Downloading $name from $url_or_urls"
            curl -L -f -o "$tarball" "$url_or_urls" || {
                echo "ERROR: Failed to download $url_or_urls"
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

# Function to check if library is already built
lib_exists() {
    local lib_name="$1"
    [[ -f "$INSTALL_PREFIX/lib/lib${lib_name}.a" ]] || [[ -f "$INSTALL_PREFIX/lib/lib${lib_name}.so" ]]
}

# Build Boost (headers-only, no need to compile libraries for our use case)
build_boost() {
    if [[ -d "$INSTALL_PREFIX/include/boost" ]]; then
        echo "Boost headers already installed"
        return 0
    fi
    
    local boost_urls_str="${BOOST_URLS[*]}"
    download_and_extract "$boost_urls_str" "Boost ${BOOST_VERSION}" "boost_${BOOST_UNDERSCORED}" || return 1
    
    echo "Installing Boost headers..."
    # For the boost components used by Rabbit Order, we only need headers
    ./bootstrap.sh --prefix="$INSTALL_PREFIX" --with-libraries=headers
    ./b2 headers
    ./b2 install --prefix="$INSTALL_PREFIX" --with-headers
    
    echo "Boost headers installed successfully"
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
echo "=== Phase 1: Building dependencies ==="

build_boost || {
    echo "ERROR: Failed to build Boost"
    exit 1
}

build_numa || {
    echo "ERROR: Failed to build libnuma"
    exit 1
}

build_gperftools || {
    echo "ERROR: Failed to build gperftools"
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

# Create modified Makefile with local dependency paths
cat > Makefile << EOF
# Modified Makefile for local dependencies
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