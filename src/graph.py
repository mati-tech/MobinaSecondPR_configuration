"""Iterative breadth-first construction of the dependency graph."""

from collections import deque
from typing import Callable

from .errors import GraphError

NAME_PARTS = 2

Graph = dict[str, list[str]]


def package_name(node: str) -> str:
    """Return the package name of a node, without its version."""
    parts = node.split(":")
    if len(parts) > NAME_PARTS:
        return ":".join(parts[:NAME_PARTS])
    return node


def is_excluded(node: str, substring: str) -> bool:
    """Check whether a node name contains the filter substring."""
    return bool(substring) and substring in package_name(node)


def build_graph(
    root: str,
    loader: Callable[[str], list[str]],
    max_depth: int,
    filter_substring: str = "",
) -> Graph:
    """Build a bounded dependency graph using BFS without recursion.

    The root has depth 0. Nodes at ``max_depth`` are kept in the graph but
    are not expanded. Every node is expanded once, so cycles terminate.
    Packages whose name contains ``filter_substring`` are skipped.
    """
    if is_excluded(root, filter_substring):
        raise GraphError(f"Root package matches the filter: {root}")
    graph: Graph = {root: []}
    queue = deque([(root, 0)])
    expanded: set[str] = set()
    while queue:
        node, depth = queue.popleft()
        if node in expanded or depth >= max_depth:
            continue
        expanded.add(node)
        accepted = [dep for dep in dict.fromkeys(loader(node))
                    if not is_excluded(dep, filter_substring)]
        graph[node] = accepted
        for dependency in accepted:
            graph.setdefault(dependency, [])
            queue.append((dependency, depth + 1))
    return graph
