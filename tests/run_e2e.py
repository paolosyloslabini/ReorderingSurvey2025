#!/usr/bin/env python3
"""
End-to-end test runner for ReorderingSurvey2025.

Runs only end-to-end tests with detailed output.
"""
import subprocess
import sys
from pathlib import Path


def main():
    """Run end-to-end tests."""
    project_root = Path(__file__).parent.parent
    
    print("Running End-to-End Tests")
    print("=" * 50)
    
    cmd = [
        "python", "-m", "pytest",
        "tests/e2e/",
        "-v",
        "--tb=short",
        "-s"  # Don't capture output for e2e tests
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()