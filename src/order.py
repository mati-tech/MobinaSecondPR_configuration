"""Dependency-first load order using an iterative depth-first search."""

from dataclasses import dataclass, field

from .graph import Graph


@dataclass
class LoadOrder:
    """A dependency-first order and the cycles met while computing it."""

    order: list[str] = field(default_factory=list)
    cycles: list[list[str]] = field(default_factory=list)


def load_order(graph: Graph, root: str) -> LoadOrder:
    """Return nodes reachable from the root, dependencies before dependents.

    The order is the post-order of a depth-first search that follows the
    dependency lists in their declared order. A back edge closes a cycle;
    it is reported and ignored, so the result is always produced.
    """
    result = LoadOrder()
    done: set[str] = set()
    path = [root]
    on_path = {root}
    iterators = [iter(graph.get(root, []))]
    while path:
        child = next(iterators[-1], None)
        if child is None:
            node = path.pop()
            iterators.pop()
            on_path.discard(node)
            done.add(node)
            result.order.append(node)
        elif child in on_path:
            result.cycles.append(path[path.index(child):] + [child])
        elif child not in done:
            path.append(child)
            on_path.add(child)
            iterators.append(iter(graph.get(child, [])))
    return result


def layer_levels(
    graph: Graph,
    root: str,
) -> tuple[dict[str, int], set[tuple[str, str]]]:
    """Assign each node its longest-path level, ignoring cycle edges.

    Returns the levels and the set of back edges that close cycles.
    With the back edges removed every other edge points to a deeper level.
    """
    result = load_order(graph, root)
    back = {(cycle[-2], cycle[-1]) for cycle in result.cycles}
    levels = {root: 0}
    for node in reversed(result.order):
        for dependency in graph.get(node, []):
            if (node, dependency) not in back:
                levels[dependency] = max(levels.get(dependency, 0),
                                         levels[node] + 1)
    return levels, back
