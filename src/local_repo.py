"""Reader for the local test repository (adjacency list) format."""

from pathlib import Path

from .config import is_package_letters
from .errors import RepositoryError


def parse_test_graph(path: str) -> dict[str, list[str]]:
    """Parse lines formatted as 'PACKAGE: DEP1, DEP2'."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise RepositoryError(f"Cannot read test graph: {exc}") from exc
    graph: dict[str, list[str]] = {}
    for number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if line and not line.startswith("#"):
            package, dependencies = _parse_line(line, number)
            if package in graph:
                raise RepositoryError(
                    f"Duplicate package on line {number}: {package}"
                )
            graph[package] = dependencies
    return graph


def _parse_line(line: str, number: int) -> tuple[str, list[str]]:
    """Parse one 'PACKAGE: DEP1, DEP2' row."""
    if ":" not in line:
        raise RepositoryError(f"Invalid line {number}: missing ':'.")
    package, text = line.split(":", maxsplit=1)
    package = package.strip()
    if not is_package_letters(package):
        raise RepositoryError(
            f"Invalid package name on line {number}: {package!r}"
        )
    dependencies = [item.strip() for item in text.split(",")
                    if item.strip()]
    if not all(is_package_letters(item) for item in dependencies):
        raise RepositoryError(f"Invalid dependency on line {number}.")
    return package, list(dict.fromkeys(dependencies))
