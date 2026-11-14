"""Tests for POM parsing and property resolution."""

import unittest

from src.errors import PomParseError
from src.pom import parse_pom
from src.resolver import resolve_dependencies, substitute

NAMESPACE = 'xmlns="http://maven.apache.org/POM/4.0.0"'


def _dependency(artifact, version="", extra=""):
    """Build a <dependency> element."""
    tag = f"<version>{version}</version>" if version else ""
    return (f"<dependency><groupId>x</groupId>"
            f"<artifactId>{artifact}</artifactId>{tag}{extra}</dependency>")


def _resolve(xml):
    """Resolve the dependencies of a single POM without parents."""
    return resolve_dependencies([parse_pom(xml)])


class PomTests(unittest.TestCase):
    """Verify dependency extraction from POM text."""

    def test_properties_and_scopes(self):
        """Resolve properties and skip test, provided and optional."""
        xml = f"""<project {NAMESPACE}>
          <properties><lib.version>1.2.3</lib.version></properties>
          <dependencies>
            {_dependency("one", "${lib.version}")}
            {_dependency("two", "1", "<scope>test</scope>")}
            {_dependency("three", "1", "<scope>provided</scope>")}
            {_dependency("four", "1", "<optional>true</optional>")}
            {_dependency("five", "2", "<scope>runtime</scope>")}
          </dependencies></project>"""
        coordinates, warnings = _resolve(xml)
        self.assertEqual(coordinates, ["x:one:1.2.3", "x:five:2"])
        self.assertEqual(warnings, [])

    def test_pom_without_namespace(self):
        """Read a POM that has no XML namespace."""
        xml = f"<project><dependencies>{_dependency('a', '1')}" \
              "</dependencies></project>"
        self.assertEqual(_resolve(xml)[0], ["x:a:1"])

    def test_no_dependencies(self):
        """Return an empty list when nothing is declared."""
        self.assertEqual(_resolve(f"<project {NAMESPACE}/>")[0], [])

    def test_unresolved_version_gives_warning(self):
        """Skip dependencies with unknown properties and report them."""
        xml = f"""<project {NAMESPACE}><dependencies>
            {_dependency("a", "${unknown}")}
            {_dependency("b")}</dependencies></project>"""
        coordinates, warnings = _resolve(xml)
        self.assertEqual(coordinates, [])
        self.assertEqual(len(warnings), 2)

    def test_version_range_gives_warning(self):
        """Report version ranges as unsupported."""
        xml = f"""<project {NAMESPACE}><dependencies>
            {_dependency("a", "[1.0,2.0)")}</dependencies></project>"""
        coordinates, warnings = _resolve(xml)
        self.assertEqual(coordinates, [])
        self.assertIn("range", warnings[0])

    def test_duplicate_dependencies_are_merged(self):
        """Keep one copy of a repeated dependency."""
        xml = f"""<project {NAMESPACE}><dependencies>
            {_dependency("a", "1")}{_dependency("a", "1")}
            </dependencies></project>"""
        self.assertEqual(_resolve(xml)[0], ["x:a:1"])

    def test_malformed_xml(self):
        """Raise a domain error for malformed XML."""
        with self.assertRaises(PomParseError):
            parse_pom("<project>")

    def test_wrong_root_element(self):
        """Reject XML that is not a POM."""
        with self.assertRaises(PomParseError):
            parse_pom("<settings/>")

    def test_incomplete_parent(self):
        """Reject a <parent> without a version."""
        xml = "<project><parent><groupId>g</groupId></parent></project>"
        with self.assertRaises(PomParseError):
            parse_pom(xml)

    def test_substitute_limits(self):
        """Stop on unknown and self-referencing properties."""
        self.assertEqual(substitute("a${x}b", {"x": "-"}), "a-b")
        self.assertIsNone(substitute("${x}", {}))
        self.assertIsNone(substitute("${x}", {"x": "${x}"}))


if __name__ == "__main__":
    unittest.main()
