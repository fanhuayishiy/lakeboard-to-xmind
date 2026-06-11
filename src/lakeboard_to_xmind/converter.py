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
) -> ConversionResult:
    source_path = Path(source)
    if output is None:
        output_path = source_path.with_suffix(".xmind")
    else:
        output_path = Path(output)

    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}")

    lakeboard = json.loads(source_path.read_text(encoding="utf-8-sig"))
    root = _find_mindmap_root(lakeboard)
    template_data = _read_template(template)

    root_topic = _convert_topic(root, is_root=True, root_id=template_data["root_id"])
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
    metadata_json = template_data["metadata_json"]
    manifest_json = template_data["manifest_json"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("content.json", content_json.encode("utf-8"))
        archive.writestr("metadata.json", metadata_json.encode("utf-8"))
        archive.writestr("manifest.json", manifest_json.encode("utf-8"))
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


def _convert_topic(node: dict[str, Any], *, is_root: bool = False, root_id: str | None = None) -> dict[str, Any]:
    topic: dict[str, Any] = {
        "id": root_id if is_root and root_id else str(uuid.uuid4()),
    }
    if is_root:
        topic["class"] = "topic"
    topic["title"] = _clean_title(node.get("html", ""))

    if is_root:
        topic["structureClass"] = "org.xmind.ui.map.unbalanced"
        topic["extensions"] = [
            {
                "content": [{"content": "0", "name": "right-number"}],
                "provider": "org.xmind.ui.map.unbalanced",
            }
        ]

    children = [_convert_topic(child) for child in node.get("children") or [] if child]
    if children:
        topic["children"] = {"attached": children}
    return topic


def _clean_title(value: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", value or "", flags=re.IGNORECASE)
    text = HTML_TAG_RE.sub("", text)
    text = html.unescape(text)
    text = text.replace("\u200b", "").replace("\ufeff", "").replace("\xa0", " ")
    text = SPACE_RE.sub(" ", text).strip()
    return text or "未命名主题"


def _count_topics(topic: dict[str, Any]) -> int:
    return 1 + sum(_count_topics(child) for child in topic.get("children", {}).get("attached", []))


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
