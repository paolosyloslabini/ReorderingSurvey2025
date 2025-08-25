#!/usr/bin/env python3
"""Tests for the enhanced bootstrap script."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestBootstrapScript(unittest.TestCase):
    """Test the bootstrap script functionality."""

    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
        self.bootstrap_script = self.project_root / "scripts" / "bootstrap.sh"
        self.build_dir = self.project_root / "build"

    def test_bootstrap_script_exists_and_executable(self):
        """Test that bootstrap script exists and is executable."""
        self.assertTrue(self.bootstrap_script.exists())
        self.assertTrue(os.access(self.bootstrap_script, os.X_OK))

    def test_bootstrap_script_syntax(self):
        """Test that bootstrap script has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(self.bootstrap_script)],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, 
                        f"Bash syntax check failed: {result.stderr}")

    def test_bootstrap_creates_build_directory(self):
        """Test that bootstrap script creates build directory."""
        # Remove build directory if it exists
        if self.build_dir.exists():
            import shutil
            shutil.rmtree(self.build_dir)
        
        # Run bootstrap script
        result = subprocess.run(
            [str(self.bootstrap_script)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        # Bootstrap should complete (with or without building external tools)
        self.assertEqual(result.returncode, 0,
                        f"Bootstrap script failed: {result.stderr}")
        
        # Build directory should be created
        self.assertTrue(self.build_dir.exists())
        
        # Log file should be created
        log_file = self.build_dir / "bootstrap.log"
        self.assertTrue(log_file.exists())

    def test_bootstrap_downloads_rabbit_order(self):
        """Test that bootstrap script downloads Rabbit Order."""
        # Run bootstrap script
        result = subprocess.run(
            [str(self.bootstrap_script)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        
        # Rabbit Order directory should exist
        rabbit_order_dir = self.build_dir / "rabbit_order"
        self.assertTrue(rabbit_order_dir.exists())
        
        # Check that specific files exist
        self.assertTrue((rabbit_order_dir / "rabbit_order.hpp").exists())
        self.assertTrue((rabbit_order_dir / "demo").exists())

    def test_bootstrap_handles_build_failure_gracefully(self):
        """Test that bootstrap script handles build failures gracefully."""
        result = subprocess.run(
            [str(self.bootstrap_script)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        # Script should complete even if builds fail
        self.assertEqual(result.returncode, 0)
        
        # Should contain expected messages about build failures being normal
        self.assertIn("expected in sandboxed environments", result.stdout)

    def test_bootstrap_log_file_format(self):
        """Test that bootstrap script creates properly formatted log files."""
        result = subprocess.run(
            [str(self.bootstrap_script)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        
        log_file = self.build_dir / "bootstrap.log"
        self.assertTrue(log_file.exists())
        
        # Check log file has timestamps
        with open(log_file, 'r') as f:
            log_content = f.read()
            
        # Should contain timestamped entries
        self.assertIn("Starting bootstrap process", log_content)
        self.assertIn("System dependencies", log_content)
        
        # Should contain year in timestamp
        self.assertIn("2025", log_content)

    def test_bootstrap_provides_helpful_output(self):
        """Test that bootstrap script provides helpful output."""
        result = subprocess.run(
            [str(self.bootstrap_script)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        
        # Should provide summary
        self.assertIn("Summary:", result.stdout)
        self.assertIn("Next steps:", result.stdout)
        
        # Should mention key components
        self.assertIn("System dependencies", result.stdout)
        self.assertIn("Rabbit Order", result.stdout)
        self.assertIn("METIS", result.stdout)


if __name__ == "__main__":
    unittest.main()