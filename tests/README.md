# Testing Guide for ReorderingSurvey2025

This directory contains a comprehensive, well-organized test suite for the ReorderingSurvey2025 sparse matrix reordering framework.

## 🏗️ Test Structure

The test suite is organized into clear categories for maintainability and ease of development:

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for component interactions
├── e2e/              # End-to-end tests for complete workflows
├── utils/            # Shared test utilities and fixtures
├── run_all.py        # Master test runner
├── run_unit.py       # Unit test runner
├── run_integration.py # Integration test runner
├── run_e2e.py        # End-to-end test runner
└── README.md         # This file
```

### Test Categories

#### 🧪 Unit Tests (`tests/unit/`)
Test individual components in isolation:
- **`test_reordering_techniques.py`** - Individual reordering algorithms (identity, RCM, etc.)
- **`test_multiplication_kernels.py`** - Individual multiplication kernels (mock, cuSPARSE, etc.)
- **`test_module_loading.py`** - Module loading system components

#### 🔗 Integration Tests (`tests/integration/`)
Test component interactions:
- **`test_reordering_integration.py`** - Reordering with module loading system
- **`test_multiplication_integration.py`** - Multiplication with module loading system

#### 🌐 End-to-End Tests (`tests/e2e/`)
Test complete workflows simulating real usage:
- **`test_complete_workflows.py`** - Full research workflows, parameter sweeps, batch processing

#### 🛠️ Test Utilities (`tests/utils/`)
Shared utilities and fixtures:
- **`fixtures.py`** - Common test fixtures, helper functions, and test data

## 🚀 Running Tests

### Quick Start
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific category
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v

# Fast mode (stop on first failure)
python -m pytest tests/ -x -v

# Verbose output with full details
python -m pytest tests/ -vv

# Run specific test file
python -m pytest tests/test_amd.py -v
python -m pytest tests/unit/test_reordering_techniques.py -v

# Run specific test function
python -m pytest tests/unit/test_reordering_techniques.py::TestIdentityReordering::test_identity_basic_4x4 -v
```

### Legacy Test Runners (Deprecated)
The repository includes legacy test runner scripts that are no longer the recommended way to run tests:
```bash
# These still work but use pytest directly instead
python tests/run_all.py       # Deprecated - use: python -m pytest tests/ -v
python tests/run_unit.py      # Deprecated - use: python -m pytest tests/unit/ -v
python tests/run_integration.py  # Deprecated - use: python -m pytest tests/integration/ -v
python tests/run_e2e.py       # Deprecated - use: python -m pytest tests/e2e/ -v
```

## 📊 Expected Results

### All Tests Passing
When all dependencies are installed and the environment is fully configured, you should see:
```
============================================ test session starts ============================================
collected 79 items

tests/e2e/test_complete_workflows.py ........                                                        [ 10%]
tests/integration/test_multiplication_integration.py ..........                                      [ 23%]
tests/integration/test_reordering_integration.py ..........                                          [ 36%]
tests/test_amd.py ....                                                                               [ 41%]
tests/test_unified_cusparse.py ......                                                                [ 48%]
tests/unit/test_block_density.py ......                                                              [ 56%]
tests/unit/test_module_loading.py ............                                                       [ 71%]
tests/unit/test_multiplication_kernels.py .............                                              [ 88%]
tests/unit/test_reordering_techniques.py .........                                                   [100%]

============================================ 79 passed in 75.00s ============================================
```

### Current Test Status (Typical Environment)
In most development environments without all system dependencies:
```
66 passed, 13 failed in 75.00s

Expected failures:
- 3 AMD tests (missing libsuitesparse-dev)
- 1 Rabbit Order test (missing built binary)
- 8 E2E tests (test design issue - depend on external matrices)
- 1 GPU pipeline test (requires CUDA)
```

