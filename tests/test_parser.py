"""Tests for POM and local graph parsers."""

import tempfile
import unittest
from pathlib import Path

from src.errors import PomParseError, RepositoryError
from src.parser import parse_pom, parse_test_graph


class ParserTests(unittest.TestCase):
    """Verify dependency extraction and test graph parsing."""

    def test_parse_pom_dependencies(self):
        """Extract compile dependencies and resolve properties."""
        xml = """<project xmlns="http://maven.apache.org/POM/4.0.0">
          <properties><lib.version>1.2.3</lib.version></properties>
          <dependencies>
            <dependency><groupId>x</groupId><artifactId>one</artifactId>
              <version>${lib.version}</version></dependency>
            <dependency><groupId>x</groupId><artifactId>test</artifactId>
              <version>1</version><scope>test</scope></dependency>
          </dependencies></project>"""
        self.assertEqual(parse_pom(xml), ["x:one:1.2.3"])

    def test_malformed_xml(self):
        """Raise a domain error for malformed XML."""
        with self.assertRaises(PomParseError):
            parse_pom("<project>")

    def test_parse_test_graph(self):
        """Read package edges from a local file."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "graph.txt"
            path.write_text("A: B, C\nB:\nC:\n", encoding="utf-8")
            self.assertEqual(
                parse_test_graph(str(path)),
                {"A": ["B", "C"], "B": [], "C": []},
            )

    def test_invalid_test_graph_row(self):
        """Reject malformed adjacency-list rows."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.txt"
            path.write_text("A -> B\n", encoding="utf-8")
            with self.assertRaises(RepositoryError):
                parse_test_graph(str(path))


if __name__ == "__main__":
    unittest.main()
