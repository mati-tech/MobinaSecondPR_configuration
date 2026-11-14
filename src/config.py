"""Command-line configuration and validation."""

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .errors import ConfigurationError

DEFAULT_IMAGE = "dependency-graph.png"
DEFAULT_D2 = "dependency-graph.d2"
DEFAULT_DEPTH = 3
COORDINATE_SEPARATORS = 2
VERSION_INDEX = 2


@dataclass(frozen=True)
class Config:
    """Validated settings for one dependency graph run."""

    package: str
    repository: str
    test_mode: bool
    test_file: str
    version: str
    image: str
    ascii_tree: bool
    max_depth: int
    filter_substring: str
    load_order: bool
    d2_file: str


def build_argument_parser() -> ArgumentParser:
    """Create the command-line argument parser."""
    parser = ArgumentParser(
        description="Build and visualize a Maven dependency graph."
    )
    parser.add_argument("--package", required=True)
    parser.add_argument("--repository", default="")
    parser.add_argument("--test-mode", action="store_true")
    parser.add_argument("--test-file", default="")
    parser.add_argument("--version", default="")
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--ascii-tree", action="store_true")
    parser.add_argument("--max-depth", type=int, default=DEFAULT_DEPTH)
    parser.add_argument("--filter", dest="filter_substring", default="")
    parser.add_argument("--load-order", action="store_true")
    parser.add_argument("--d2-file", default=DEFAULT_D2)
    return parser


def parse_config(args: Sequence[str] | None = None) -> Config:
    """Parse and validate command-line arguments."""
    namespace = build_argument_parser().parse_args(args)
    return config_from_namespace(namespace)


def _validate_basics(namespace: Namespace, package: str) -> None:
    """Check the package name and the maximum depth."""
    if not package:
        raise ConfigurationError("Package name cannot be empty.")
    if namespace.max_depth < 0:
        raise ConfigurationError("--max-depth must be zero or greater.")


def _validate_sources(namespace: Namespace) -> None:
    """Check that exactly one dependency source fits the chosen mode."""
    if namespace.test_mode and not namespace.test_file:
        raise ConfigurationError("--test-file is required with --test-mode.")
    if not namespace.test_mode and not namespace.repository:
        raise ConfigurationError("--repository is required in Maven mode.")
    if namespace.test_mode and namespace.repository:
        raise ConfigurationError(
            "--repository cannot be combined with --test-mode."
        )


def _validate_package_format(namespace: Namespace, package: str) -> None:
    """Check the package name format required by the chosen mode."""
    separators = package.count(":")
    if not namespace.test_mode and separators != COORDINATE_SEPARATORS:
        raise ConfigurationError(
            "--package must use group:artifact:version in Maven mode."
        )
    if namespace.test_mode and separators:
        raise ConfigurationError("Test-mode package names cannot contain ':'.")


def _validate_test_file(namespace: Namespace) -> None:
    """Check that the test repository file exists when it is given."""
    if namespace.test_file and not Path(namespace.test_file).is_file():
        raise ConfigurationError(
            f"Test repository file does not exist: {namespace.test_file}"
        )


def _resolve_version(namespace: Namespace, package: str) -> str:
    """Use --version or take the version from a Maven coordinate."""
    version = namespace.version.strip()
    if not namespace.test_mode and not version:
        version = package.split(":")[VERSION_INDEX]
    return version


def config_from_namespace(namespace: Namespace) -> Config:
    """Validate parsed arguments and construct an immutable config."""
    package = namespace.package.strip()
    _validate_basics(namespace, package)
    _validate_sources(namespace)
    _validate_package_format(namespace, package)
    _validate_test_file(namespace)
    version = _resolve_version(namespace, package)
    return Config(
        package=package,
        repository=namespace.repository.strip(),
        test_mode=namespace.test_mode,
        test_file=namespace.test_file,
        version=version,
        image=namespace.image,
        ascii_tree=namespace.ascii_tree,
        max_depth=namespace.max_depth,
        filter_substring=namespace.filter_substring,
        load_order=namespace.load_order,
        d2_file=namespace.d2_file,
    )


def print_config(config: Config) -> None:
    """Print all user-configurable values in key-value format."""
    values = vars(config)
    print("Configuration:")
    for key, value in values.items():
        print(f"  {key}={value}")
