"""Resolve effective POM values (properties, managed versions)."""

import re

from .pom import PomInfo, RawDependency

PROPERTY_PATTERN = re.compile(r"\$\{([^}]+)\}")
MAX_SUBSTITUTIONS = 20
USED_SCOPES = {"compile", "runtime"}
RANGE_PREFIXES = ("[", "(")


def substitute(text: str, properties: dict[str, str]) -> str | None:
    """Replace ${name} references; return None if one cannot be resolved."""
    for _ in range(MAX_SUBSTITUTIONS):
        match = PROPERTY_PATTERN.search(text)
        if match is None:
            return text
        value = properties.get(match.group(1))
        if value is None:
            return None
        text = text[:match.start()] + value + text[match.end():]
    return None


def project_properties(chain: list[PomInfo]) -> dict[str, str]:
    """Merge properties along the parent chain (the child wins)."""
    merged: dict[str, str] = {}
    for info in reversed(chain):
        merged.update(info.properties)
    child = chain[0]
    parent = child.parent or ("", "", "")
    group = child.group or parent[0]
    version = child.version or parent[2]
    merged.update({
        "project.groupId": group,
        "pom.groupId": group,
        "project.artifactId": child.artifact,
        "project.version": version,
        "pom.version": version,
        "project.parent.groupId": parent[0],
        "project.parent.version": parent[2],
    })
    return merged


def managed_versions(
    chain: list[PomInfo],
    properties: dict[str, str],
) -> dict[tuple[str, str], str]:
    """Collect dependencyManagement versions; the child wins."""
    managed: dict[tuple[str, str], str] = {}
    for info in reversed(chain):
        for dep in info.managed:
            if dep.scope == "import" or not dep.version:
                continue
            values = [substitute(item, properties)
                      for item in (dep.group, dep.artifact, dep.version)]
            if None not in values:
                managed[(values[0], values[1])] = values[2]
    return managed


def _resolve_one(
    dep: RawDependency,
    properties: dict[str, str],
    managed: dict[tuple[str, str], str],
) -> tuple[str | None, str | None]:
    """Resolve one dependency to a coordinate or to a warning."""
    group = substitute(dep.group, properties)
    artifact = substitute(dep.artifact, properties)
    if group is None or artifact is None:
        return None, f"unresolved name of {dep.group}:{dep.artifact}"
    raw_version = dep.version or managed.get((group, artifact), "")
    version = substitute(raw_version, properties) if raw_version else None
    if not version:
        return None, f"no resolvable version for {group}:{artifact}"
    if version.startswith(RANGE_PREFIXES):
        return None, f"version range not supported: {group}:{artifact}"
    return f"{group}:{artifact}:{version}", None


def resolve_dependencies(
    chain: list[PomInfo],
) -> tuple[list[str], list[str]]:
    """Return direct compile/runtime coordinates and resolution warnings."""
    properties = project_properties(chain)
    managed = managed_versions(chain, properties)
    coordinates: list[str] = []
    warnings: list[str] = []
    for dep in chain[0].dependencies:
        if dep.optional or dep.scope not in USED_SCOPES:
            continue
        coordinate, warning = _resolve_one(dep, properties, managed)
        if warning:
            warnings.append(warning)
        elif coordinate not in coordinates:
            coordinates.append(coordinate)
    return coordinates, warnings
