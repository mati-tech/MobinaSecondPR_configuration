# Maven Dependency Graph Tool — Variant 23

A Python 3.10+ command-line application that reads Maven `pom.xml` files
without invoking Maven or using a third-party dependency-fetching package.
It builds a bounded dependency graph with iterative breadth-first search,
supports local test graphs, reports a dependency-first load order, writes
D2 diagram source, and creates a PNG visualization using only Python's
standard library.

## Requirements

- Python 3.10 or newer
- No third-party runtime packages
- `pytest` is optional and required only to run the test suite

## Repository layout

```text
dependency_graph_tool/
├── README.md
├── .gitignore
├── Makefile
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── errors.py
│   ├── parser.py
│   ├── repository.py
│   ├── graph.py
│   ├── visualizer.py
│   └── main.py
└── tests/
    ├── test_config.py
    ├── test_parser.py
    ├── test_graph.py
    ├── test_visualizer.py
    └── fixtures/
        ├── acyclic.txt
        ├── cyclic.txt
        └── filtered.txt
```

## CLI settings

| Option | Meaning |
| --- | --- |
| `--package` | Root package coordinate: `group:artifact:version` |
| `--repository` | Maven repository base URL or direct `pom.xml` URL |
| `--test-mode` | Read a local adjacency-list text file instead |
| `--test-file` | Path to the local test graph |
| `--version` | Version to analyze; overrides the version in `--package` |
| `--image` | Output PNG filename |
| `--ascii-tree` | Print dependencies as an ASCII tree |
| `--max-depth` | Maximum BFS depth; root has depth zero |
| `--filter` | Exclude package names containing this substring |
| `--load-order` | Print a dependency-first topological load order |
| `--d2-file` | Output D2 diagram source filename |

At startup, all settings are printed as key-value pairs. In test mode,
`--package` is the name of the root node (for example `A`). In Maven mode,
it must be a Maven coordinate. The `--repository` value may be a Maven
repository root (for example `https://repo1.maven.org/maven2`) or a URL
that points directly to a POM file.

## Run

```bash
python -m src.main --help

# Local graph
python -m src.main --package A --test-mode --test-file tests/fixtures/acyclic.txt \
  --ascii-tree --load-order --image graph.png --d2-file graph.d2

# Maven Central (the package must exist at the selected repository)
python -m src.main --package org.slf4j:slf4j-api:2.0.13 \
  --repository https://repo1.maven.org/maven2 --max-depth 2 \
  --ascii-tree --load-order
```

The test-file format is one package per line, followed by a colon and a
comma-separated list of its dependencies. Empty dependency lists are valid.

```text
A: B, C
B: D
C: D
D:
```

## Three test examples

**Example 1 — acyclic graph**

Input: `A: B, C`, `B: D`, `C: D`, `D:`

```text
A
├── B
│   └── D
└── C
    └── D
```

Dependency-first load order: `D -> B -> C -> A`.

**Example 2 — cycle**

Input: `A: B`, `B: C`, `C: A`

The graph traversal terminates because each node is expanded once.
Topological sorting reports a cycle instead of returning a false order.

**Example 3 — substring filter**

Input: `A: B, C`, `B:`, `C:`

With `--filter C`, the graph contains `A` and `B`; `C` is excluded.

## Maven parsing and limitations

The POM reader uses Python's standard-library XML parser. It extracts
direct `<dependencies>` entries, resolves simple `${property}` version
references, and ignores test, provided, system, and optional dependencies.
It does not implement the complete Maven model-building process:
parent inheritance, profiles, dependency mediation, BOM imports,
plugin dependencies, classifiers, version ranges, and all Maven property
rules are outside this assignment's scope. A repository root is used to
construct Maven's standard group/artifact/version POM path. For a direct
POM URL, only the root POM can be loaded unless its dependency POMs are
available through a repository URL.

The reported topological order is a graph-theory dependency-first order.
Real Maven resolution also applies scopes, exclusions, conflict mediation,
nearest-definition rules, parent POMs, BOMs, plugins, and lifecycle phases.
Therefore, this simplified order is not guaranteed to match Maven's
actual build or classpath resolution order.

## Visualization

The program always writes D2 source to `--d2-file`. It also creates a
basic PNG graph using a small standard-library renderer. The PNG is a
simple static visualization rather than a layout-engine-quality diagram.
If D2 is installed, the source can additionally be compiled with:

```bash
d2 graph.d2 graph-from-d2.png
```

## Tests

```bash
python -m unittest discover -s tests -v
# or, if pytest is installed:
pytest -q
```

## Error handling

Invalid CLI combinations, malformed XML, inaccessible URLs, missing files,
invalid graph rows, and cyclic topological-order requests produce readable
errors and a non-zero process exit code. Network requests use a timeout.
No Maven executable or third-party dependency downloader is used.
