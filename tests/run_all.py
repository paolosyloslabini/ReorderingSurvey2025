#!/usr/bin/env python3
"""
Master test runner for the ReorderingSurvey2025 test suite.

This script provides comprehensive test execution with clear reporting
and is the primary entry point for running tests.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path


def run_test_category(category: str, verbose: bool = False, fast: bool = False) -> tuple[int, float]:
    """
    Run tests for a specific category.
    
    Args:
        category: Test category (unit, integration, e2e, or all)
        verbose: Whether to show verbose output
        fast: Whether to run in fast mode (skip slower tests)
    
    Returns:
        Tuple of (exit_code, execution_time)
    """
    project_root = Path(__file__).parent.parent
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    if category == "all":
        cmd.append("tests/")
    else:
        cmd.append(f"tests/{category}/")
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.extend(["-q", "--tb=short"])
    
    if fast:
        cmd.extend(["-x", "--disable-warnings"])  # Stop on first failure, reduce output
    
    # Add coverage if requested
    if not fast:
        cmd.extend(["--tb=short"])
    
    print(f"Running {category} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=not verbose,
            text=True
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if not verbose and result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
        
        return result.returncode, execution_time
        
    except Exception as e:
        print(f"Error running {category} tests: {e}", file=sys.stderr)
        return 1, time.time() - start_time


def run_bash_tests(verbose: bool = False) -> tuple[int, float]:
    """
    Run bash-based tests.
    
    Args:
        verbose: Whether to show verbose output
    
    Returns:
        Tuple of (exit_code, execution_time)
    """
    project_root = Path(__file__).parent.parent
    
    print("Running bash tests...")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["bash", "tests/test_module_loading.sh"],
            cwd=project_root,
            capture_output=not verbose,
            text=True
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if not verbose and result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
        
        return result.returncode, execution_time
        
    except Exception as e:
        print(f"Error running bash tests: {e}", file=sys.stderr)
        return 1, time.time() - start_time


def run_end_to_end_validation() -> tuple[int, float]:
    """
    Run the complete end-to-end validation scenario.
    
    Returns:
        Tuple of (exit_code, execution_time)
    """
    project_root = Path(__file__).parent.parent
    
    print("Running end-to-end validation...")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Create test matrix
        test_script = f"""
cd {project_root}

# 1. Create test matrix
mkdir -p /tmp/e2e_validation/sample_data
cat > /tmp/e2e_validation/sample_data/test.mtx << 'EOF'
%%MatrixMarket matrix coordinate real general
4 4 4
1 1 1.0
2 2 2.0
3 3 3.0
4 4 4.0
EOF

# 2. Copy to proper location
mkdir -p Raw_Matrices/sample_data
cp /tmp/e2e_validation/sample_data/test.mtx Raw_Matrices/sample_data/

# 3. Run reordering
export RESULTS_DIR=/tmp/e2e_validation_results
bash Programs/Reorder.sbatch Raw_Matrices/sample_data/test.mtx identity

# 4. Verify reordering output
ls -la $RESULTS_DIR/Reordering/test/identity_default/
cat $RESULTS_DIR/Reordering/test/identity_default/results.csv

# 5. Run multiplication  
bash Programs/Multiply.sbatch $RESULTS_DIR/Reordering/test/identity_default/results.csv mock

# 6. Verify complete pipeline
cat $RESULTS_DIR/Multiplication/test/identity_default/mock/results.csv

echo "End-to-end validation completed successfully!"
"""
        
        result = subprocess.run(
            ["bash", "-c", test_script],
            capture_output=True,
            text=True
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
        
        return result.returncode, execution_time
        
    except Exception as e:
        print(f"Error running end-to-end validation: {e}", file=sys.stderr)
        return 1, time.time() - start_time


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="ReorderingSurvey2025 Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Categories:
  unit         Unit tests for individual components
  integration  Integration tests for component interactions  
  e2e          End-to-end tests for complete workflows
  bash         Bash-based module loading tests
  validation   Complete end-to-end validation scenario
  all          All pytest-based tests (unit + integration + e2e)
  
Examples:
  python tests/run_all.py unit                    # Run unit tests only
  python tests/run_all.py integration --verbose   # Run integration tests with verbose output
  python tests/run_all.py all --fast              # Run all tests quickly
  python tests/run_all.py validation              # Run end-to-end validation
  python tests/run_all.py                         # Run complete test suite
        """
    )
    
    parser.add_argument(
        "category",
        nargs="?",
        default="complete",
        choices=["unit", "integration", "e2e", "bash", "validation", "all", "complete"],
        help="Test category to run (default: complete)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose test output"
    )
    
    parser.add_argument(
        "-f", "--fast",
        action="store_true", 
        help="Run tests in fast mode (less verbose, stop on first failure)"
    )
    
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip end-to-end validation when running complete suite"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("ReorderingSurvey2025 Test Suite")
    print("=" * 80)
    
    total_start_time = time.time()
    total_exit_code = 0
    results = {}
    
    if args.category == "complete":
        # Run complete test suite
        categories_to_run = ["bash", "unit", "integration", "e2e"]
        if not args.no_validation:
            categories_to_run.append("validation")
        
        for category in categories_to_run:
            if category == "bash":
                exit_code, exec_time = run_bash_tests(args.verbose)
            elif category == "validation":
                exit_code, exec_time = run_end_to_end_validation()
            else:
                exit_code, exec_time = run_test_category(category, args.verbose, args.fast)
            
            results[category] = (exit_code, exec_time)
            
            if exit_code != 0:
                total_exit_code = exit_code
                if args.fast:
                    print(f"\\nFast mode: Stopping after {category} test failure")
                    break
            
            print()  # Add spacing between categories
    
    else:
        # Run specific category
        if args.category == "bash":
            exit_code, exec_time = run_bash_tests(args.verbose)
        elif args.category == "validation":
            exit_code, exec_time = run_end_to_end_validation()
        else:
            exit_code, exec_time = run_test_category(args.category, args.verbose, args.fast)
        
        results[args.category] = (exit_code, exec_time)
        total_exit_code = exit_code
    
    # Print summary
    total_time = time.time() - total_start_time
    
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for category, (exit_code, exec_time) in results.items():
        status = "✅ PASSED" if exit_code == 0 else "❌ FAILED"
        print(f"{category:<12} {status:<10} ({exec_time:.2f}s)")
    
    print("-" * 80)
    print(f"Total time: {total_time:.2f}s")
    
    if total_exit_code == 0:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")
        
    print("=" * 80)
    
    sys.exit(total_exit_code)


if __name__ == "__main__":
    main()