### Test Coverage
The current test suite covers:
- ✅ **79 total tests** across all categories
- ✅ **44 unit tests** - Individual component testing (~30s)
- ✅ **21 integration tests** - Component interaction testing (~25s)
- ✅ **8 end-to-end tests** - Complete workflow simulation (~15s)
- ✅ **6 cuSPARSE-specific tests** - GPU kernel validation
- ✅ **Module loading system** (basic, python_scipy, cuda_cusparse, python_graphblas)
- ✅ **Reordering techniques** (identity, RCM, RCM-GraphBLAS, AMD)
- ✅ **Multiplication kernels** (mock, cuSPARSE variants, SMaT)
- ✅ **Complete pipelines** (reorder → multiply)
- ✅ **Error handling** and edge cases
- ✅ **Output validation** (CSV schema, file formats)
- ✅ **Block density metrics**

## 🧩 Adding New Tests

### For New Reordering Techniques

1. **Add unit test** in `tests/unit/test_reordering_techniques.py`:
```python
class TestNewTechnique:
    def test_new_technique_basic(self, tmp_path):
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "new_technique", test_env["env"])
        assert result.returncode == 0
        
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "new_technique")
        assert_valid_permutation(output_data["permutation"], 5)
        assert_valid_csv_data(output_data["csv_data"], "new_technique", "matrix")
```

2. **Add integration test** in `tests/integration/test_reordering_integration.py`:
```python
def test_new_technique_with_modules(self, tmp_path):
    # Test with appropriate module loading
    pass
```

3. **Add to end-to-end workflows** if appropriate.

### For New Multiplication Kernels

1. **Add unit test** in `tests/unit/test_multiplication_kernels.py`:
```python
class TestNewKernel:
    def test_new_kernel_basic(self, tmp_path):
        test_env = setup_test_environment(tmp_path)
        outdir = test_env["tmp_path"] / "output"
        outdir.mkdir()
        
        # Create reordered matrix
        reordered_mtx = outdir / "reordered.mtx"
        reordered_mtx.write_text("...matrix content...")
        
        wrapper_path = Path("Programs/Multiplication/Techniques/operation_new_kernel.sh")
        result = subprocess.run(["bash", str(wrapper_path), str(outdir)], ...)
        
        assert result.returncode == 0
        assert "TIMING_MS:" in result.stdout
```

2. **Add integration test** for complete pipeline.

### Best Practices

- **Use shared fixtures** from `tests/utils/fixtures.py`
- **Follow naming conventions**: `test_<component>_<scenario>`
- **Test both success and failure cases**
- **Validate output formats** (CSV schema, file contents)
- **Test with different matrix sizes** and types
- **Include parameter variations** where applicable
- **Add appropriate docstrings** explaining what is being tested

## 🔧 Test Utilities

### Available Fixtures
```python
from tests.utils.fixtures import (
    create_test_matrix,           # Create test matrix files
    setup_test_environment,       # Set up test environment
    run_reordering_test,         # Run reordering with proper env
    run_multiplication_test,     # Run multiplication with proper env
    validate_reordering_output,   # Validate reordering results
    validate_multiplication_output, # Validate multiplication results
    assert_valid_permutation,     # Assert permutation is valid
    assert_valid_csv_data,       # Assert CSV data is correct
    get_test_matrices           # Get predefined test matrices
)
```

### Test Matrices
Pre-defined test matrices for different scenarios:
- `identity_4x4` - Simple diagonal matrix
- `connected_5x5` - Connected graph matrix
- `structured_6x6` - Structured matrix that benefits from reordering
- `disconnected_4x4` - Disconnected components

### Environment Setup
Tests automatically handle:
- Temporary directories and cleanup
- Environment variable setup (`RESULTS_DIR`, `PROJECT_ROOT`)
- Module loading system
- Output validation

## 🐛 Troubleshooting

### Common Issues

1. **Tests fail with "Module not found"**
   - Ensure you're running from the project root
   - Install dependencies: `pip install -r requirements.txt`

2. **AMD tests fail with "libamd.so not found"**
   - Expected in environments without SuiteSparse
   - Install: `sudo apt-get install libsuitesparse-dev` (Ubuntu/Debian)
   - Or use HPC module system if available
   - Tests: 3 AMD tests will fail without this library

