"""Tests for D2 and PNG output."""

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from src.d2 import build_d2, write_d2
from src.errors import GraphError
from src.font import glyph_rows
from src.layout import compute_layout
from src.raster import PNG_SIGNATURE, Canvas
from src.visualizer import create_image, render_png

DATA = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}


def _decode_png(content):
    """Decode a PNG produced by Canvas into (width, height, rows)."""
    width, height = struct.unpack(">2I", content[16:24])
    start = content.index(b"IDAT") + 4
    size = struct.unpack(">I", content[start - 8:start - 4])[0]
    raw = zlib.decompress(content[start:start + size])
    stride = width * 3 + 1
    return width, height, [raw[i * stride:(i + 1) * stride]
                           for i in range(height)]


class D2Tests(unittest.TestCase):
    """Check the generated D2 text."""

    def test_nodes_and_edges(self):
        """Declare labelled nodes and all edges."""
        text = build_d2(DATA, "A")
        self.assertIn('n0: "A"', text)
        self.assertIn("n0 -> n1", text)
        self.assertEqual(text.count("->"), 4)

    def test_quotes_are_escaped(self):
        """Escape quotes inside labels."""
        self.assertIn('n0: "a\\"b"', build_d2({'a"b': []}, 'a"b'))

    def test_write_file(self):
        """Write the D2 source to disk."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "graph.d2"
            write_d2(DATA, "A", str(path))
            self.assertTrue(path.read_text().startswith("direction:"))


class PngTests(unittest.TestCase):
    """Check PNG encoding and rendering."""

    def test_canvas_png_roundtrip(self):
        """Encode a coloured pixel and read it back."""
        canvas = Canvas(3, 2)
        canvas.set_pixel(1, 1, (10, 20, 30))
        width, height, rows = _decode_png(canvas.to_png())
        self.assertEqual((width, height), (3, 2))
        self.assertEqual(rows[1][1 + 3:1 + 6], bytes((10, 20, 30)))

    def test_render_png_file(self):
        """Create a valid PNG for a graph."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "graph.png"
            render_png(DATA, "A", str(path))
            self.assertTrue(path.read_bytes().startswith(PNG_SIGNATURE))

    def test_create_image_reports_renderer(self):
        """Fall back to the built-in renderer or use d2 when installed."""
        with tempfile.TemporaryDirectory() as folder:
            d2_path = str(Path(folder) / "g.d2")
            png_path = str(Path(folder) / "g.png")
            write_d2(DATA, "A", d2_path)
            renderer = create_image(DATA, "A", d2_path, png_path)
            self.assertIn(renderer, {"d2", "built-in"})
            self.assertTrue(Path(png_path).is_file())

    def test_cycle_graph_renders(self):
        """Draw back edges and self loops without errors."""
        graph = {"A": ["B", "A"], "B": ["A"]}
        self.assertGreater(len(Canvas(5, 5).to_png()), 0)
        self.assertTrue(render_png_bytes(graph))

    def test_layout_boxes_do_not_overlap(self):
        """Give every node its own non-overlapping box."""
        layout = compute_layout(DATA, "A")
        width, height = layout.width, layout.height
        self.assertEqual(len(layout.boxes), 4)
        items = list(layout.boxes.values())
        for index, first in enumerate(items):
            self.assertLessEqual(first.x + first.width, width)
            self.assertLessEqual(first.y + first.height, height)
            for second in items[index + 1:]:
                apart = (first.x + first.width <= second.x
                         or second.x + second.width <= first.x
                         or first.y + first.height <= second.y
                         or second.y + second.height <= first.y)
                self.assertTrue(apart)

    def test_font_has_visible_glyphs(self):
        """Letters have pixels; a space has none; unknown uses '?'."""
        self.assertTrue(any(glyph_rows("A")))
        self.assertFalse(any(glyph_rows(" ")))
        self.assertEqual(glyph_rows("\u0436"), glyph_rows("?"))

    def test_huge_graph_is_rejected(self):
        """Refuse graphs that would need an enormous image."""
        huge = {"R": [f"N{index}" for index in range(3000)]}
        with self.assertRaises(GraphError):
            compute_layout(huge, "R")


def render_png_bytes(graph):
    """Render a graph into PNG bytes using a temporary file."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "graph.png"
        render_png(graph, "A", str(path))
        return path.read_bytes()


if __name__ == "__main__":
    unittest.main()
