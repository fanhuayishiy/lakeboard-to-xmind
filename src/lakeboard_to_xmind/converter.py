from __future__ import annotations

import html
import json
import re
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONTENT_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?><xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" xmlns:fo="http://www.w3.org/1999/XSL/Format" xmlns:svg="http://www.w3.org/2000/svg" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xlink="http://www.w3.org/1999/xlink" modified-by="lakeboard-to-xmind" timestamp="1503058545540" version="2.0"><sheet id="7abtd0ssc7n4pi1nu6i7b6lsdh" modified-by="lakeboard-to-xmind" timestamp="1503058545540"><topic id="1vr0lcte2og4t2sopiogvdmifc" modified-by="lakeboard-to-xmind" structure-class="org.xmind.ui.logic.right" timestamp="1503058545417"><title>Warning\n警告</title><children><topics type="attached"><topic id="71h1aip2t1o8vvm0a41nausaar" modified-by="lakeboard-to-xmind" timestamp="1503058545423"><title svg:width="500">This file is generated for XMind 8 Update 3 or later.</title></topic></topics></children></topic><title>Sheet 1</title></sheet></xmap-content>'''

DEFAULT_MANIFEST = {
    "file-entries": {
        "content.json": {},
        "metadata.json": {},
        "Thumbnails/thumbnail.png": {},
    }
}

DEFAULT_THEME = {
    "id": "6518e97a4149b5f96691ab3b5d",
    "importantTopic": {
        "type": "topic",
        "properties": {"fo:font-weight": "bold", "fo:color": "#333333", "svg:fill": "#FFFF00"},
    },
    "minorTopic": {
        "type": "topic",
        "properties": {"fo:font-weight": "bold", "fo:color": "#333333", "svg:fill": "#FFCB88"},
    },
    "expiredTopic": {
        "type": "topic",
        "properties": {"fo:font-style": "italic", "fo:text-decoration": " line-through"},
    },
    "centralTopic": {
        "properties": {"fo:font-family": "Open Sans", "fo:font-weight": "normal"},
        "styleId": "5a0ad466f338cd4e379fcbc6ac",
        "type": "topic",
    },
    "boundary": {
        "properties": {"fo:font-family": "Open Sans", "fo:font-weight": "normal"},
        "styleId": "6a197ea81a2b411f469fb810ca",
        "type": "boundary",
    },
    "floatingTopic": {
        "properties": {
            "fo:font-family": "Open Sans",
            "fo:font-weight": "normal",
            "fo:font-size": "12px",
        },
        "styleId": "d0ca7d1d8398da5d02d37b829c",
        "type": "topic",
    },
    "subTopic": {
        "properties": {
            "fo:font-weight": "normal",
            "fo:text-align": "left",
            "fo:font-family": "Open Sans",
        },
        "styleId": "a4d8a065efcaf0b96c645b7699",
        "type": "topic",
    },
    "mainTopic": {
        "properties": {"fo:font-weight": "normal", "fo:font-family": "Open Sans"},
        "styleId": "83fa7fc7525ad26c9e943af5c7",
        "type": "topic",
    },
    "calloutTopic": {
        "properties": {"fo:font-family": "Open Sans", "fo:font-weight": "normal"},
        "styleId": "8c0919e10e79743716f3c86f2d",
        "type": "topic",
    },
    "summaryTopic": {
        "properties": {
            "fo:font-family": "Open Sans",
            "fo:font-weight": "normal",
            "fo:font-size": "12px",
        },
        "styleId": "c788f68038baaa4d4edd199de8",
        "type": "topic",
    },
    "relationship": {
        "properties": {"fo:font-family": "Open Sans", "fo:font-weight": "normal"},
        "styleId": "28b8e3abe7aa107af82a98d69f",
        "type": "relationship",
    },
}

