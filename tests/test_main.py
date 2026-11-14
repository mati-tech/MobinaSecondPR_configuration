"""End-to-end tests of the command-line program."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from src.main import run
from tests.helpers import MAVEN_REPO_URL, fixture


def _run(*args):
    """Run the program in a temp folder; return code, stdout, stderr."""
    out, err = io.StringIO(), io.StringIO()
    with tempfile.TemporaryDirectory() as folder:
        image = str(Path(folder) / "graph.png")
        d2_file = str(Path(folder) / "graph.d2")
        full = [*args, "--image", image, "--d2-file", d2_file]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = run(full)
        created = Path(image).is_file() and Path(d2_file).is_file()
    return code, out.getvalue(), err.getvalue(), created


def _test_args(name, *extra):
    """Arguments for a test-mode run on a fixture graph."""
    return ["--package", "A", "--test-mode",
            "--repository", fixture(name), *extra]


class MainTests(unittest.TestCase):
    """Run whole scenarios through the public entry point."""

    def test_acyclic_report(self):
        """Print config, tree, order and create both output files."""
        code, out, _, created = _run(*_test_args(
            "acyclic.txt", "--ascii-tree", "--load-order"))
        self.assertEqual(code, 0)
        self.assertIn("max_depth=3", out)
        self.assertIn("D -> B -> C -> A", out)
        self.assertIn("`-- C", out)
        self.assertTrue(created)

    def test_cyclic_graph_warns(self):
        """Finish normally and mention the cycle."""
        code, out, _, _ = _run(*_test_args(
            "cyclic.txt", "--load-order", "--ascii-tree"))
        self.assertEqual(code, 0)
        self.assertIn("dependency cycle A -> B -> C -> A", out)
        self.assertIn("A (cycle)", out)

    def test_filter(self):
        """Drop filtered packages from the printed result."""
        code, out, _, _ = _run(*_test_args(
            "acyclic.txt", "--filter", "C", "--ascii-tree"))
        self.assertEqual(code, 0)
        tree = out.split("Dependency tree:")[1].split("\n\n")[0]
        self.assertNotIn("C", tree)

    def test_depth_limit(self):
        """Respect --max-depth."""
        _, out, _, _ = _run(*_test_args(
            "deep.txt", "--max-depth", "1", "--ascii-tree"))
        tree = out.split("Dependency tree:")[1].split("\n\n")[0]
        self.assertIn("B", tree)
        self.assertNotIn("D", tree)

    def test_maven_repository(self):
        """Resolve a package from a Maven-layout repository."""
        code, out, _, created = _run(
            "--package", "com.example:app", "--version", "1.0",
            "--repository", MAVEN_REPO_URL, "--max-depth", "4",
            "--load-order")
        self.assertEqual(code, 0)
        self.assertIn("com.example:core:2.0", out)
        self.assertIn("com.example:logging:1.4", out)
        self.assertTrue(created)

    def test_missing_transitive_pom_is_a_warning(self):
        """Continue when a transitive POM is not in the repository."""
        code, _, err, _ = _run(
            "--package", "com.example:broken-app", "--version", "1.0",
            "--repository", MAVEN_REPO_URL)
        self.assertEqual(code, 0)
        self.assertIn("missing", err)

    def test_missing_root_pom_is_an_error(self):
        """Fail when the analyzed package itself cannot be found."""
        code, _, err, _ = _run(
            "--package", "com.example:nothing", "--version", "9",
            "--repository", MAVEN_REPO_URL)
        self.assertEqual(code, 2)
        self.assertIn("Error:", err)

    def test_absent_root_in_test_file(self):
        """Fail when the root is not described in the test file."""
        code, _, err, _ = _run("--package", "Z", "--test-mode",
                               "--repository", fixture("acyclic.txt"))
        self.assertEqual(code, 2)
        self.assertIn("absent", err)

    def test_invalid_option_is_reported(self):
        """Show a readable error and a non-zero exit code."""
        code, _, err, created = _run(*_test_args(
            "acyclic.txt", "--max-depth", "-5"))
        self.assertEqual(code, 2)
        self.assertIn("--max-depth", err)
        self.assertFalse(created)

    def test_root_filtered_out(self):
        """Fail when the filter removes the analyzed package."""
        code, _, err, _ = _run(*_test_args("acyclic.txt", "--filter", "A"))
        self.assertEqual(code, 2)
        self.assertIn("filter", err)


if __name__ == "__main__":
    unittest.main()
