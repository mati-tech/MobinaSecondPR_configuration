"""Command-line configuration and validation."""

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .errors import ConfigurationError

DEFAULT_IMAGE = "dependency-graph.png"
DEFAULT_D2 = "dependency-graph.d2"
DEFAULT_DEPTH = 3
NAME_PARTS = 2
COORDINATE_PARTS = 3
URL_SCHEMES = ("http://", "https://", "file://")


@dataclass(frozen=True)
class Config:
    """Validated settings for one dependency graph run."""

    package: str
    repository: str
    test_mode: bool
    version: str
    image: str
    ascii_tree: bool
    max_depth: int
    filter_substring: str
    load_order: bool
    d2_file: str


class ConfigArgumentParser(ArgumentParser):
    """Argument parser that reports problems as configuration errors."""

    def error(self, message):
        """Raise a configuration error instead of exiting the process."""
        raise ConfigurationError(message)


def build_argument_parser() -> ArgumentParser:
    """Create the command-line argument parser."""
    parser = ConfigArgumentParser(
        description="Build and visualize a Maven dependency graph."
    )
    parser.add_argument("--package", required=True,
                        help="group:artifact (Maven) or a name such as A")
    parser.add_argument("--repository", required=True,
                        help="Maven repository URL or test graph file path")
    parser.add_argument("--test-mode", action="store_true",
                        help="treat --repository as a test graph file")
    parser.add_argument("--version", default="",
                        help="package version (Maven mode)")
    parser.add_argument("--image", default=DEFAULT_IMAGE,
                        help="output PNG file name")
    parser.add_argument("--ascii-tree", action="store_true",
                        help="print dependencies as an ASCII tree")
    parser.add_argument("--max-depth", type=int, default=DEFAULT_DEPTH,
                        help="maximum dependency depth (root is 0)")
    parser.add_argument("--filter", dest="filter_substring", default="",
                        help="skip packages whose name contains this text")
    parser.add_argument("--load-order", action="store_true",
                        help="print the dependency-first load order")
    parser.add_argument("--d2-file", default=DEFAULT_D2,
                        help="output D2 diagram source file name")
    return parser


def parse_config(args: Sequence[str] | None = None) -> Config:
    """Parse and validate command-line arguments."""
    namespace = build_argument_parser().parse_args(args)
    return config_from_namespace(namespace)


def is_package_letters(name: str) -> bool:
    """Check that a test package is named with capital Latin letters."""
    return name.isascii() and name.isalpha() and name.isupper()


def split_package(package: str) -> tuple[str, str]:
    """Split group:artifact[:version] into a name and an optional version."""
    parts = package.split(":")
    valid_size = len(parts) in (NAME_PARTS, COORDINATE_PARTS)
    if not valid_size or not all(parts) or " " in package:
        raise ConfigurationError(
            "--package must look like group:artifact or "
            "group:artifact:version in Maven mode."
        )
    name = ":".join(parts[:NAME_PARTS])
    version = parts[NAME_PARTS] if len(parts) == COORDINATE_PARTS else ""
    return name, version


def _check_maven(namespace: Namespace) -> tuple[str, str]:
    """Validate Maven-mode options and return package name and version."""
    if not namespace.repository.startswith(URL_SCHEMES):
        raise ConfigurationError(
            "--repository must start with http://, https:// or file://."
        )
    name, embedded = split_package(namespace.package.strip())
    explicit = namespace.version.strip()
    if explicit and embedded and explicit != embedded:
        raise ConfigurationError(
            "--version conflicts with the version inside --package."
        )
    version = explicit or embedded
    if not version or " " in version:
        raise ConfigurationError("A package version is required (--version).")
    return name, version


def _check_test_mode(namespace: Namespace) -> str:
    """Validate test-mode options and return the root package name."""
    if not Path(namespace.repository).is_file():
        raise ConfigurationError(
            f"Test repository file does not exist: {namespace.repository}"
        )
    package = namespace.package.strip()
    if not is_package_letters(package):
        raise ConfigurationError(
            "Test-mode package names use capital Latin letters (e.g. A)."
        )
    return package


def _check_output(path: str, suffix: str, option: str) -> None:
    """Validate an output file name and its target directory."""
    if not path.lower().endswith(suffix):
        raise ConfigurationError(f"{option} must end with {suffix}.")
    if not Path(path).resolve().parent.is_dir():
        raise ConfigurationError(f"Directory for {option} does not exist.")


def config_from_namespace(namespace: Namespace) -> Config:
    """Validate parsed arguments and construct an immutable config."""
    if namespace.max_depth < 0:
        raise ConfigurationError("--max-depth must be zero or greater.")
    _check_output(namespace.image, ".png", "--image")
    _check_output(namespace.d2_file, ".d2", "--d2-file")
    if namespace.test_mode:
        package, version = _check_test_mode(namespace), ""
    else:
        package, version = _check_maven(namespace)
    return Config(
        package=package,
        repository=namespace.repository.strip(),
        test_mode=namespace.test_mode,
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
    print("Configuration:")
    for key, value in vars(config).items():
        print(f"  {key}={value}")
