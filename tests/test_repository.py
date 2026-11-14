"""Tests for Maven repository access using a local file:// repository."""

import unittest

from src.errors import RepositoryError
from src.repository import MavenRepository, fetch_text
from tests.helpers import MAVEN_REPO_URL


class RepositoryTests(unittest.TestCase):
    """Read the fixture repository that follows the Maven layout."""

    def setUp(self):
        """Create a repository bound to the fixture folder."""
        self.repository = MavenRepository(MAVEN_REPO_URL + "/")

    def test_pom_url(self):
        """Build the standard group/artifact/version path."""
        url = self.repository.pom_url("com.example:app:1.0")
        self.assertTrue(url.endswith("/com/example/app/1.0/app-1.0.pom"))

    def test_invalid_coordinate(self):
        """Reject coordinates that are not group:artifact:version."""
        with self.assertRaises(RepositoryError):
            self.repository.pom_url("broken")

    def test_parent_inheritance(self):
        """Take versions and properties from the parent POM."""
        self.assertEqual(
            self.repository.dependencies("com.example:app:1.0"),
            ["com.example:core:2.0", "com.example:util:3.1",
             "com.example:runtime-lib:1.0"],
        )

    def test_leaf_package(self):
        """A package without dependencies has an empty list."""
        self.assertEqual(
            self.repository.dependencies("com.example:logging:1.5"), [])

    def test_missing_pom(self):
        """Raise a readable error for an absent POM."""
        with self.assertRaises(RepositoryError):
            self.repository.dependencies("com.example:missing:1.0")

    def test_unsupported_range_is_reported(self):
        """Keep other dependencies and record a warning."""
        result = self.repository.dependencies("com.example:ranged:1.0")
        self.assertEqual(result, ["com.example:util:3.1"])
        self.assertEqual(len(self.repository.warnings), 1)

    def test_fetch_error(self):
        """Wrap network and file failures in RepositoryError."""
        with self.assertRaises(RepositoryError):
            fetch_text(MAVEN_REPO_URL + "/nothing.pom")

    def test_missing_parent_gives_warning(self):
        """Continue when the parent POM cannot be downloaded."""
        pages = {
            "http://h/g/a/1/a-1.pom":
                "<project><parent><groupId>g</groupId>"
                "<artifactId>p</artifactId><version>1</version></parent>"
                "<dependencies><dependency><groupId>g</groupId>"
                "<artifactId>d</artifactId><version>2</version>"
                "</dependency></dependencies></project>",
        }

        def fetcher(url):
            """Serve pages from a dictionary."""
            if url not in pages:
                raise RepositoryError(f"no {url}")
            return pages[url]

        repository = MavenRepository("http://h", fetcher)
        self.assertEqual(repository.dependencies("g:a:1"), ["g:d:2"])
        self.assertEqual(len(repository.warnings), 1)


if __name__ == "__main__":
    unittest.main()
