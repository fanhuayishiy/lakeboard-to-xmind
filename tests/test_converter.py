from __future__ import annotations

import json
import unittest
import zipfile
from pathlib import Path

from lakeboard_to_xmind import convert_lakeboard_to_xmind, convert_xmind_to_lakeboard


class ConverterTests(unittest.TestCase):
    def test_convert_fixture_without_template(self) -> None:
        fixtures = Path(__file__).resolve().parent / "fixtures"
        source = fixtures / "sample.lakeboard"
        output = fixtures / "sample-output.xmind"
        if output.exists():
            output.unlink()

        try:
            result = convert_lakeboard_to_xmind(source, output)

            self.assertEqual(result.root_title, "web端")
            self.assertEqual(result.topic_count, 7)
            self.assertEqual(result.first_level_count, 2)
            self.assertTrue(output.exists())

            content = _read_xmind_content(output)
            root = content[0]["rootTopic"]
            self.assertEqual(root["title"], "web端")
            self.assertEqual(root["structureClass"], "org.xmind.ui.map.unbalanced")
            self.assertEqual(root["extensions"][0]["content"][0]["content"], "1")
            self.assertEqual(len(root["children"]["attached"]), 2)

            right = root["children"]["attached"][0]
            left = root["children"]["attached"][1]
            self.assertEqual(right["title"], "右侧主题")
            self.assertEqual(left["title"], "左侧主题")
            self.assertEqual(right["style"]["properties"]["svg:fill"], "#FAEDF6")
            self.assertEqual(right["style"]["properties"]["line-color"], "#E482D4")
            self.assertEqual(right["markers"][0]["markerId"], "priority-1")
            self.assertEqual(left["style"]["properties"]["svg:fill"], "#E9F7E9")
            self.assertEqual(left["markers"][0]["markerId"], "flag-green")
            self.assertEqual(right["children"]["attached"][0]["title"], "关联展区")
            self.assertEqual(right["children"]["attached"][1]["title"], "二维码")
            self.assertEqual(right["children"]["summary"][0]["title"], "概要")
            self.assertEqual(right["summaries"][0]["range"], "(0,2)")
            self.assertEqual(right["summaries"][0]["topicId"], right["children"]["summary"][0]["id"])
            self.assertEqual(root["boundaries"][0]["title"], "外框备注")
            self.assertEqual(root["boundaries"][0]["range"], "(1,1)")
        finally:
            if output.exists():
                output.unlink()

    def test_roundtrip_xmind_to_lakeboard(self) -> None:
        fixtures = Path(__file__).resolve().parent / "fixtures"
        source = fixtures / "sample.lakeboard"
        xmind = fixtures / "roundtrip.xmind"
        lakeboard = fixtures / "roundtrip.lakeboard"
        for path in (xmind, lakeboard):
            if path.exists():
                path.unlink()

        try:
            convert_lakeboard_to_xmind(source, xmind)
            result = convert_xmind_to_lakeboard(xmind, lakeboard)

            self.assertEqual(result.root_title, "web端")
            self.assertEqual(result.topic_count, 7)
            self.assertEqual(result.first_level_count, 2)
            data = json.loads(lakeboard.read_text(encoding="utf-8"))
            root = next(item for item in data["diagramData"]["body"] if item.get("type") == "mindmap")
            groups = [item for item in data["diagramData"]["body"] if item.get("type") == "group"]

            self.assertEqual(root["children"][0]["html"], "右侧主题")
            self.assertEqual(root["children"][0]["layout"]["quadrant"], 1)
            self.assertEqual(root["children"][1]["html"], "左侧主题")
            self.assertEqual(root["children"][1]["layout"]["quadrant"], 2)
            self.assertEqual(root["children"][0]["border"]["fill"], "#FAEDF6")
            self.assertEqual(root["children"][0]["treeEdge"]["stroke"], "#E482D4")
            self.assertEqual(root["children"][0]["icons"]["priority"], 0)
            self.assertEqual(root["children"][1]["icons"]["flag"], 3)
            summary = root["children"][0]["children"][2]
            self.assertTrue(summary["abstract"])
            self.assertEqual(summary["html"], '<span style="font-weight:bold;">概要</span>')
            self.assertEqual(summary["start"], 0)
            self.assertEqual(summary["end"], 2)
            self.assertEqual(groups[0]["children"][1]["html"], '<div style="text-align:center;"><span style="font-weight:bold; font-size:12px;">外框备注</span></div>')
        finally:
            for path in (xmind, lakeboard):
                if path.exists():
                    path.unlink()


def _read_xmind_content(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        assert "content.json" in names
        assert "metadata.json" in names
        assert "manifest.json" in names
        assert "content.xml" in names
        assert "Thumbnails/thumbnail.png" in names
        content_text = archive.read("content.json").decode("utf-8")
        assert content_text.startswith("[")
        return json.loads(content_text)


if __name__ == "__main__":
    unittest.main()


