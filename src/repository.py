"""Maven repository access without Maven or third-party fetch libraries."""

from typing import Callable
from urllib.request import Request, urlopen

from .errors import RepositoryError
from .pom import PomInfo, parse_pom
from .resolver import resolve_dependencies

USER_AGENT = "DependencyGraphTool/1.0"
REQUEST_TIMEOUT = 15
MAX_PARENT_DEPTH = 20
COORDINATE_SIZE = 3


def fetch_text(url: str) -> str:
    """Download a text document from an http, https or file URL."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return response.read().decode("utf-8")
    except (OSError, ValueError) as exc:
        raise RepositoryError(f"Unable to fetch {url}: {exc}") from exc


class MavenRepository:
    """Read POM files from a repository that uses the Maven layout."""

    def __init__(
        self,
        base_url: str,
        fetcher: Callable[[str], str] = fetch_text,
    ) -> None:
        """Store the normalized repository URL and the fetch function."""
        self.base_url = base_url.rstrip("/")
        self.warnings: list[str] = []
        self._fetch = fetcher
        self._cache: dict[str, PomInfo] = {}

    def pom_url(self, coordinate: str) -> str:
        """Build the standard Maven-layout URL of a coordinate's POM."""
        parts = coordinate.split(":")
        if len(parts) != COORDINATE_SIZE or not all(parts):
            raise RepositoryError(f"Invalid Maven coordinate: {coordinate}")
        group, artifact, version = parts
        return (
            f"{self.base_url}/{group.replace('.', '/')}/{artifact}/"
            f"{version}/{artifact}-{version}.pom"
        )

    def load_pom(self, coordinate: str) -> PomInfo:
        """Download and parse one POM, caching the result."""
        if coordinate not in self._cache:
            text = self._fetch(self.pom_url(coordinate))
            self._cache[coordinate] = parse_pom(text)
        return self._cache[coordinate]

    def load_chain(self, coordinate: str) -> list[PomInfo]:
        """Load a POM followed by its parent POMs, without recursion."""
        chain = [self.load_pom(coordinate)]
        seen = {coordinate}
        while chain[-1].parent and len(chain) < MAX_PARENT_DEPTH:
            parent = ":".join(chain[-1].parent)
            if parent in seen:
                raise RepositoryError(f"Parent cycle at {parent}")
            seen.add(parent)
            try:
                chain.append(self.load_pom(parent))
            except RepositoryError as exc:
                self.warnings.append(f"{coordinate}: parent skipped: {exc}")
                break
        return chain

    def dependencies(self, coordinate: str) -> list[str]:
        """Return direct dependencies of one package version."""
        coordinates, warnings = resolve_dependencies(
            self.load_chain(coordinate)
        )
        self.warnings.extend(f"{coordinate}: {text}" for text in warnings)
        return coordinates
