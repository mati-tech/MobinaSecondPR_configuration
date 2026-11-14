"""ASCII tree rendering of a dependency graph."""

from .errors import GraphError
from .graph import Graph

BRANCH = "|-- "
LAST_BRANCH = "`-- "
PIPE = "|   "
BLANK = "    "
CYCLE_MARK = " (cycle)"
REPEAT_MARK = " (*)"


def _frames(children: list[str], prefix: str, path: tuple[str, ...]):
    """Build stack frames for children, reversed so pop gives the first."""
    last = len(children) - 1
    frames = [(child, prefix, index == last, path + (child,))
              for index, child in enumerate(children)]
    return frames[::-1]


def _mark(graph: Graph, node: str, path, expanded: set[str]) -> str:
    """Return a marker for a cyclic or already expanded node."""
    if node in path[:-1]:
        return CYCLE_MARK
    if node in expanded and graph.get(node):
        return REPEAT_MARK
    return ""


def ascii_tree(graph: Graph, root: str) -> str:
    """Render a graph as an ASCII tree starting at the root.

    A node that closes a cycle is marked ``(cycle)``. A node whose
    dependencies were already printed is marked ``(*)`` and not repeated.
    """
    if root not in graph:
        raise GraphError(f"Root package is not in graph: {root}")
    lines = [root]
    expanded = {root}
    stack = _frames(graph[root], "", (root,))
    while stack:
        node, prefix, last, path = stack.pop()
        mark = _mark(graph, node, path, expanded)
        lines.append(prefix + (LAST_BRANCH if last else BRANCH) + node + mark)
        if not mark:
            expanded.add(node)
            child_prefix = prefix + (BLANK if last else PIPE)
            stack.extend(_frames(graph.get(node, []), child_prefix, path))
    return "\n".join(lines)
