"""Command-line entry point."""

import sys
from typing import Callable, NamedTuple

from .config import Config, parse_config, print_config
from .d2 import write_d2
from .errors import DependencyToolError, RepositoryError
from .graph import Graph, build_graph
from .local_repo import parse_test_graph
from .order import load_order
from .repository import MavenRepository
from .tree import ascii_tree
from .visualizer import create_image

EXIT_OK = 0
EXIT_ERROR = 2


class Source(NamedTuple):
    """Root node, dependency loader and collected warnings of a run."""

    root: str
    loader: Callable[[str], list[str]]
    warnings: list[str]


def _tolerant(loader, root: str, warnings: list[str]):
    """Wrap a loader so that only the root package must be loadable."""

    def wrapper(node: str) -> list[str]:
        """Load dependencies; report failures of non-root packages."""
        try:
            return loader(node)
        except RepositoryError as exc:
            if node == root:
                raise
            warnings.append(str(exc))
            return []

    return wrapper


def open_source(config: Config) -> Source:
    """Create the root node and loader for the configured repository."""
    if config.test_mode:
        test_graph = parse_test_graph(config.repository)
        if config.package not in test_graph:
            raise RepositoryError(
                f"Root package '{config.package}' is absent from test file."
            )
        return Source(config.package, lambda n: test_graph.get(n, []), [])
    repository = MavenRepository(config.repository)
    root = f"{config.package}:{config.version}"
    loader = _tolerant(repository.dependencies, root, repository.warnings)
    return Source(root, loader, repository.warnings)


def _print_direct(graph: Graph, root: str) -> None:
    """Print the direct dependencies of the root package."""
    print("\nDirect dependencies:")
    for dependency in graph.get(root, []):
        print(f"  - {dependency}")


def _print_order(graph: Graph, root: str) -> None:
    """Print the dependency-first load order and any cycles."""
    result = load_order(graph, root)
    print("\nDependency-first load order:")
    print(" -> ".join(result.order))
    for cycle in result.cycles:
        print(f"Warning: dependency cycle {' -> '.join(cycle)}")


def _write_outputs(config: Config, graph: Graph, root: str) -> None:
    """Write the D2 source and the PNG image."""
    write_d2(graph, root, config.d2_file)
    renderer = create_image(graph, root, config.d2_file, config.image)
    print(f"\nD2 diagram saved to: {config.d2_file}")
    print(f"PNG graph saved to: {config.image} ({renderer} renderer)")


def run(args=None) -> int:
    """Execute the configured dependency analysis."""
    try:
        config = parse_config(args)
        print_config(config)
        source = open_source(config)
        graph = build_graph(source.root, source.loader, config.max_depth,
                            config.filter_substring)
        _print_direct(graph, source.root)
        if config.ascii_tree:
            print("\nDependency tree:")
            print(ascii_tree(graph, source.root))
        if config.load_order:
            _print_order(graph, source.root)
        _write_outputs(config, graph, source.root)
        for warning in source.warnings:
            print(f"Warning: {warning}", file=sys.stderr)
        return EXIT_OK
    except (DependencyToolError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(run())
