import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "scripts/getnote_readonly.py"
spec = importlib.util.spec_from_file_location("reader", path)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


class ReaderTests(unittest.TestCase):
    def test_pages_preserve_large_ids_and_deduplicate(self):
        note = {"id": 1900000000000000123, "title": "数据分析", "created_at": "2026-10-31T10:00:00+08:00"}
        pages = iter([{"notes": [note], "has_more": True, "next_cursor": 9},
                      {"notes": [note], "has_more": False}])
        calls = []
        def fetch(path, params):
            calls.append(params)
            return next(pages)
        result = reader.find_notes(fetch, "数据分析")
        self.assertTrue(result["complete"])
        self.assertEqual(result["notes"][0]["id"], "1900000000000000123")
        self.assertEqual(len(result["notes"]), 1)
        self.assertEqual(calls[1], {"cursor": "9"})

    def test_partial_search_not_claimed_complete(self):
        fetch = lambda p, q: {"notes": [], "has_more": True, "next_cursor": "next"}
        self.assertFalse(reader.find_notes(fetch, "课", max_pages=1)["complete"])
        self.assertEqual(reader.find_notes(fetch, "课")["reason"], "repeated_cursor")

    def test_missing_pagination_flag_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing_pagination"):
            reader.find_notes(lambda p, q: {"notes": []}, "课")

    def test_date_and_keyword_filter(self):
        data = {"notes": [{"id": "1", "title": "数据课", "created_at": "2026-10-01"},
                          {"id": "2", "title": "数据课", "created_at": "2026-09-30"},
                          {"id": "3", "title": "销售课", "created_at": "2026-10-01"}],
                "has_more": False}
        result = reader.find_notes(lambda p, q: data, "数据", "2026-10-01", "2026-10-31")
        self.assertEqual([n["id"] for n in result["notes"]], ["1"])

    def test_detail_preserves_raw_fields_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "note.json"
            note = {"audio": {"original": "模拟原文"}, "content": "模拟摘要"}
            reader.write_detail({"note": note}, path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), note)
            with self.assertRaises(FileExistsError):
                reader.write_detail({"note": {}}, path)

    def test_api_false_even_http_200_is_rejected(self):
        response = io.StringIO('{"success":false,"data":{}}')
        with patch.object(reader.urllib.request, "build_opener") as opener:
            opener.return_value.open.return_value = response
            with self.assertRaisesRegex(ValueError, "api_rejected_request"):
                reader.request("/resource/note/list", {}, "fake-id", "fake-key")

    def test_no_disk_fallback_when_no_injected_credentials(self):
        output = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), patch.object(reader, "request") as request:
            with contextlib.redirect_stdout(output):
                self.assertEqual(reader.main(["check"]), 1)
            request.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["status"], "injected_credentials_unavailable")

    def test_failure_does_not_leak_credential_in_exception(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"GETNOTE_CLIENT_ID": "test-id", "GETNOTE_API_KEY": "test-secret"}):
            with patch.object(reader, "request", side_effect=RuntimeError("test-secret")):
                with contextlib.redirect_stdout(output):
                    self.assertEqual(reader.main(["check"]), 1)
        self.assertNotIn("test-secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
