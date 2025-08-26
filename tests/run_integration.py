#!/usr/bin/env python3
"""
Integration test runner for ReorderingSurvey2025.

Runs only integration tests with detailed output.
"""
import subprocess
import sys
from pathlib import Path


def main():
    """Run integration tests."""
    project_root = Path(__file__).parent.parent
    
    print("Running Integration Tests")
    print("=" * 50)
    
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()