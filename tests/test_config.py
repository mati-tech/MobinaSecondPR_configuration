"""Tests for CLI configuration."""

import tempfile
import unittest
from pathlib import Path

from src.config import is_package_letters, parse_config, split_package
from src.errors import ConfigurationError
from tests.helpers import MAVEN_REPO_URL, fixture


def _test_args(*extra):
    """Build arguments for a valid test-mode run."""
    return ["--package", "A", "--test-mode",
            "--repository", fixture("acyclic.txt"), *extra]


def _maven_args(*extra):
    """Build arguments for a valid Maven-mode run."""
    return ["--package", "com.example:app", "--version", "1.0",
            "--repository", MAVEN_REPO_URL, *extra]


class ValidConfigTests(unittest.TestCase):
    """Accept valid combinations of options."""

    def test_test_mode_defaults(self):
        """Fill defaults in test mode."""
        config = parse_config(_test_args())
        self.assertTrue(config.test_mode)
        self.assertEqual(config.max_depth, 3)
        self.assertEqual(config.version, "")

    def test_maven_mode_with_version_option(self):
        """Read the version from --version."""
        config = parse_config(_maven_args("--filter", "log"))
        self.assertEqual(config.package, "com.example:app")
        self.assertEqual(config.version, "1.0")
        self.assertEqual(config.filter_substring, "log")

    def test_version_inside_package(self):
        """Accept group:artifact:version in --package."""
        config = parse_config([
            "--package", "g:a:2.5", "--repository", MAVEN_REPO_URL])
        self.assertEqual((config.package, config.version), ("g:a", "2.5"))

    def test_split_package(self):
        """Split coordinates into name and version."""
        self.assertEqual(split_package("g:a"), ("g:a", ""))
        self.assertEqual(split_package("g:a:1"), ("g:a", "1"))

    def test_package_letters(self):
        """Recognize capital Latin names only."""
        self.assertTrue(is_package_letters("AB"))
        self.assertFalse(is_package_letters("Ab"))
        self.assertFalse(is_package_letters("A1"))


class InvalidConfigTests(unittest.TestCase):
    """Reject every kind of invalid option."""

    def assert_rejected(self, args):
        """Check that arguments raise a configuration error."""
        with self.assertRaises(ConfigurationError):
            parse_config(args)

    def test_missing_required_option(self):
        """Reject a missing --package."""
        self.assert_rejected(["--repository", "x"])

    def test_negative_depth(self):
        """Reject a negative depth."""
        self.assert_rejected(_test_args("--max-depth", "-1"))

    def test_depth_is_not_a_number(self):
        """Reject a non-numeric depth."""
        self.assert_rejected(_test_args("--max-depth", "many"))

    def test_missing_test_file(self):
        """Reject a test repository file that does not exist."""
        self.assert_rejected(["--package", "A", "--test-mode",
                              "--repository", "missing.txt"])

    def test_bad_test_package_name(self):
        """Reject test package names that are not capital letters."""
        self.assert_rejected(["--package", "a1", "--test-mode",
                              "--repository", fixture("acyclic.txt")])

    def test_bad_repository_url(self):
        """Reject a Maven repository that is not a URL."""
        self.assert_rejected(["--package", "g:a", "--version", "1",
                              "--repository", "some/folder"])

    def test_bad_package_format(self):
        """Reject a Maven package without a group."""
        self.assert_rejected(["--package", "lonely", "--version", "1",
                              "--repository", MAVEN_REPO_URL])

    def test_missing_version(self):
        """Reject a Maven package without any version."""
        self.assert_rejected(["--package", "g:a",
                              "--repository", MAVEN_REPO_URL])

    def test_conflicting_versions(self):
        """Reject different versions in --package and --version."""
        self.assert_rejected(["--package", "g:a:1", "--version", "2",
                              "--repository", MAVEN_REPO_URL])

    def test_image_extension(self):
        """Reject an image name that does not end with .png."""
        self.assert_rejected(_test_args("--image", "graph.jpg"))

    def test_d2_extension(self):
        """Reject a D2 file name that does not end with .d2."""
        self.assert_rejected(_test_args("--d2-file", "graph.txt"))

    def test_missing_output_directory(self):
        """Reject an output folder that does not exist."""
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "absent" / "graph.png"
            self.assert_rejected(_test_args("--image", str(target)))


if __name__ == "__main__":
    unittest.main()
