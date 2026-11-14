"""Tests for CLI configuration."""

import unittest

from src.config import parse_config
from src.errors import ConfigurationError


class ConfigTests(unittest.TestCase):
    """Verify CLI configuration validation."""

    def test_test_mode_config(self):
        """Accept a valid local test configuration."""
        config = parse_config([
            "--package", "A", "--test-mode",
            "--test-file", "tests/fixtures/acyclic.txt",
        ])
        self.assertTrue(config.test_mode)
        self.assertEqual(config.max_depth, 3)

    def test_requires_repository_in_maven_mode(self):
        """Reject Maven mode without a repository URL."""
        with self.assertRaises(ConfigurationError):
            parse_config(["--package", "g:a:1"])

    def test_rejects_negative_depth(self):
        """Reject negative traversal depth."""
        with self.assertRaises(ConfigurationError):
            parse_config([
                "--package", "A", "--test-mode",
                "--test-file", "tests/fixtures/acyclic.txt",
                "--max-depth", "-1",
            ])


if __name__ == "__main__":
    unittest.main()
