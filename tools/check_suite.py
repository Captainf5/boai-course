"""Check the public course package's entry points and local Markdown links."""
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
NAMES = {'boai-course-value', 'boai-kegang', 'boai-questionnaire', 'boai-ppt',
         'boai-showcase', 'boai-zengxiao-data-case', 'boai-recording-review'}

def main():
    assert {p.parent.name for p in ROOT.glob('*/SKILL.md')} == NAMES
    for name in NAMES:
        text = (ROOT / name / 'SKILL.md').read_text(encoding='utf-8-sig')
        assert re.search(r'^name:\s*' + re.escape(name) + r'\s*$', text, re.M), name
        assert (ROOT / name / 'README.md').is_file(), name
    count = 0
    for path in ROOT.rglob('*.md'):
        # Historical local files are explicitly excluded from the public tree.
        if any(part in path.parts for part in ('.git', 'reference-pack', 'posters')):
            continue
        for target in re.findall(r'\]\(([^\n)]+)\)', path.read_text(encoding='utf-8-sig')):
            url = urlsplit(target.strip('<>'))
            if url.scheme or url.netloc or not url.path:
                continue
            count += 1
            assert (path.parent / unquote(url.path)).exists(), f'{path}: {target}'
    print(f'PASS: 7 Skill entries; {count} local Markdown links')

if __name__ == '__main__':
    main()
