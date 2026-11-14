"""A tiny RGB raster canvas with a standard-library PNG encoder."""

import math
import struct
import zlib
from pathlib import Path

from .font import GLYPH_HEIGHT, GLYPH_WIDTH, glyph_rows

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
WHITE = (255, 255, 255)
CHANNELS = 3
BIT_DEPTH = 8
COLOR_TYPE_RGB = 2


class Canvas:
    """A mutable RGB image that can be saved as a PNG file."""

    def __init__(self, width: int, height: int, background=WHITE) -> None:
        """Create a canvas filled with a background color."""
        self.width = width
        self.height = height
        self.pixels = bytearray(bytes(background) * (width * height))

    def set_pixel(self, x: int, y: int, color) -> None:
        """Set one pixel if it lies inside the canvas."""
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * CHANNELS
            self.pixels[offset:offset + CHANNELS] = bytes(color)

    def fill_rect(self, left: int, top: int, width: int, height: int,
                  color) -> None:
        """Fill a rectangle, clipped to the canvas."""
        start = max(left, 0)
        stop = min(left + width, self.width)
        if stop <= start:
            return
        row = bytes(color) * (stop - start)
        for y in range(max(top, 0), min(top + height, self.height)):
            offset = (y * self.width + start) * CHANNELS
            self.pixels[offset:offset + len(row)] = row

    def draw_rect(self, left: int, top: int, width: int, height: int,
                  color, thickness: int = 2) -> None:
        """Draw a rectangle outline."""
        self.fill_rect(left, top, width, thickness, color)
        self.fill_rect(left, top + height - thickness, width, thickness,
                       color)
        self.fill_rect(left, top, thickness, height, color)
        self.fill_rect(left + width - thickness, top, thickness, height,
                       color)

    def draw_line(self, start, end, color, thickness: int = 2) -> None:
        """Draw a line with the integer Bresenham algorithm."""
        x1, y1 = round(start[0]), round(start[1])
        x2, y2 = round(end[0]), round(end[1])
        delta_x, delta_y = abs(x2 - x1), -abs(y2 - y1)
        step_x = 1 if x1 < x2 else -1
        step_y = 1 if y1 < y2 else -1
        error = delta_x + delta_y
        while True:
            self.fill_rect(x1, y1, thickness, thickness, color)
            if x1 == x2 and y1 == y2:
                return
            doubled = 2 * error
            if doubled >= delta_y:
                error += delta_y
                x1 += step_x
            if doubled <= delta_x:
                error += delta_x
                y1 += step_y

    def fill_arrow_head(self, tip, source, color, size: int = 14) -> None:
        """Draw a filled triangle at ``tip`` pointing away from ``source``."""
        angle = math.atan2(tip[1] - source[1], tip[0] - source[0])
        points = [tip]
        for offset in (math.pi - 0.45, math.pi + 0.45):
            points.append((tip[0] + size * math.cos(angle + offset),
                           tip[1] + size * math.sin(angle + offset)))
        self._fill_triangle(points, color)

    def _fill_triangle(self, points, color) -> None:
        """Fill a triangle given by three points."""
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        for y in range(math.floor(min(ys)), math.ceil(max(ys)) + 1):
            for x in range(math.floor(min(xs)), math.ceil(max(xs)) + 1):
                if _inside(points, (x, y)):
                    self.set_pixel(x, y, color)

    def draw_text(self, x: int, y: int, text: str, color,
                  scale: int = 2) -> None:
        """Draw text with the embedded bitmap font."""
        for index, char in enumerate(text):
            left = x + index * GLYPH_WIDTH * scale
            for row, bits in enumerate(glyph_rows(char)):
                for col in range(GLYPH_WIDTH):
                    if bits >> (GLYPH_WIDTH - 1 - col) & 1:
                        self.fill_rect(left + col * scale, y + row * scale,
                                       scale, scale, color)

    def to_png(self) -> bytes:
        """Encode the canvas as PNG bytes."""
        stride = self.width * CHANNELS
        raw = bytearray()
        for row in range(self.height):
            raw.append(0)
            raw.extend(self.pixels[row * stride:(row + 1) * stride])
        header = struct.pack(">2I", self.width, self.height)
        header += bytes([BIT_DEPTH, COLOR_TYPE_RGB, 0, 0, 0])
        return (PNG_SIGNATURE + _chunk(b"IHDR", header)
                + _chunk(b"IDAT", zlib.compress(bytes(raw)))
                + _chunk(b"IEND", b""))

    def save(self, path: str) -> None:
        """Write the canvas to a PNG file."""
        Path(path).write_bytes(self.to_png())


def text_size(text: str, scale: int = 2) -> tuple[int, int]:
    """Return the pixel width and height of one line of text."""
    return len(text) * GLYPH_WIDTH * scale, GLYPH_HEIGHT * scale


def _chunk(name: bytes, data: bytes) -> bytes:
    """Build a PNG chunk with its CRC."""
    payload = name + data
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", checksum)


def _inside(points, point) -> bool:
    """Check whether a point lies inside a triangle (edges included)."""
    signs = []
    for index in range(len(points)):
        ax, ay = points[index]
        bx, by = points[(index + 1) % len(points)]
        signs.append((bx - ax) * (point[1] - ay) - (by - ay) * (point[0] - ax))
    return all(sign >= 0 for sign in signs) or all(sign <= 0 for sign in signs)
