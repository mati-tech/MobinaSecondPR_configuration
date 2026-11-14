"""Tests for the local test repository reader."""

import tempfile
import unittest
from pathlib import Path

from src.errors import RepositoryError
from src.local_repo import parse_test_graph
from tests.helpers import fixture


def _parse_text(text):
    """Parse a test graph stored in a temporary file."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "graph.txt"
        path.write_text(text, encoding="utf-8")
        return parse_test_graph(str(path))


class LocalRepositoryTests(unittest.TestCase):
    """Verify parsing of 'PACKAGE: DEP, DEP' rows."""

    def test_fixture(self):
        """Read the acyclic fixture."""
        self.assertEqual(
            parse_test_graph(fixture("acyclic.txt")),
            {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []},
        )

    def test_comments_and_blank_lines(self):
        """Ignore empty lines and # comments."""
        self.assertEqual(_parse_text("# note\n\nA: B\nB:\n"),
                         {"A": ["B"], "B": []})

    def test_repeated_dependency(self):
        """Keep one copy of a repeated dependency."""
        self.assertEqual(_parse_text("A: B, B\n"), {"A": ["B"]})

    def test_rejects_bad_rows(self):
        """Reject malformed rows, names and duplicates."""
        for text in ("A -> B\n", "a: B\n", "A: b\n", "A:\nA:\n", ": B\n"):
            with self.subTest(text=text):
                with self.assertRaises(RepositoryError):
                    _parse_text(text)

    def test_missing_file(self):
        """Reject a file that cannot be read."""
        with self.assertRaises(RepositoryError):
            parse_test_graph("no-such-file.txt")


if __name__ == "__main__":
    unittest.main()
