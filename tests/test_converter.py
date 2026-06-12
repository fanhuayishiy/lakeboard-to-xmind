from __future__ import annotations

import json
import unittest
import zipfile
from pathlib import Path

from lakeboard_to_xmind import convert_lakeboard_to_xmind


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
            self.assertEqual(result.topic_count, 6)
            self.assertEqual(result.first_level_count, 2)
            self.assertTrue(output.exists())

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("content.json", names)
                self.assertIn("metadata.json", names)
                self.assertIn("manifest.json", names)
                self.assertIn("content.xml", names)
                self.assertIn("Thumbnails/thumbnail.png", names)
                content_text = archive.read("content.json").decode("utf-8")
                self.assertTrue(content_text.startswith("["))
                content = json.loads(content_text)

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
        finally:
            if output.exists():
                output.unlink()


if __name__ == "__main__":
    unittest.main()
