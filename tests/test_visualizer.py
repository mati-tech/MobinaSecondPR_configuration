"""Tests for D2 and PNG output."""

import tempfile
import unittest
from pathlib import Path

from src.visualizer import PNG_SIGNATURE, render_png, write_d2


class VisualizerTests(unittest.TestCase):
    """Check generated diagram files."""

    def test_writes_d2_and_png(self):
        """Write a D2 graph and a valid PNG signature."""
        graph = {"A": ["B"], "B": []}
        with tempfile.TemporaryDirectory() as folder:
            d2_path = Path(folder) / "graph.d2"
            png_path = Path(folder) / "graph.png"
            write_d2(graph, str(d2_path))
            render_png(graph, str(png_path))
            self.assertIn('"A" -> "B"', d2_path.read_text())
            self.assertTrue(png_path.read_bytes().startswith(PNG_SIGNATURE))


if __name__ == "__main__":
    unittest.main()
