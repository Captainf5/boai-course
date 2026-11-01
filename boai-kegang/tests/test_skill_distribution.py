import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "delivery-pack/scripts"
CATALOG = ROOT / "outputs/catalog"
COURSE_MANIFEST = ROOT / "references/CURRENT-COURSE-PACK.json"
sys.path.insert(0, str(SCRIPTS))

import build_mobile_pack
import build_skill_package
import layout_identity


EXPECTED_FAMILIES = {
    "office-management": 5,
    "marketing-agent": 4,
    "industry": 4,
}
PACKAGE_OUTPUTS = {
    "full": build_skill_package.OUTPUT,
    "authoring": build_skill_package.AUTHORING_OUTPUT,
}


def relative(path):
    return path.relative_to(ROOT).as_posix()


def canonical_text(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.course_manifest = json.loads(COURSE_MANIFEST.read_text(encoding="utf-8"))
        cls.courses = cls.course_manifest["courses"]
        cls.catalog_paths = {relative(path) for path in CATALOG.glob("*.md")}

    def test_current_course_manifest_is_complete_and_partitioned(self):
        self.assertEqual(self.course_manifest["reference_basis"], "outputs/catalog")
        self.assertEqual(len(self.courses), 13)
        self.assertEqual(len({entry["id"] for entry in self.courses}), 13)
        self.assertEqual(len({entry["title"] for entry in self.courses}), 13)
        self.assertEqual(len({entry["path"] for entry in self.courses}), 13)
        self.assertEqual(
            Counter(entry["family"] for entry in self.courses),
            Counter(EXPECTED_FAMILIES),
        )
        self.assertEqual({entry["path"] for entry in self.courses}, self.catalog_paths)

        for entry in self.courses:
            course_path = ROOT / entry["path"]
            first_line = canonical_text(course_path).splitlines()[0]
            self.assertEqual(first_line, "# " + entry["title"], entry["path"])
            if entry["id"] == "opc-half-day":
                self.assertEqual(entry["title"], "博AI增效-OPC实战工作坊")
            else:
                filename_prefix = f"博AI增效-{entry['duration']}-"
                self.assertTrue(course_path.stem.startswith(filename_prefix), entry["path"])
                self.assertEqual(
                    entry["title"],
                    f"【博AI增效-{entry['duration']}】"
                    + course_path.stem.removeprefix(filename_prefix),
                    entry["path"],
                )
            self.assertEqual(
                entry["sha256"],
                hashlib.sha256(canonical_text(course_path).encode("utf-8")).hexdigest(),
                entry["path"],
            )

    def test_mobile_core_and_direction_packs_are_complete_and_bounded(self):
        build_mobile_pack.build(check=True)
        specs = {spec["key"]: spec for spec in build_mobile_pack.pack_specs()}
        self.assertEqual(
            set(specs),
            {"core", "office-management", "marketing-agent", "industry", "full"},
        )

        rendered = build_mobile_pack.rendered_packs()
        core_text = rendered[specs["core"]["output"]]
        core_sources = {relative(path) for path in specs["core"]["sources"]}
        self.assertNotIn("MOBILE-WORKFLOW.md", core_sources)
        self.assertNotIn("references/README.md", core_sources)
        marketing_sources = {
            relative(path) for path in specs["marketing-agent"]["sources"]
        }
        self.assertNotIn("references/03-营销内容-经典母版.md", marketing_sources)
        distributed_courses = []
        for family, expected_count in EXPECTED_FAMILIES.items():
            spec = specs[family]
            route_courses = [
                relative(path)
                for path in spec["sources"]
                if relative(path).startswith("outputs/catalog/")
            ]
            self.assertEqual(len(route_courses), expected_count, family)
            self.assertTrue(
                all(
                    next(entry for entry in self.courses if entry["path"] == path)["family"]
                    == family
                    for path in route_courses
                ),
                family,
            )
            distributed_courses.extend(route_courses)
            route_text = rendered[spec["output"]]
            # v1.8.1 preserves both clients' rules (PCR and customization guidance).
            # This is a packaging growth budget, not a mobile client capacity claim.
            self.assertLess(len(core_text), 25_000, family)
            self.assertLess(len(core_text) + len(route_text), 50_000, family)

        self.assertEqual(Counter(distributed_courses), Counter(self.catalog_paths))

    def test_mobile_manifest_hashes_match_rendered_packs_and_sources(self):
        build_mobile_pack.build(check=True)
        manifest = json.loads(build_mobile_pack.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        self.assertEqual(manifest["reference_basis"], "outputs/catalog")
        self.assertEqual(
            manifest["basis_sha256"], build_mobile_pack.course_basis_sha256()
        )
        self.assertEqual(
            manifest["layout_basis_sha256"],
            layout_identity.layout_basis_sha256(),
        )

        rendered = build_mobile_pack.rendered_packs()
        self.assertEqual(set(manifest["packs"]), {output.name for output in rendered})
        for output, expected_text in rendered.items():
            pack = manifest["packs"][output.name]
            actual_text = output.read_text(encoding="utf-8")
            self.assertEqual(actual_text, expected_text, output.name)
            self.assertEqual(pack["characters"], len(expected_text), output.name)
            self.assertEqual(
                pack["sha256"],
                hashlib.sha256(expected_text.encode("utf-8")).hexdigest(),
                output.name,
            )
            for source in pack["sources"]:
                source_path = ROOT / source["path"]
                self.assertEqual(
                    source["sha256"],
                    hashlib.sha256(canonical_text(source_path).encode("utf-8")).hexdigest(),
                    source["path"],
                )

    def test_full_and_authoring_zips_match_sources_and_manifests(self):
        build_skill_package.build(check=True)
        for flavor, output in PACKAGE_OUTPUTS.items():
            expected_paths = [relative(path) for path in build_skill_package.source_files(flavor)]
            self.assertEqual(expected_paths, sorted(expected_paths), flavor)

            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertEqual(len(names), len(set(names)), flavor)
                self.assertTrue(
                    all(
                        name.startswith("boai-kegang/")
                        and ".." not in Path(name).parts
                        for name in names
                    ),
                    flavor,
                )
                self.assertFalse(any("/mobile/" in name for name in names), flavor)
                self.assertFalse(
                    any(
                        "/reference-pack/" in name
                        or "/.git/" in name
                        or name.endswith(".pdf")
                        for name in names
                    ),
                    flavor,
                )

                catalog_names = [
                    name
                    for name in names
                    if name.startswith("boai-kegang/outputs/catalog/")
                    and name.endswith(".md")
                ]
                self.assertEqual(len(catalog_names), 13, flavor)
                self.assertEqual(
                    {name.removeprefix("boai-kegang/") for name in catalog_names},
                    self.catalog_paths,
                    flavor,
                )

                manifest = json.loads(archive.read("boai-kegang/PACKAGE-MANIFEST.json"))
                self.assertEqual(manifest["version"], (ROOT / "VERSION").read_text(encoding="utf-8").strip(), flavor)
                self.assertEqual(manifest["flavor"], flavor)
                self.assertEqual(manifest["reference_basis"], "outputs/catalog")
                self.assertEqual(
                    manifest["basis_sha256"],
                    build_mobile_pack.course_basis_sha256(),
                    flavor,
                )
                self.assertEqual(
                    manifest["layout_basis_sha256"],
                    layout_identity.layout_basis_sha256(),
                    flavor,
                )
                self.assertTrue(manifest["capabilities"]["markdown_authoring"], flavor)
                self.assertTrue(manifest["capabilities"]["canonical_cloud_render"], flavor)
                self.assertEqual(
                    manifest["capabilities"]["embedded_word_layout_runtime"],
                    flavor == "full",
                    flavor,
                )
                self.assertEqual(
                    manifest["capabilities"]["cross_device_fixed_layout"],
                    "download_the_same_cloud_pdf",
                    flavor,
                )
                if flavor == "full":
                    self.assertIn("完整交付包", manifest["package_label"])
                else:
                    self.assertIn("纯写稿精简包", manifest["package_label"])
                self.assertEqual(set(manifest["files"]), set(expected_paths), flavor)
                for path, digest in manifest["files"].items():
                    self.assertEqual(
                        hashlib.sha256(archive.read("boai-kegang/" + path)).hexdigest(),
                        digest,
                        f"{flavor}: {path}",
                    )

    def test_normal_skill_build_regenerates_mobile_packs(self):
        with patch.object(build_mobile_pack, "build") as mobile_build, patch.object(
            build_skill_package, "_write"
        ):
            build_skill_package.build(check=False)
        mobile_build.assert_called_once_with(check=False)

    def test_authoring_zip_excludes_layout_runtime_assets(self):
        build_skill_package.build(check=True)
        with zipfile.ZipFile(build_skill_package.AUTHORING_OUTPUT) as archive:
            names = archive.namelist()
            self.assertFalse(
                any(
                    "/delivery-pack/scripts/" in name
                    or "/delivery-pack/images/" in name
                    or name.endswith("/delivery-pack/课纲模板.docx")
                    for name in names
                )
            )

    def test_full_zip_contains_layout_assets_and_can_render_after_unpack(self):
        build_skill_package.build(check=True)
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(build_skill_package.OUTPUT) as archive:
                names = set(archive.namelist())
                for required in [
                    "boai-kegang/delivery-pack/课纲模板.docx",
                    "boai-kegang/delivery-pack/scripts/课纲排版toWord带图版.py",
                    "boai-kegang/delivery-pack/scripts/layout_identity.py",
                    "boai-kegang/delivery-pack/images/讲师照片1.png",
                    "boai-kegang/delivery-pack/requirements.txt",
                ]:
                    self.assertIn(required, names)
                archive.extractall(tmp)

            package = Path(tmp) / "boai-kegang"
            renderer_path = package / "delivery-pack/scripts/课纲排版toWord带图版.py"
            spec = importlib.util.spec_from_file_location("portable_layout", renderer_path)
            renderer = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(renderer)
            for days in (1, 2):
                source = package / f"outputs/catalog/博AI增效-{days}D-10倍职场办公_6X畅销版.md"
                target = Path(tmp) / f"{days}D.docx"
                renderer.convert_md_to_docx(source, target)
                self.assertGreater(target.stat().st_size, 10_000)

            entry = (package / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: boai-kegang", entry)
            self.assertNotRegex(entry, r"[CDE]:[/\\]")

    def test_default_links_do_not_misrepresent_the_authoring_package(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cross_platform = (ROOT / "CROSS-PLATFORM.md").read_text(encoding="utf-8")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("默认下载[完整便携Skill包]", readme)
        self.assertIn("默认下载[完整Skill包]", cross_platform)
        self.assertIn("课程交付默认导入[完整Skill包]", cross_platform)
        self.assertIn("纯写稿精简包", readme)
        self.assertIn("不含Word模板、图片、Python脚本", readme)
        self.assertIn("同一次运行的同一PDF", skill)


if __name__ == "__main__":
    unittest.main()
