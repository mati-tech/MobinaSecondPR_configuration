"""Tests for ASCII tree output."""

import unittest

from src.errors import GraphError
from src.tree import ascii_tree

DATA = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}


class TreeTests(unittest.TestCase):
    """Check the exact tree layout."""

    def test_diamond(self):
        """Print a shared leaf under each parent."""
        expected = "\n".join([
            "A",
            "|-- B",
            "|   `-- D",
            "`-- C",
            "    `-- D",
        ])
        self.assertEqual(ascii_tree(DATA, "A"), expected)

    def test_repeated_subtree_is_marked(self):
        """Do not print the dependencies of a node twice."""
        data = {"A": ["B", "C"], "B": ["D"], "C": ["B"], "D": []}
        self.assertIn("`-- B (*)", ascii_tree(data, "A").splitlines()[-1])

    def test_cycle_is_marked(self):
        """Stop at a node that is already on the current path."""
        data = {"A": ["B"], "B": ["A"]}
        self.assertEqual(ascii_tree(data, "A"),
                         "A\n`-- B\n    `-- A (cycle)")

    def test_output_is_ascii(self):
        """Use only ASCII characters."""
        self.assertTrue(ascii_tree(DATA, "A").isascii())

    def test_unknown_root(self):
        """Reject a root that is absent from the graph."""
        with self.assertRaises(GraphError):
            ascii_tree(DATA, "Z")


if __name__ == "__main__":
    unittest.main()
