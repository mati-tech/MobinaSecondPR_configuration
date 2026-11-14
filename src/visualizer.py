"""PNG rendering of the dependency graph (D2 CLI or built-in drawing)."""

import shutil
import subprocess
from pathlib import Path

from .graph import Graph
from .layout import LANE_GAP, TEXT_SCALE, Box, Layout, compute_layout
from .raster import Canvas, text_size

D2_TIMEOUT = 120
EDGE_COLOR = (80, 80, 80)
BACK_EDGE_COLOR = (200, 50, 50)
BOX_COLOR = (233, 242, 252)
ROOT_COLOR = (255, 236, 179)
BORDER_COLOR = (20, 70, 130)
TEXT_COLOR = (25, 25, 25)
BACK_SHIFT = 18
SHIFT_STEP = 6
SHIFT_CYCLE = 6


def _draw_back_edge(canvas: Canvas, source: Box, target: Box,
                    lane_y: int, shift: int) -> None:
    """Route a cycle edge below the boxes, through the column gaps."""
    start, end = source.right, target.left
    out_x, in_x = start[0] + shift, end[0] - shift
    points = [start, (out_x, start[1]), (out_x, lane_y), (in_x, lane_y),
              (in_x, end[1]), end]
    for first, second in zip(points, points[1:]):
        canvas.draw_line(first, second, BACK_EDGE_COLOR)
    canvas.fill_arrow_head(end, points[-2], BACK_EDGE_COLOR)


def _draw_edges(canvas: Canvas, graph: Graph, layout: Layout) -> None:
    """Draw edges first so that boxes can cover their inner parts."""
    boxes = layout.boxes
    arrows = []
    lane = 0
    for node, dependencies in graph.items():
        for dependency in dependencies:
            if (node, dependency) in layout.back:
                if node != dependency:
                    _draw_back_edge(
                        canvas, boxes[node], boxes[dependency],
                        layout.lane_top + lane * LANE_GAP,
                        BACK_SHIFT + SHIFT_STEP * (lane % SHIFT_CYCLE))
                    lane += 1
                continue
            start, end = boxes[node].right, boxes[dependency].left
            canvas.draw_line(start, end, EDGE_COLOR)
            arrows.append((end, start))
    for tip, start in arrows:
        canvas.fill_arrow_head(tip, start, EDGE_COLOR)


def _draw_boxes(canvas: Canvas, boxes, root: str) -> None:
    """Draw node rectangles and their centered labels."""
    for node, box in boxes.items():
        fill = ROOT_COLOR if node == root else BOX_COLOR
        canvas.fill_rect(box.x, box.y, box.width, box.height, fill)
        canvas.draw_rect(box.x, box.y, box.width, box.height, BORDER_COLOR)
        line_height = text_size("X", TEXT_SCALE)[1]
        top = box.y + (box.height - line_height * len(box.lines)) // 2
        for index, line in enumerate(box.lines):
            width = text_size(line, TEXT_SCALE)[0]
            canvas.draw_text(box.x + (box.width - width) // 2,
                             top + index * line_height, line, TEXT_COLOR,
                             TEXT_SCALE)


def draw_graph(graph: Graph, root: str) -> Canvas:
    """Draw the whole graph on a new canvas."""
    layout = compute_layout(graph, root)
    canvas = Canvas(layout.width, layout.height)
    _draw_edges(canvas, graph, layout)
    _draw_boxes(canvas, layout.boxes, root)
    return canvas


def render_png(graph: Graph, root: str, path: str) -> None:
    """Create the PNG with the built-in standard-library renderer."""
    draw_graph(graph, root).save(path)


def render_with_d2(d2_path: str, png_path: str) -> bool:
    """Try to render the D2 file with the d2 command; report success."""
    executable = shutil.which("d2")
    if executable is None:
        return False
    try:
        result = subprocess.run(
            [executable, d2_path, png_path],
            capture_output=True, timeout=D2_TIMEOUT, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and Path(png_path).is_file()


def create_image(graph: Graph, root: str, d2_path: str,
                 png_path: str) -> str:
    """Create the PNG; return the name of the renderer that was used."""
    if render_with_d2(d2_path, png_path):
        return "d2"
    render_png(graph, root, png_path)
    return "built-in"
