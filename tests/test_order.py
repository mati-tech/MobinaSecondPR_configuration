"""Tests for the dependency-first load order."""

import unittest

from src.order import layer_levels, load_order

DATA = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}


class LoadOrderTests(unittest.TestCase):
    """Verify post-order output and cycle reporting."""

    def test_dependencies_come_first(self):
        """Place each package after everything it needs."""
        result = load_order(DATA, "A")
        self.assertEqual(result.order, ["D", "B", "C", "A"])
        self.assertEqual(result.cycles, [])

    def test_only_reachable_nodes(self):
        """Ignore nodes that the root does not need."""
        data = dict(DATA, X=["D"])
        self.assertNotIn("X", load_order(data, "A").order)

    def test_cycle_is_reported_and_order_is_complete(self):
        """Report the cycle and still return every package once."""
        data = {"A": ["B"], "B": ["C"], "C": ["A"]}
        result = load_order(data, "A")
        self.assertEqual(result.order, ["C", "B", "A"])
        self.assertEqual(result.cycles, [["A", "B", "C", "A"]])

    def test_single_package(self):
        """A lone package is its own order."""
        self.assertEqual(load_order({"A": []}, "A").order, ["A"])

    def test_self_cycle(self):
        """Report a package that requires itself."""
        result = load_order({"A": ["A"]}, "A")
        self.assertEqual(result.order, ["A"])
        self.assertEqual(result.cycles, [["A", "A"]])


class LayerTests(unittest.TestCase):
    """Verify longest-path levels used by the diagram layout."""

    def test_skip_edges_do_not_lower_levels(self):
        """Place a node below every package that requires it."""
        data = {"A": ["B", "C"], "B": ["C"], "C": []}
        levels, back = layer_levels(data, "A")
        self.assertEqual(levels, {"A": 0, "B": 1, "C": 2})
        self.assertEqual(back, set())

    def test_cycle_edge_is_a_back_edge(self):
        """Ignore the edge that closes a cycle."""
        data = {"A": ["B"], "B": ["C"], "C": ["A"]}
        levels, back = layer_levels(data, "A")
        self.assertEqual(levels, {"A": 0, "B": 1, "C": 2})
        self.assertEqual(back, {("C", "A")})


if __name__ == "__main__":
    unittest.main()
