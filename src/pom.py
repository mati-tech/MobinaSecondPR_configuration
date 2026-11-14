"""Manual Maven POM parsing based on the standard XML parser."""

from dataclasses import dataclass, field
from xml.etree.ElementTree import Element, ParseError, fromstring

from .errors import PomParseError

DEFAULT_SCOPE = "compile"


@dataclass(frozen=True)
class RawDependency:
    """A dependency declaration exactly as it is written in a POM."""

    group: str
    artifact: str
    version: str
    scope: str
    optional: bool


@dataclass
class PomInfo:
    """The parts of one POM file needed to resolve its dependencies."""

    group: str
    artifact: str
    version: str
    parent: tuple[str, str, str] | None
    properties: dict[str, str] = field(default_factory=dict)
    managed: list[RawDependency] = field(default_factory=list)
    dependencies: list[RawDependency] = field(default_factory=list)


def parse_pom(xml_text: str) -> PomInfo:
    """Parse POM XML text into a PomInfo structure."""
    root = _parse_root(xml_text)
    return PomInfo(
        group=_text(root, "groupId"),
        artifact=_text(root, "artifactId"),
        version=_text(root, "version"),
        parent=_read_parent(root),
        properties=_read_properties(root),
        managed=_read_dependencies(root.find("dependencyManagement/"
                                             "dependencies")),
        dependencies=_read_dependencies(root.find("dependencies")),
    )


def _parse_root(xml_text: str) -> Element:
    """Parse XML and drop namespaces so tags can be searched by name."""
    try:
        root = fromstring(xml_text)
    except ParseError as exc:
        raise PomParseError(f"Malformed pom.xml: {exc}") from exc
    for element in root.iter():
        if isinstance(element.tag, str) and "}" in element.tag:
            element.tag = element.tag.split("}", maxsplit=1)[1]
    if root.tag != "project":
        raise PomParseError("pom.xml root element must be <project>.")
    return root


def _text(node: Element, name: str) -> str:
    """Read and trim the text of a direct child element."""
    child = node.find(name)
    return (child.text or "").strip() if child is not None else ""


def _read_parent(root: Element) -> tuple[str, str, str] | None:
    """Read the parent coordinate, if the POM declares one."""
    node = root.find("parent")
    if node is None:
        return None
    parent = (_text(node, "groupId"), _text(node, "artifactId"),
              _text(node, "version"))
    if not all(parent):
        raise PomParseError("<parent> needs groupId, artifactId, version.")
    return parent


def _read_properties(root: Element) -> dict[str, str]:
    """Read the <properties> section as a name-to-value mapping."""
    node = root.find("properties")
    if node is None:
        return {}
    return {child.tag: (child.text or "").strip() for child in node}


def _read_dependencies(node: Element | None) -> list[RawDependency]:
    """Read every <dependency> element below a <dependencies> node."""
    if node is None:
        return []
    return [_read_dependency(item) for item in node.findall("dependency")]


def _read_dependency(item: Element) -> RawDependency:
    """Convert one <dependency> element into a RawDependency."""
    return RawDependency(
        group=_text(item, "groupId"),
        artifact=_text(item, "artifactId"),
        version=_text(item, "version"),
        scope=_text(item, "scope") or DEFAULT_SCOPE,
        optional=_text(item, "optional").lower() == "true",
    )
