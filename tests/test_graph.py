"""Tests for graph traversal and ordering."""

import unittest

from src.errors import GraphError
from src.graph import ascii_tree, build_graph, filter_graph, topological_sort


class GraphTests(unittest.TestCase):
    """Exercise BFS, filtering, cycles, and topological ordering."""

    def setUp(self):
        """Prepare a reusable acyclic graph."""
        self.data = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": [],
        }

    def test_bfs_builds_graph(self):
        """Expand reachable nodes breadth-first without recursion."""
        graph = build_graph("A", self.data.get, 3)
        self.assertEqual(graph, self.data)

    def test_depth_limit(self):
        """Do not expand nodes at the configured maximum depth."""
        graph = build_graph("A", self.data.get, 1)
        self.assertEqual(graph, {"A": ["B", "C"], "B": [], "C": []})

    def test_filter(self):
        """Exclude matching package names and their edges."""
        graph = filter_graph(self.data, "C")
        self.assertNotIn("C", graph)
        self.assertEqual(graph["A"], ["B"])

    def test_cycle_does_not_loop(self):
        """BFS terminates when dependencies form a cycle."""
        data = {"A": ["B"], "B": ["C"], "C": ["A"]}
        graph = build_graph("A", data.get, 10)
        self.assertEqual(set(graph), {"A", "B", "C"})

    def test_topological_order(self):
        """Place dependencies before packages that require them."""
        order = topological_sort(self.data)
        self.assertLess(order.index("D"), order.index("B"))
        self.assertLess(order.index("B"), order.index("A"))

    def test_topological_cycle_error(self):
        """Reject a graph that cannot have a topological ordering."""
        with self.assertRaises(GraphError):
            topological_sort({"A": ["B"], "B": ["A"]})

    def test_ascii_tree(self):
        """Render root and child nodes."""
        output = ascii_tree(self.data, "A")
        self.assertIn("A", output)
        self.assertIn("B", output)
        self.assertIn("D", output)


if __name__ == "__main__":
    unittest.main()
