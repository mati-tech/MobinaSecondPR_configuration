"""Tests for BFS graph construction."""

import unittest

from src.errors import GraphError
from src.graph import build_graph, package_name
from src.local_repo import parse_test_graph
from tests.helpers import fixture

DATA = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}


def _loader(data):
    """Create a dependency loader from a dictionary."""
    return lambda node: data.get(node, [])


class GraphTests(unittest.TestCase):
    """Exercise depth limits, filtering and cycles."""

    def test_builds_full_graph(self):
        """Reach every node when the depth is large enough."""
        self.assertEqual(build_graph("A", _loader(DATA), 5), DATA)

    def test_depth_zero_keeps_only_root(self):
        """Do not expand anything with depth zero."""
        self.assertEqual(build_graph("A", _loader(DATA), 0), {"A": []})

    def test_depth_limit(self):
        """Keep nodes at the limit but do not expand them."""
        graph = build_graph("A", _loader(DATA), 1)
        self.assertEqual(graph, {"A": ["B", "C"], "B": [], "C": []})

    def test_depth_two(self):
        """Include the third level when the depth is two."""
        graph = build_graph("A", _loader(DATA), 2)
        self.assertEqual(graph["B"], ["D"])
        self.assertEqual(graph["D"], [])

    def test_filter_removes_nodes_and_edges(self):
        """Exclude matching packages and everything behind them."""
        data = {"A": ["BX", "C"], "BX": ["D"], "C": [], "D": []}
        graph = build_graph("A", _loader(data), 5, "X")
        self.assertEqual(graph, {"A": ["C"], "C": []})

    def test_filter_uses_package_name_not_version(self):
        """Ignore the version part when matching the filter."""
        data = {"g:a:1.2": ["g:b:1.2"], "g:b:1.2": []}
        graph = build_graph("g:a:1.2", _loader(data), 3, "1.2")
        self.assertEqual(len(graph), 2)

    def test_filter_matching_root_is_an_error(self):
        """Refuse to filter out the analyzed package itself."""
        with self.assertRaises(GraphError):
            build_graph("A", _loader(DATA), 3, "A")

    def test_cycle_terminates(self):
        """Visit every node of a cycle once."""
        graph = parse_test_graph(fixture("cyclic.txt"))
        built = build_graph("A", _loader(graph), 50)
        self.assertEqual(built, graph)

    def test_self_dependency_terminates(self):
        """Accept a package that depends on itself."""
        graph = build_graph("A", _loader({"A": ["A"]}), 9)
        self.assertEqual(graph, {"A": ["A"]})

    def test_loader_called_once_per_node(self):
        """Expand a shared dependency only once."""
        calls = []

        def loader(node):
            """Record calls and answer from DATA."""
            calls.append(node)
            return DATA.get(node, [])

        build_graph("A", loader, 5)
        self.assertEqual(sorted(calls), ["A", "B", "C", "D"])

    def test_package_name(self):
        """Strip the version from Maven coordinates only."""
        self.assertEqual(package_name("g:a:1"), "g:a")
        self.assertEqual(package_name("A"), "A")


if __name__ == "__main__":
    unittest.main()
