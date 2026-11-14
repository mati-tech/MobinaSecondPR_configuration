"""Manual POM XML and local test graph parsing."""

import re
from pathlib import Path
from xml.etree.ElementTree import Element, ParseError, fromstring

from .errors import PomParseError, RepositoryError

PROPERTY_PATTERN = re.compile(r"\$\{([^}]+)\}")
IGNORED_SCOPES = {"test", "provided", "system"}
DEFAULT_SCOPE = "compile"
MAVEN_NAMESPACE = "{http://maven.apache.org/POM/4.0.0}"


def _tag(name: str) -> str:
    """Return a Maven POM tag with its optional namespace."""
    return f"{MAVEN_NAMESPACE}{name}"


def parse_pom(xml_text: str) -> list[str]:
    """Extract direct dependency coordinates from POM XML text."""
    try:
        root = fromstring(xml_text)
    except ParseError as exc:
        raise PomParseError(f"Malformed pom.xml: {exc}") from exc
    properties = _read_properties(root)
    result = []
    for dependency in _find_dependencies(root):
        coordinate = _dependency_coordinate(dependency, properties)
        if coordinate:
            result.append(coordinate)
    return result


def _read_properties(root: Element) -> dict[str, str]:
    """Read the <properties> section as a name-to-value mapping."""
    node = root.find(_tag("properties"))
    if node is None:
        return {}
    return {
        child.tag.split("}")[-1]: (child.text or "").strip()
        for child in node
    }


def _find_dependencies(root: Element) -> list[Element]:
    """Return the <dependency> elements of the top-level section."""
    node = root.find(_tag("dependencies"))
    if node is None:
        node = root.find("dependencies")
    if node is None:
        return []
    return node.findall(_tag("dependency"))


def _is_runtime_dependency(dependency: Element) -> bool:
    """Check that a dependency is required at compile or run time."""
    scope = _child_text(dependency, "scope") or DEFAULT_SCOPE
    optional = _child_text(dependency, "optional").lower() == "true"
    return not optional and scope not in IGNORED_SCOPES


def _dependency_coordinate(dependency: Element,
                           properties: dict[str, str]) -> str:
    """Build 'group:artifact:version' or return '' to skip the entry."""
    group = _child_text(dependency, "groupId")
    artifact = _child_text(dependency, "artifactId")
    if not group or not artifact:
        return ""
    if not _is_runtime_dependency(dependency):
        return ""
    version = _resolve_properties(_child_text(dependency, "version"),
                                  properties)
    return f"{group}:{artifact}:{version}" if version else ""


def _child_text(parent: Element, name: str) -> str:
    """Read and trim the text of a direct child element."""
    child = parent.find(_tag(name))
    if child is None:
        child = parent.find(name)
    return (child.text or "").strip() if child is not None else ""


def _resolve_properties(value: str, properties: dict[str, str]) -> str:
    """Resolve simple Maven property references without recursion."""
    for _ in range(len(properties) + 1):
        match = PROPERTY_PATTERN.search(value)
        if match is None:
            return value
        replacement = properties.get(match.group(1))
        if replacement is None:
            return ""
        value = value[:match.start()] + replacement + value[match.end():]
    return ""


def _is_package_name(name: str) -> bool:
    """Check that a test package is named with capital Latin letters."""
    return name.isalpha() and name.isupper()


def parse_test_graph(path: str) -> dict[str, list[str]]:
    """Parse lines formatted as 'PACKAGE: DEP1, DEP2'."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RepositoryError(f"Cannot read test graph: {exc}") from exc
    graph = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        package, dependencies = _parse_graph_line(line, line_number)
        if package in graph:
            raise RepositoryError(
                f"Duplicate package on line {line_number}: {package}"
            )
        graph[package] = dependencies
    return graph


def _parse_graph_line(line: str, line_number: int) -> tuple[str, list[str]]:
    """Parse one 'PACKAGE: DEP1, DEP2' row of the test graph."""
    if ":" not in line:
        raise RepositoryError(
            f"Invalid test graph line {line_number}: missing ':'."
        )
    package, dependency_text = line.split(":", maxsplit=1)
    package = package.strip()
    if not _is_package_name(package):
        raise RepositoryError(
            f"Invalid package name on line {line_number}: {package!r}"
        )
    dependencies = [
        item.strip() for item in dependency_text.split(",")
        if item.strip()
    ]
    if not all(_is_package_name(item) for item in dependencies):
        raise RepositoryError(f"Invalid dependency on line {line_number}.")
    return package, dependencies
