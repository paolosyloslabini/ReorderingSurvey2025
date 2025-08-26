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
python tests/run_all.py

# Run specific category
python tests/run_all.py unit
python tests/run_all.py integration  
python tests/run_all.py e2e

# Fast mode (stop on first failure)
python tests/run_all.py --fast

# Verbose output
python tests/run_all.py --verbose
```

### Individual Test Runners
```bash
# Run only unit tests
python tests/run_unit.py

# Run only integration tests
python tests/run_integration.py

# Run only end-to-end tests
python tests/run_e2e.py

# Traditional pytest (any category)
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v
```

### End-to-End Validation
```bash
# Complete pipeline validation
python tests/run_all.py validation

# This runs the full validation scenario:
# 1. Creates test matrix
# 2. Runs reordering (identity technique)
# 3. Runs multiplication (mock kernel)
# 4. Validates complete CSV output
```

## 📊 Expected Results

### All Tests Passing
When everything is working correctly, you should see:
```
ReorderingSurvey2025 Test Suite
===============================================================================
bash         ✅ PASSED  (2.1s)
unit         ✅ PASSED  (8.4s)
integration  ✅ PASSED  (12.2s)
e2e          ✅ PASSED  (25.7s)
validation   ✅ PASSED  (3.8s)
-------------------------------------------------------------------------------
Total time: 52.2s
🎉 All tests passed!
```

### Test Coverage
The current test suite covers:
- ✅ **21+ individual test cases** across all categories
- ✅ **Module loading system** (basic, python_scipy, cuda_cusparse)
- ✅ **Reordering techniques** (identity, RCM)
- ✅ **Multiplication kernels** (mock, cuSPARSE)
- ✅ **Complete pipelines** (reorder → multiply)
- ✅ **Error handling** and edge cases
- ✅ **Output validation** (CSV schema, file formats)
- ✅ **Real-world scenarios** (batch processing, parameter sweeps)

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

2. **CUDA-related warnings**
   - Normal in environments without GPU
   - Tests should still pass (fall back to CPU)

3. **Timing-related test failures**
   - Mock kernel timing might vary slightly
   - Tests have reasonable tolerances built in

4. **Permission errors**
   - Ensure script files are executable: `chmod +x tests/run_*.py`

### Getting Help

1. **Run tests with verbose output**: `python tests/run_all.py --verbose`
2. **Run specific failing test**: `python -m pytest tests/unit/test_specific.py::test_function -v`
3. **Check end-to-end validation**: `python tests/run_all.py validation`

## 📈 Continuous Integration

The test suite is designed for CI/CD environments:

- **Fast feedback**: Unit tests complete in ~8 seconds
- **Comprehensive coverage**: Integration and E2E tests ensure real-world functionality
- **Clear reporting**: Structured output with timing and status
- **Fail-fast option**: `--fast` mode for quick development feedback
- **Environment independence**: Works with or without GPU/CUDA

### CI Configuration Example
```yaml
- name: Run Test Suite
  run: |
    pip install -r requirements.txt
    python tests/run_all.py --fast
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