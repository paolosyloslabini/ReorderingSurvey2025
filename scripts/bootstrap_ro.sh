#!/usr/bin/env bash
# Build Rabbit Order, preferring cluster modules and falling back to
# source tarballs when modules are missing or incompatible.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
DEPS="$BUILD/deps"
RO_DIR="$BUILD/rabbit_order"

NUMA_VERSION="2.0.14"
GPERFTOOLS_VERSION="2.10"
BOOST_VERSION="1.58.0"
BOOST_UNDERSCORED="${BOOST_VERSION//./_}"

RO_REPO="https://github.com/araij/rabbit_order.git"
RO_COMMIT="f67a79e427e2a06e72f6b528fd5464dfe8a43174"

mkdir -p "$BUILD" "$DEPS"
export PREFIX="$DEPS"
export PKG_CONFIG_PATH="$DEPS/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="$DEPS/lib:${LD_LIBRARY_PATH:-}"

clone_ro() {
    if [[ ! -d "$RO_DIR" ]]; then
        git clone --depth 1 "$RO_REPO" "$RO_DIR"
        git -C "$RO_DIR" checkout "$RO_COMMIT"
    fi
}

# ---------------- Module-based build -----------------
build_with_modules() {
    echo "Attempting Rabbit Order build using loaded modules..."
    clone_ro
    if make -C "$RO_DIR/demo" clean && make -C "$RO_DIR/demo"; then
        echo "Rabbit Order built successfully using modules."
        echo "Binary: $RO_DIR/demo/reorder"
        return 0
    fi
    echo "Rabbit Order build with modules failed."
    return 1
}

# ---------------- Source builds ----------------------
download_and_extract() {
    local url="$1"; local name="$2"; local dir="$3"
    echo "=== Building $name ==="
    cd "$BUILD"
    local tarball="$(basename "$url")"
    if [[ ! -f "$tarball" ]]; then
        echo "Downloading $name from $url"
        curl -L -f -o "$tarball" "$url"
    fi
    if [[ ! -d "$dir" ]]; then
        echo "Extracting $tarball"
        tar -xzf "$tarball"
    fi
    cd "$dir"
}

lib_exists() {
    local lib="$1"
    [[ -f "$DEPS/lib/lib${lib}.a" ]] || [[ -f "$DEPS/lib/lib${lib}.so" ]]
}

build_numa() {
    if lib_exists "numa"; then
        echo "libnuma already built"
        return 0
    fi
    download_and_extract "https://github.com/numactl/numactl/releases/download/v${NUMA_VERSION}/numactl-${NUMA_VERSION}.tar.gz" \
        "libnuma ${NUMA_VERSION}" "numactl-${NUMA_VERSION}"
    ./configure --prefix="$DEPS" --enable-static --disable-shared
    make -j"$(nproc)"
    make install
}

build_gperftools() {
    if lib_exists "tcmalloc_minimal"; then
        echo "gperftools already built"
        return 0
    fi
    download_and_extract "https://github.com/gperftools/gperftools/releases/download/gperftools-${GPERFTOOLS_VERSION}/gperftools-${GPERFTOOLS_VERSION}.tar.gz" \
        "gperftools ${GPERFTOOLS_VERSION}" "gperftools-${GPERFTOOLS_VERSION}"
    ./configure --prefix="$DEPS" --enable-static --disable-shared --enable-minimal
    make -j"$(nproc)"
    make install
}

build_boost() {
    if [[ -d "$DEPS/include/boost" ]] && lib_exists "boost_atomic"; then
        echo "Boost already built"
        return 0
    fi
    download_and_extract "https://archives.boost.io/release/${BOOST_VERSION}/source/boost_${BOOST_UNDERSCORED}.tar.gz" \
        "Boost ${BOOST_VERSION}" "boost_${BOOST_UNDERSCORED}"
    ./bootstrap.sh --prefix="$DEPS" --with-libraries=atomic
    ./b2 -j"$(nproc)" install --prefix="$DEPS" --with-atomic link=static threading=multi
}

build_with_local() {
    echo "Building dependencies from source tarballs..."
    build_boost
    build_numa
    build_gperftools
    clone_ro
    local mf="$RO_DIR/demo/Makefile"
    cp "$mf" "$mf.orig"
    cat > "$mf" <<EOF_MAKE
# Auto-generated Makefile using locally built dependencies
DEPS_PREFIX = $DEPS
CXXFLAGS += -I\$(DEPS_PREFIX)/include -fopenmp -std=c++14 -mcx16 -O3 -DNDEBUG
LDFLAGS  += -L\$(DEPS_PREFIX)/lib
LDLIBS   += -ltcmalloc_minimal -lnuma -lboost_atomic
TARGETS   = reorder

\$(TARGETS): %: %.cc
	\$(LINK.cc) -MD -o \$@ \$< \$(LDLIBS)
	@cp \$*.d .\$*.P; \\
	  sed -e 's/#.*//' -e 's/^[^:]*: *//' -e 's/ *\\\\\$\$//' \\
	      -e '/^\$\$/ d' -e 's/\$\$/ :/' < \$*.d >> .\$*.P; \\
	  rm -f \$*.d

.PHONY: clean
clean:
	\$(RM) \$(TARGETS) \$(TARGETS:%=.%.P)

-include .*.P
EOF_MAKE
    make -C "$RO_DIR/demo" clean
    make -C "$RO_DIR/demo"
    echo "Rabbit Order built with local dependencies."
    echo "Binary: $RO_DIR/demo/reorder"
}

# ----------- Main logic -----------------------------
if command -v module >/dev/null 2>&1; then
    echo "Module system detected; trying modules first."
    module purge >/dev/null 2>&1 || true
    if module load numactl/$NUMA_VERSION gperftools/$GPERFTOOLS_VERSION boost/$BOOST_VERSION 2>/dev/null; then
        if build_with_modules; then
            exit 0
        fi
        echo "Falling back to source build due to module build failure." >&2
    else
        echo "Required modules not available." >&2
    fi
else
    echo "No module command found." >&2
fi

echo "Proceeding with source-based build."
build_with_local