DEFAULT_STYLE = {"id": "75d1ec30-bcd7-4d95-b1e1-9f9942556ba7", "properties": {"svg:fill": "#FFFFFF"}}
HTML_TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"[ \t\r\n]+")
SHAPE_CLASS = {
    "capsule": "org.xmind.topicShape.roundedRect",
    "rounded-rect": "org.xmind.topicShape.roundedRect",
    "rect": "org.xmind.topicShape.rect",
}
FLAG_MARKERS = {
    1: "flag-red",
    2: "flag-yellow",
    3: "flag-green",
    4: "flag-blue",
    5: "flag-purple",
    6: "flag-gray",
}


@dataclass(frozen=True)
class ConversionResult:
    output: Path
    root_title: str
    topic_count: int
    first_level_count: int


def convert_lakeboard_to_xmind(
    source: str | Path,
    output: str | Path | None = None,
    *,
    template: str | Path | None = None,
    overwrite: bool = True,
    preserve_style: bool = True,
) -> ConversionResult:
    source_path = Path(source)
    output_path = source_path.with_suffix(".xmind") if output is None else Path(output)

    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}")

    lakeboard = json.loads(source_path.read_text(encoding="utf-8-sig"))
    root = _find_mindmap_root(lakeboard)
    template_data = _read_template(template)

    root_topic = _convert_topic(root, is_root=True, root_id=template_data["root_id"], preserve_style=preserve_style)
    boundaries = _convert_boundaries(lakeboard, root_topic) if preserve_style else []
    if boundaries:
        root_topic["boundaries"] = boundaries

    sheet = {
        "id": template_data["sheet_id"],
        "class": "sheet",
        "title": template_data["sheet_title"],
        "rootTopic": root_topic,
        "theme": template_data["theme"],
        "topicPositioning": "fixed",
        "style": template_data["style"],
    }

    content_json = json.dumps([sheet], ensure_ascii=False, separators=(",", ":"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("content.json", content_json.encode("utf-8"))
        archive.writestr("metadata.json", template_data["metadata_json"].encode("utf-8"))
        archive.writestr("manifest.json", template_data["manifest_json"].encode("utf-8"))
        archive.writestr("content.xml", template_data["content_xml"].encode("utf-8"))
        archive.writestr("Thumbnails/thumbnail.png", template_data["thumbnail_png"])

    return ConversionResult(
        output=output_path,
        root_title=root_topic["title"],
        topic_count=_count_topics(root_topic),
        first_level_count=len(root_topic.get("children", {}).get("attached", [])),
    )


def _find_mindmap_root(lakeboard: dict[str, Any]) -> dict[str, Any]:
    for node in lakeboard.get("diagramData", {}).get("body", []):
        if node.get("type") == "mindmap":
            return node
    raise ValueError("No mindmap root found in lakeboard file")


def _read_template(template: str | Path | None) -> dict[str, Any]:
    if template is None:
        return {
            "sheet_id": _compact_id(),
            "sheet_title": "画布 1",
            "root_id": _compact_id(),
            "theme": DEFAULT_THEME,
            "style": DEFAULT_STYLE,
            "metadata_json": "{}",
            "manifest_json": json.dumps(DEFAULT_MANIFEST, ensure_ascii=False, separators=(",", ":")),
            "content_xml": DEFAULT_CONTENT_XML,
            "thumbnail_png": b"",
        }

    template_path = Path(template)
    with zipfile.ZipFile(template_path, "r") as archive:
        content = json.loads(archive.read("content.json").decode("utf-8-sig"))
        sheet = content[0]
        root_topic = sheet.get("rootTopic", {})
        return {
            "sheet_id": sheet.get("id") or _compact_id(),
            "sheet_title": sheet.get("title") or "画布 1",
            "root_id": root_topic.get("id") or _compact_id(),
            "theme": sheet.get("theme") or DEFAULT_THEME,
            "style": sheet.get("style") or DEFAULT_STYLE,
            "metadata_json": _read_archive_text(archive, "metadata.json", "{}"),
            "manifest_json": _read_archive_text(
                archive,
                "manifest.json",
                json.dumps(DEFAULT_MANIFEST, ensure_ascii=False, separators=(",", ":")),
            ),
            "content_xml": _read_archive_text(archive, "content.xml", DEFAULT_CONTENT_XML),
            "thumbnail_png": _read_archive_bytes(archive, "Thumbnails/thumbnail.png", b""),
        }


def _convert_topic(
    node: dict[str, Any],
    *,
    is_root: bool = False,
    root_id: str | None = None,
    preserve_style: bool = True,
    inherited_edge_color: str | None = None,
) -> dict[str, Any]:
    topic: dict[str, Any] = {
        "id": root_id if is_root and root_id else str(uuid.uuid4()),
    }
    if is_root:
        topic["class"] = "topic"
    topic["title"] = _clean_title(node.get("html", ""))

    if preserve_style:
        style = _topic_style(node, inherited_edge_color=inherited_edge_color)
        if style:
            topic["style"] = style
        markers = _topic_markers(node)
        if markers:
            topic["markers"] = markers

    raw_children = [child for child in node.get("children") or [] if child]
    summary_children = [child for child in raw_children if child.get("abstract") is True]
    raw_children = [child for child in raw_children if child.get("abstract") is not True]

    if is_root:
        right_children = [child for child in raw_children if _quadrant(child) == 1]
        left_children = [child for child in raw_children if _quadrant(child) == 2]
        other_children = [child for child in raw_children if _quadrant(child) not in {1, 2}]
        raw_children = right_children + other_children + left_children
        right_count = len(right_children)
        topic["structureClass"] = "org.xmind.ui.map.unbalanced"
        topic["extensions"] = [
            {
                "content": [{"content": str(right_count), "name": "right-number"}],
                "provider": "org.xmind.ui.map.unbalanced",
            }
        ]

    edge_color = _color_value((node.get("treeEdge") or {}).get("stroke")) or inherited_edge_color
    children = [
        _convert_topic(child, preserve_style=preserve_style, inherited_edge_color=edge_color)
        for child in raw_children
    ]
    if children:
        topic["children"] = {"attached": children}
    if preserve_style and summary_children:
        _attach_summaries(topic, summary_children)
    return topic


def _attach_summaries(topic: dict[str, Any], summary_nodes: list[dict[str, Any]]) -> None:
    children = topic.setdefault("children", {})
    summary_topics = children.setdefault("summary", [])
    summaries = topic.setdefault("summaries", [])

    for node in summary_nodes:
        summary_topic_id = str(uuid.uuid4())
        summary_topics.append({"title": _clean_title(node.get("html", "")), "id": summary_topic_id})
        start = int(node.get("start", 0) or 0)
        end = int(node.get("end", start) or start) + 1
        edge_color = _color_value((node.get("treeEdge") or {}).get("stroke")) or "#007AC8"
        summaries.append(
            {
                "id": str(uuid.uuid4()),
                "range": f"({start},{end})",
                "topicId": summary_topic_id,
                "style": {
                    "id": str(uuid.uuid4()),
                    "properties": {
                        "line-color": edge_color,
                        "shape-class": "org.xmind.summaryShape.round",
                    },
                },
            }
        )


def _convert_boundaries(lakeboard: dict[str, Any], root_topic: dict[str, Any]) -> list[dict[str, Any]]:
    first_level = root_topic.get("children", {}).get("attached", [])
    if not first_level:
        return []

    total = len(first_level)
    right_count = int(root_topic.get("extensions", [{}])[0].get("content", [{}])[0].get("content", 0))
    boundaries: list[dict[str, Any]] = []

    for group in lakeboard.get("diagramData", {}).get("body", []):
        if group.get("type") != "group":
            continue
        title = _group_title(group)
        if not title:
            continue
        start, end = _boundary_range(right_count, total)
        boundaries.append(
            {
                "id": str(uuid.uuid4()),
                "title": title,
                "range": f"({start},{end})",
                "style": {
                    "id": str(uuid.uuid4()),
                    "properties": {"fo:color": "#E0E0E0"},
                },
            }
        )
    return boundaries


def _group_title(group: dict[str, Any]) -> str | None:
    titles = []
    for child in group.get("children") or []:
        title = _clean_title(child.get("html", ""))
        if title and title != "未命名主题":
            titles.append(title)
    return titles[-1] if titles else None


def _boundary_range(right_count: int, total: int) -> tuple[int, int]:
    if total <= 1:
        return 0, total
    if right_count and right_count < total:
        start = min(right_count + 1, total - 1)
        return start, total - 1
    return 0, total


def _topic_style(node: dict[str, Any], *, inherited_edge_color: str | None = None) -> dict[str, Any] | None:
    properties: dict[str, str] = {}
    border = node.get("border") or {}
    fill = _color_value(border.get("fill"))
    stroke = _color_value(border.get("stroke"))
    shape = border.get("shape")
    edge = node.get("treeEdge") or {}
    edge_color = _color_value(edge.get("stroke")) or inherited_edge_color
    edge_width = edge.get("stroke-width") or border.get("stroke-width")
    text_color = _color_value((node.get("defaultContentStyle") or {}).get("color"))

    if fill:
        properties["svg:fill"] = fill
    if stroke:
        properties["svg:stroke"] = stroke
    if shape in SHAPE_CLASS:
        properties["shape-class"] = SHAPE_CLASS[shape]
    if edge_color:
        properties["line-color"] = edge_color
    if edge_width:
        properties["line-width"] = f"{edge_width}pt"
    if text_color:
        properties["fo:color"] = text_color
    if "font-weight:bold" in (node.get("html") or "").replace(" ", ""):
        properties["fo:font-weight"] = "bold"

    if not properties:
        return None
    return {"id": str(uuid.uuid4()), "properties": properties}


def _topic_markers(node: dict[str, Any]) -> list[dict[str, str]]:
    icons = node.get("icons") or {}
    markers: list[dict[str, str]] = []
    priority = icons.get("priority")
    if isinstance(priority, int):
        markers.append({"markerId": f"priority-{priority + 1}"})
    flag = icons.get("flag")
    if isinstance(flag, int) and flag in FLAG_MARKERS:
        markers.append({"markerId": FLAG_MARKERS[flag]})
    return markers


def _quadrant(node: dict[str, Any]) -> int | None:
    quadrant = (node.get("layout") or {}).get("quadrant")
    return quadrant if isinstance(quadrant, int) else None


def _color_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or value.lower() == "transparent":
        return None
    if value.startswith("rgb("):
        numbers = [int(part.strip()) for part in value[4:-1].split(",")]
        if len(numbers) == 3:
            return "#" + "".join(f"{number:02X}" for number in numbers)
    return value


def _clean_title(value: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", value or "", flags=re.IGNORECASE)
    text = HTML_TAG_RE.sub("", text)
    text = html.unescape(text)
    text = text.replace("\u200b", "").replace("\ufeff", "").replace("\xa0", " ")
    text = SPACE_RE.sub(" ", text).strip()
    return text or "未命名主题"


def _count_topics(topic: dict[str, Any]) -> int:
    children = topic.get("children", {})
    return (
        1
        + sum(_count_topics(child) for child in children.get("attached", []))
        + len(children.get("summary", []))
    )


def _compact_id() -> str:
    return uuid.uuid4().hex[:26]


def _read_archive_text(archive: zipfile.ZipFile, name: str, default: str) -> str:
    try:
        return archive.read(name).decode("utf-8-sig")
    except KeyError:
        return default


def _read_archive_bytes(archive: zipfile.ZipFile, name: str, default: bytes) -> bytes:
    try:
        return archive.read(name)
    except KeyError:
        return default
