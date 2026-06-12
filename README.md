# lakeboard-to-xmind

[![CI](https://github.com/fhysy/lakeboard-to-xmind/actions/workflows/ci.yml/badge.svg)](https://github.com/fhysy/lakeboard-to-xmind/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)

Convert Youzan Lakeboard mind maps (`.lakeboard`) into XMind workbooks (`.xmind`).

Lakeboard files are JSON documents used by Youzan's Lakeboard whiteboard/mind-map format. This tool extracts the mind map tree from `diagramData.body`, cleans node titles, and writes an XMind-compatible `.xmind` ZIP package.

## Features

- Converts Youzan Lakeboard mind map nodes to XMind topics.
- Preserves title hierarchy, child order, and left/right branch layout.
- Preserves common Lakeboard visual styling, including topic fill colors, branch line colors, line widths, rounded topic shapes, and priority/flag markers where XMind supports them.
- Cleans HTML tags, `<br>`, zero-width characters, non-breaking spaces, and HTML entities from titles.
- Supports a template `.xmind` file for better compatibility with strict XMind versions.
- Writes the common XMind package entries: `content.json`, `metadata.json`, `manifest.json`, `content.xml`, and `Thumbnails/thumbnail.png`.
- Uses only the Python standard library at runtime.

## Installation

Install from a local checkout:

```bash
python -m pip install .
```

For development:

```bash
python -m pip install -e .
```

## Usage

Convert a Lakeboard file:

```bash
lakeboard-to-xmind input.lakeboard -o output.xmind
```

Use an existing XMind file as a compatibility and style template:

```bash
lakeboard-to-xmind input.lakeboard -o output.xmind --template template.xmind
```

Template mode is recommended when your XMind build rejects generic `.xmind` packages. The converter reuses the template's sheet/theme metadata, compatibility XML, manifest, and thumbnail, then replaces the actual topic tree.

Disable style copying if you only want the hierarchy:

```bash
lakeboard-to-xmind input.lakeboard -o output.xmind --no-style
```

## Python API

```python
from lakeboard_to_xmind import convert_lakeboard_to_xmind

result = convert_lakeboard_to_xmind(
    "input.lakeboard",
    "output.xmind",
    template="template.xmind",
)
print(result.topic_count)
```

## How It Works

1. Parse the `.lakeboard` file as UTF-8 JSON.
2. Find the first object in `diagramData.body` with `type == "mindmap"`.
3. Recursively convert each Lakeboard node's `html` and `children` into XMind topics.
4. Generate fresh XMind topic IDs and map common Lakeboard style fields to XMind topic style properties.
5. Package the result as an `.xmind` ZIP archive.

## Development

Run tests with the standard library test runner:

```bash
python -m unittest discover -s tests -v
```

Build the package:

```bash
python -m pip install build
python -m build
```

## Compatibility

This project targets the Lakeboard mind map shape observed in Youzan Lakeboard exports. Lakeboard may contain other board elements; only the first `mindmap` root is converted.

The converter preserves common mind-map styling fields. Advanced canvas-only decorations, such as freeform outer rectangles or some summary braces, may not have a one-to-one XMind equivalent and are handled conservatively.

XMind is a ZIP-based format. Newer XMind versions primarily read `content.json`; older or stricter builds may expect compatibility entries. Use `--template` with a known-good `.xmind` if you need exact compatibility with a specific XMind version.

## Roadmap

- Preserve Lakeboard colors and branch styles where practical.
- Support multiple mind map roots as multiple sheets.
- Add more real-world fixture files after removing private data.

## Contributing

Issues and pull requests are welcome. Please include a small sanitized `.lakeboard` sample when reporting conversion problems.

## License

MIT. See [LICENSE](LICENSE).

## Trademark Notice

Youzan, Lakeboard, and XMind are trademarks of their respective owners. This project is independent and is not affiliated with or endorsed by Youzan or XMind.

