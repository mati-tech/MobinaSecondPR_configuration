"""D2 export and dependency graph PNG rendering."""

import struct
import zlib
from pathlib import Path

CANVAS_WIDTH = 900
CANVAS_HEIGHT = 600
NODE_WIDTH = 150
NODE_HEIGHT = 42
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def write_d2(graph: dict[str, list[str]], path: str) -> None:
    """Write a D2 diagram describing all dependency edges."""
    lines = ["direction: right"]
    for node in sorted(graph):
        lines.append(f'"{_escape(node)}": {{shape: rectangle}}')
    for node, dependencies in sorted(graph.items()):
        for dependency in dependencies:
            lines.append(
                f'"{_escape(node)}" -> "{_escape(dependency)}"'
            )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_png(graph: dict[str, list[str]], path: str) -> None:
    """Create a simple standard-library PNG graph without dependencies."""
    nodes = sorted(set(graph) | {
        item for values in graph.values() for item in values
    })
    if not nodes:
        nodes = ["(empty)"]
    pixels = bytearray([255] * CANVAS_WIDTH * CANVAS_HEIGHT * 3)
    positions = _positions(nodes)
    for source, targets in graph.items():
        for target in targets:
            _draw_line(pixels, positions[source], positions[target])
    for node in nodes:
        _draw_node(pixels, positions[node], node)
    _write_png(path, pixels)


def _escape(value: str) -> str:
    """Escape text for a quoted D2 identifier."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _positions(nodes: list[str]) -> dict[str, tuple[int, int]]:
    """Place nodes in columns according to their sorted index."""
    positions = {}
    columns = 3
    for index, node in enumerate(nodes):
        column = index % columns
        row = index // columns
        x = 170 + column * 270
        y = 90 + row * 110
        positions[node] = (x, y)
    return positions


def _set_pixel(pixels: bytearray, x: int, y: int, color) -> None:
    """Set one pixel if it lies within the canvas."""
    if 0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT:
        offset = (y * CANVAS_WIDTH + x) * 3
        pixels[offset:offset + 3] = bytes(color)


def _draw_line(pixels, start, end) -> None:
    """Draw an edge using the integer Bresenham algorithm."""
    x1, y1 = start
    x2, y2 = end
    dx = abs(x2 - x1)
    sx = 1 if x1 < x2 else -1
    dy = -abs(y2 - y1)
    sy = 1 if y1 < y2 else -1
    error = dx + dy
    while True:
        _set_pixel(pixels, x1, y1, (90, 90, 90))
        if x1 == x2 and y1 == y2:
            break
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x1 += sx
        if doubled <= dx:
            error += dx
            y1 += sy


def _draw_node(pixels, center, label) -> None:
    """Draw a bordered rectangle as a package node."""
    center_x, center_y = center
    left = center_x - NODE_WIDTH // 2
    top = center_y - NODE_HEIGHT // 2
    right = left + NODE_WIDTH
    bottom = top + NODE_HEIGHT
    for x in range(left, right):
        _set_pixel(pixels, x, top, (20, 70, 130))
        _set_pixel(pixels, x, bottom, (20, 70, 130))
    for y in range(top, bottom):
        _set_pixel(pixels, left, y, (20, 70, 130))
        _set_pixel(pixels, right, y, (20, 70, 130))
    _draw_label_bar(pixels, center, label)


def _draw_label_bar(pixels, center, label) -> None:
    """Draw a short deterministic bar that stands for the node label.

    The minimal PNG renderer has no font support, so the bar width is
    proportional to the label length instead of drawing the text.
    """
    center_x, center_y = center
    bar_width = min(len(label) * 5, NODE_WIDTH - 20)
    for y in range(center_y - 2, center_y + 3):
        for x in range(center_x - bar_width // 2,
                       center_x - bar_width // 2 + bar_width):
            _set_pixel(pixels, x, y, (35, 35, 35))


def _write_png(path: str, pixels: bytearray) -> None:
    """Encode RGB pixels into a valid PNG file."""
    raw = bytearray()
    stride = CANVAS_WIDTH * 3
    for row in range(CANVAS_HEIGHT):
        raw.append(0)
        start = row * stride
        raw.extend(pixels[start:start + stride])
    compressed = zlib.compress(bytes(raw))

    def chunk(name: bytes, data: bytes) -> bytes:
        """Build a PNG chunk with its CRC."""
        payload = name + data
        checksum = zlib.crc32(payload) & 0xFFFFFFFF
        return (struct.pack(">I", len(data)) + payload
                + struct.pack(">I", checksum))

    header = struct.pack(">2I", CANVAS_WIDTH, CANVAS_HEIGHT)
    content = (
        PNG_SIGNATURE + chunk(b"IHDR", header + b"\x08\x02\x00\x00\x00")
        + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")
    )
    Path(path).write_bytes(content)
