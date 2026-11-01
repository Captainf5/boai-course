"""Combined mobile packs retain navigable links from nested source files."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'delivery-pack/scripts'))
import build_mobile_pack

class MobileLinkTests(unittest.TestCase):
    def test_all_generated_relative_markdown_links_resolve(self):
        import re
        from urllib.parse import urlsplit, unquote
        for spec in build_mobile_pack.pack_specs():
            body = build_mobile_pack.render_sources(spec['title'], spec['guidance'], spec['sources'])
            for target in re.findall(r'\]\(([^\n)]+)\)', body):
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                resolved = spec['output'].parent / unquote(url.path)
                self.assertTrue(resolved.exists(), f"{spec['key']}: {target}")

if __name__ == '__main__':
    unittest.main()
