"""Application-specific exceptions."""


class DependencyToolError(Exception):
    """Base exception for expected application errors."""


class ConfigurationError(DependencyToolError):
    """Raised when command-line configuration is invalid."""


class RepositoryError(DependencyToolError):
    """Raised when repository data cannot be read."""


class PomParseError(DependencyToolError):
    """Raised when a POM document is malformed or invalid."""


class GraphError(DependencyToolError):
    """Raised when graph operations cannot be completed."""
