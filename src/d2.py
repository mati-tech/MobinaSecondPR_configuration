"""Text representation of the dependency graph in the D2 language."""

from pathlib import Path

from .graph import Graph

ROOT_FILL = "#ffecb3"


def ordered_nodes(graph: Graph) -> list[str]:
    """List every node once, in graph order, including edge targets."""
    nodes = dict.fromkeys(graph)
    for dependencies in graph.values():
        nodes.update(dict.fromkeys(dependencies))
    return list(nodes)


def _escape(value: str) -> str:
    """Escape text for a double-quoted D2 string."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_d2(graph: Graph, root: str) -> str:
    """Return D2 source describing the graph; ids are n0, n1, and so on."""
    ids = {node: f"n{index}" for index, node in enumerate(ordered_nodes(graph))}
    lines = ["direction: right"]
    for node, node_id in ids.items():
        lines.append(f'{node_id}: "{_escape(node)}"')
    lines.append(f'{ids[root]}.style.fill: "{ROOT_FILL}"')
    for node, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(f"{ids[node]} -> {ids[dependency]}")
    return "\n".join(lines) + "\n"


def write_d2(graph: Graph, root: str, path: str) -> None:
    """Write the D2 source of the graph to a file."""
    Path(path).write_text(build_d2(graph, root), encoding="utf-8")
