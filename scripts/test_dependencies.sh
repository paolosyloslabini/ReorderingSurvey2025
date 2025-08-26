#!/usr/bin/env bash
# Test script to validate that locally built dependencies work correctly
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEPS="$ROOT/build/deps"

echo "=== Testing Locally Built Dependencies ==="

# Test libnuma
echo "Testing libnuma..."
cat > /tmp/test_numa.c << 'EOF'
#include <numa.h>
#include <stdio.h>

int main() {
    if (numa_available() == -1) {
        printf("NUMA not available, but library works\n");
    } else {
        printf("NUMA available, %d nodes\n", numa_max_node() + 1);
    }
    return 0;
}
EOF

if gcc -I"$DEPS/include" -L"$DEPS/lib" /tmp/test_numa.c -lnuma -o /tmp/test_numa; then
    echo "✓ libnuma compilation successful"
    if /tmp/test_numa; then
        echo "✓ libnuma runtime test passed"
    else
        echo "✗ libnuma runtime test failed"
        exit 1
    fi
else
    echo "✗ libnuma compilation failed"
    exit 1
fi

# Test tcmalloc
echo ""
echo "Testing tcmalloc..."
cat > /tmp/test_tcmalloc.c << 'EOF'
#include <gperftools/tcmalloc.h>
#include <stdio.h>
#include <stdlib.h>

int main() {
    void* ptr = tc_malloc(1024);
    if (ptr) {
        printf("tcmalloc allocation successful\n");
        tc_free(ptr);
        printf("tcmalloc free successful\n");
        return 0;
    } else {
        printf("tcmalloc allocation failed\n");
        return 1;
    }
}
EOF

if gcc -I"$DEPS/include" -L"$DEPS/lib" /tmp/test_tcmalloc.c -ltcmalloc_minimal -lstdc++ -lm -o /tmp/test_tcmalloc; then
    echo "✓ tcmalloc compilation successful"
    if /tmp/test_tcmalloc; then
        echo "✓ tcmalloc runtime test passed"
    else
        echo "✗ tcmalloc runtime test failed"  
        exit 1
    fi
else
    echo "✗ tcmalloc compilation failed"
    exit 1
fi

# Test boost (basic compilation)
echo ""
echo "Testing boost headers..."
cat > /tmp/test_boost.cpp << 'EOF'
#include <boost/atomic.hpp>
#include <boost/range/algorithm/count.hpp>
#include <boost/range/irange.hpp>
#include <iostream>
#include <vector>

int main() {
    // Test boost::atomic
    boost::atomic<int> atomic_int(42);
    std::cout << "boost::atomic value: " << atomic_int.load() << std::endl;
    
    // Test boost::range
    std::vector<int> vec = {1, 2, 3, 2, 4, 2};
    int count = boost::count(vec, 2);
    std::cout << "boost::count result: " << count << std::endl;
    
    // Test boost::irange
    auto range = boost::irange(1, 5);
    std::cout << "boost::irange size: " << range.size() << std::endl;
    
    return 0;
}
EOF

BOOST_INCLUDE="/usr/local/share/vcpkg/installed/x64-linux/include"
BOOST_LIB="/usr/local/share/vcpkg/installed/x64-linux/lib"

if [[ -d "$BOOST_INCLUDE" ]]; then
    if g++ -std=c++14 -I"$BOOST_INCLUDE" -L"$BOOST_LIB" /tmp/test_boost.cpp -lboost_atomic -o /tmp/test_boost; then
        echo "✓ boost compilation successful"
        if /tmp/test_boost; then
            echo "✓ boost runtime test passed"
        else
            echo "✗ boost runtime test failed"
            exit 1
        fi
    else
        echo "✗ boost compilation failed"
        exit 1
    fi
else
    echo "⚠ boost not available (vcpkg not installed)"
fi

# Cleanup
rm -f /tmp/test_numa /tmp/test_numa.c /tmp/test_tcmalloc /tmp/test_tcmalloc.c /tmp/test_boost /tmp/test_boost.cpp

echo ""
echo "=== All dependency tests passed! ==="
echo "Local build environment is working correctly."
echo ""
echo "Dependencies available:"
echo "  libnuma: $DEPS/lib/libnuma.a"
echo "  tcmalloc: $DEPS/lib/libtcmalloc_minimal.a" 
if [[ -d "$BOOST_INCLUDE" ]]; then
    echo "  boost: $BOOST_LIB/libboost_atomic.a"
fi
echo ""
echo "These dependencies can be used for building other projects that"
echo "don't have the specific compatibility issues of Rabbit Order."