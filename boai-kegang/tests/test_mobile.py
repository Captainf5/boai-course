import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pypdfium2


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "cloud", ROOT / "delivery-pack/scripts/cloud_render.py"
)
cloud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cloud)


class MobileInputTests(unittest.TestCase):
    def event(self):
        md = (
            ROOT / "outputs/catalog/博AI增效-2D-10倍职场办公_6X畅销版.md"
        ).read_text(encoding="utf-8")
        return {
            "repository": {"owner": {"login": "owner"}},
            "sender": {"login": "owner"},
            "issue": {
                "number": 123,
                "user": {"login": "owner"},
                "title": "[课纲排版] test",
                "body": (
                    "### 课纲 Markdown\n\n"
                    + md
                    + "\n\n### 发布确认\n\n- [X] "
                    + cloud.ACK
                ),
            },
        }

    def test_preserves_complete_markdown(self):
        text, number = cloud.issue_markdown(self.event())
        self.assertIn("第二天", text)
        self.assertIn("培训准备", text)
        self.assertEqual(number, 123)

    def test_rejects_other_user(self):
        event = self.event()
        event["sender"]["login"] = "stranger"
        with self.assertRaises(ValueError):
            cloud.issue_markdown(event)

    def test_requires_public_ack(self):
        event = self.event()
        event["issue"]["body"] = event["issue"]["body"].replace("[X]", "[ ]")
        with self.assertRaises(ValueError):
            cloud.issue_markdown(event)

    def test_markdown_is_not_executed(self):
        event = self.event()
        event["issue"]["body"] = event["issue"]["body"].replace(
            "## 八、", "$(touch SHOULD_NOT_EXIST)\n\n## 八、"
        )
        text, _ = cloud.issue_markdown(event)
        self.assertIn("$(touch SHOULD_NOT_EXIST)", text)
        self.assertFalse((ROOT / "SHOULD_NOT_EXIST").exists())

    def test_rejects_one_line_request(self):
        event = self.event()
        event["issue"]["body"] = (
            "### 课纲 Markdown\n\n# 帮我做课纲\n\n"
            "### 发布确认\n\n- [X] " + cloud.ACK
        )
        with self.assertRaises(ValueError):
            cloud.issue_markdown(event)

    def test_validates_same_course_contract_before_layout(self):
        text, _ = cloud.issue_markdown(self.event())
        checks = cloud.validate_course_markdown(text)
        self.assertEqual(checks["title_duration"], "2D")
        self.assertEqual(checks["required_sections"], 8)
        self.assertGreater(checks["modules"], 0)
        self.assertEqual(checks["modules"], checks["schedule_rows"])

    def test_rejects_missing_module_field(self):
        text, _ = cloud.issue_markdown(self.event())
        with self.assertRaisesRegex(ValueError, "缺少字段"):
            cloud.validate_course_markdown(text.replace("产出物：", "课堂作品：", 1))

    def test_rejects_naked_or_legacy_title(self):
        text, _ = cloud.issue_markdown(self.event())
        first_line = text.splitlines()[0]
        for invalid_title in (
            "# 数智强能专题——智能体的场景化探索",
            "# 博AI增效-2D-10倍职场办公_6X畅销版",
        ):
            with self.subTest(title=invalid_title):
                with self.assertRaisesRegex(ValueError, "课纲标题必须使用"):
                    cloud.validate_course_markdown(
                        text.replace(first_line, invalid_title, 1)
                    )

    def test_accepts_exact_opc_title_exception(self):
        text, _ = cloud.issue_markdown(self.event())
        first_line = text.splitlines()[0]
        checks = cloud.validate_course_markdown(
            text.replace(first_line, cloud.OPC_TITLE, 1)
        )
        self.assertEqual(checks["title_duration"], "OPC")

    def test_accepts_spaced_module_number(self):
        text, _ = cloud.issue_markdown(self.event())
        spaced = text.replace("**模块1：", "**模块 1：", 1)
        checks = cloud.validate_course_markdown(spaced)
        self.assertGreater(checks["modules"], 0)

    def test_docx_audit_confirms_template_and_letter_geometry(self):
        layout = cloud.load_layout_module()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "course.docx"
            layout.convert_md_to_docx(
                ROOT / "outputs/catalog/博AI增效-1D-10倍职场办公_6X畅销版.md",
                output,
            )
            checks = cloud.audit_docx(output)
        self.assertTrue(checks["template_parts_preserved"])
        self.assertEqual(checks["page_size_points"], [612, 792])
        self.assertEqual(checks["orphan_images"], [])

    def test_pdf_audit_rejects_a_blank_page(self):
        class TextPage:
            def __init__(self, text):
                self.text = text

            def get_text_range(self):
                return self.text

        class Page:
            def __init__(self, text):
                self.text = text

            def get_textpage(self):
                return TextPage(self.text)

        with patch.object(
            pypdfium2,
            "PdfDocument",
            return_value=[Page("课程正文"), Page("  \n")],
        ):
            with self.assertRaisesRegex(ValueError, "纯空白页"):
                cloud.audit_pdf(Path("unused.pdf"))


if __name__ == "__main__":
    unittest.main()