3. **Rabbit Order test fails**
   - Expected - requires building external binary
   - Run: `./scripts/bootstrap_ro.sh` to build Rabbit Order
   - Requires: g++ ≥4.9.2, Boost ≥1.58.0, libnuma ≥2.0.9, tcmalloc
   - See `Programs/Reordering/Techniques/README.md` for details

4. **E2E tests fail with "FileNotFoundError: Raw_Matrices/benchmark/"**
   - Known issue - E2E tests currently depend on external test matrices
   - Status: Test design issue (tests should create matrices internally)
   - Impact: 8 E2E workflow tests fail
   - Workaround: Not needed - core functionality tested by unit/integration tests

5. **CUDA-related warnings or GPU test failures**
   - Normal in environments without GPU
   - Most tests gracefully fall back to CPU
   - 1 integration test requires GPU (test_complete_pipeline_rcm_cusparse)

6. **Timing-related test variations**
   - Mock kernel timing might vary slightly between runs
   - Tests have reasonable tolerances built in
   - If tests fail due to timing, it's usually a real issue

7. **Permission errors**
   - Ensure script files are executable: `chmod +x Programs/**/*.sh`
   - Check write permissions in test output directories

### Getting Help

1. **Run tests with verbose output**: `python -m pytest tests/ -vv`
2. **Run specific failing test**: `python -m pytest tests/unit/test_specific.py::test_function -v`
3. **Check test logs**: Look at captured stdout/stderr in pytest output
4. **Validate environment**: 
   ```bash
   python -c "import numpy, pandas, scipy, graphblas, pymetis; print('All imports OK')"
   ```

### Test Failure Summary

| Failure Type | Count | Severity | Action |
|-------------|-------|----------|--------|
| AMD library missing | 3 | Low | Install libsuitesparse-dev (optional) |
| Rabbit Order not built | 1 | Low | Run bootstrap script (optional) |
| E2E matrix dependency | 8 | Medium | Tests need refactoring (not user issue) |
| GPU unavailable | 1 | Low | Expected without CUDA (optional) |

**Total expected failures in typical environment: 13 out of 79 tests**

## 📈 Continuous Integration

The test suite is designed for CI/CD environments:

- **Fast feedback**: Unit tests complete in ~30 seconds
- **Comprehensive coverage**: 79 tests covering all framework components
- **Clear reporting**: Structured pytest output with timing and status
- **Fail-fast option**: Use `-x` flag for quick development feedback
- **Environment independence**: Works with or without GPU/CUDA
- **Graceful degradation**: Tests skip or pass when optional dependencies missing

### CI Configuration Example
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/ -v --tb=short
      - name: Run tests (fail fast)
        run: |
          python -m pytest tests/ -x -v
```

### Expected CI Behavior
- **Minimum passing**: 66/79 tests (without AMD library, Rabbit Order, or GPU)
- **With SuiteSparse**: 69/79 tests (AMD tests pass)
- **Full environment**: All 79 tests can pass with all dependencies

### Recommended CI Strategy
```bash
# For PR validation - fast feedback
python -m pytest tests/unit/ tests/integration/ -v --tb=short

# For main branch - comprehensive validation  
python -m pytest tests/ -v

# For releases - full validation with coverage
python -m pytest tests/ -v --cov=. --cov-report=html
```

## 🎯 Test Philosophy

This test suite follows these principles:

1. **Clear Organization** - Tests are categorized by scope and purpose
2. **Realistic Scenarios** - E2E tests simulate actual research workflows
3. **Maintainable Code** - Shared utilities reduce duplication
4. **Fast Feedback** - Unit tests provide quick development feedback
5. **Comprehensive Coverage** - Integration tests ensure components work together
6. **Documentation** - Clear instructions for running and extending tests

The goal is to make testing easy for contributors while ensuring the framework remains reliable and robust for research use.