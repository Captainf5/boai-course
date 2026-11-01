"""Validate the single course title across Markdown, Word, and PDF artifacts."""

import argparse
import sys
from pathlib import Path

from docx import Document


IMAGE_SUFFIX = '_带图'


def markdown_title(path: Path) -> str:
    titles = [line[2:].strip() for line in path.read_text(encoding='utf-8-sig').splitlines()
              if line.startswith('# ')]
    if len(titles) != 1:
        raise ValueError(f'Markdown 必须且只能有一个 H1，当前为 {len(titles)} 个')
    return titles[0]


def artifact_title_from_filename(path: Path) -> str:
    stem = path.stem
    return stem[:-len(IMAGE_SUFFIX)] if stem.endswith(IMAGE_SUFFIX) else stem


def assert_same(label: str, actual: str, expected: str) -> None:
    if actual != expected:
        raise ValueError(f'{label} 不一致：期望“{expected}”，实际“{actual}”')


def main() -> int:
    parser = argparse.ArgumentParser(description='校验课纲标题单一来源')
    parser.add_argument('--input', required=True, help='课纲 Markdown 路径')
    parser.add_argument('--docx', required=True, help='Word 路径')
    parser.add_argument('--pdf', help='PDF 路径（可选）')
    args = parser.parse_args()

    try:
        md_path = Path(args.input)
        docx_path = Path(args.docx)
        expected = markdown_title(md_path)
        document = Document(docx_path)
        visible_title = next((p.text.strip() for p in document.paragraphs if p.text.strip()), '')
        metadata_title = document.core_properties.title.strip()

        assert_same('Markdown 文件名', artifact_title_from_filename(md_path), expected)
        assert_same('Word 首页 H1', visible_title, expected)
        assert_same('Word 文档属性 Title', metadata_title, expected)
        assert_same('Word 文件名', artifact_title_from_filename(docx_path), expected)

        if args.pdf:
            assert_same('PDF 文件名', artifact_title_from_filename(Path(args.pdf)), expected)

        print(f'TITLE_SYNC_OK: {expected}')
        return 0
    except Exception as exc:
        print(f'TITLE_SYNC_ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
