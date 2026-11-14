"""Layered left-to-right layout of a dependency graph."""

from dataclasses import dataclass

from .errors import GraphError
from .d2 import ordered_nodes
from .graph import Graph
from .order import layer_levels
from .raster import text_size

PADDING = 12
COLUMN_GAP = 110
ROW_GAP = 34
MARGIN = 40
TEXT_SCALE = 2
LANE_GAP = 16
MAX_PIXELS = 60_000_000


@dataclass(frozen=True)
class Layout:
    """Node boxes, canvas size and the top of the back-edge lanes."""

    boxes: dict
    width: int
    height: int
    lane_top: int
    back: frozenset


@dataclass(frozen=True)
class Box:
    """Position, size and label lines of one node."""

    x: int
    y: int
    width: int
    height: int
    lines: tuple[str, ...]

    @property
    def center(self) -> tuple[float, float]:
        """Return the center point."""
        return self.x + self.width / 2, self.y + self.height / 2

    @property
    def left(self) -> tuple[float, float]:
        """Return the middle of the left side."""
        return self.x, self.y + self.height / 2

    @property
    def right(self) -> tuple[float, float]:
        """Return the middle of the right side."""
        return self.x + self.width, self.y + self.height / 2


def _box_size(lines: tuple[str, ...]) -> tuple[int, int]:
    """Compute the size of a node box that fits its label lines."""
    width = max(text_size(line, TEXT_SCALE)[0] for line in lines)
    height = text_size("X", TEXT_SCALE)[1] * len(lines)
    return width + 2 * PADDING, height + 2 * PADDING


def _columns(graph: Graph, levels: dict[str, int]) -> list[list[str]]:
    """Group nodes by level, keeping the graph order inside a level."""
    unreachable = max(levels.values()) + 1
    columns: list[list[str]] = [[] for _ in range(unreachable + 1)]
    for node in ordered_nodes(graph):
        columns[levels.get(node, unreachable)].append(node)
    return [column for column in columns if column]


def compute_layout(graph: Graph, root: str) -> Layout:
    """Place nodes in level columns and size the canvas."""
    levels, back = layer_levels(graph, root)
    columns = _columns(graph, levels)
    sizes = {node: _box_size(tuple(node.split(":")))
             for column in columns for node in column}
    heights = [sum(sizes[n][1] + ROW_GAP for n in column) - ROW_GAP
               for column in columns]
    lanes = len(back)
    canvas_height = max(heights) + 2 * MARGIN + lanes * LANE_GAP
    boxes: dict[str, Box] = {}
    x = MARGIN
    for column, column_height in zip(columns, heights):
        y = MARGIN + (max(heights) - column_height) // 2
        for node in column:
            width, height = sizes[node]
            boxes[node] = Box(x, y, width, height, tuple(node.split(":")))
            y += height + ROW_GAP
        x += max(sizes[node][0] for node in column) + COLUMN_GAP
    canvas_width = x - COLUMN_GAP + MARGIN
    if canvas_width * canvas_height > MAX_PIXELS:
        raise GraphError("Graph is too large for the built-in PNG renderer.")
    return Layout(boxes, canvas_width, canvas_height,
                  MARGIN + max(heights) + LANE_GAP, frozenset(back))
