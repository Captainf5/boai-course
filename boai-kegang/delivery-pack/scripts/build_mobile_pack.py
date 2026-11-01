"""Build mobile authoring packs from the same authoritative Skill sources."""

import argparse
import hashlib
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
MOBILE = ROOT / "mobile"
MANIFEST_PATH = MOBILE / "PACK-MANIFEST.json"
FULL_OUTPUT = MOBILE / "博AI课纲-手机加载包.md"

CORE_RELATIVE = [
    "SKILL.md",
    "WORKFLOW.md",
    "OUTPUT-FORMAT.md",
    "CHECKLIST.md",
    "references/CURRENT-COURSE-PACK.md",
    "references/STYLE-BENCHMARK.md",
    "references/01-三天综合办公-语言标杆.md",
    "references/LECTURER.md",
    "references/COURSE-CATALOG.md",
    "大展宏图方法论.md",
]

ROUTE_EXTRAS = {
    "office-management": [
        "references/WORKBUDDY-COURSE.md",
        "references/08-HR与WorkBuddy-两天.md",
    ],
    "marketing-agent": [],
    "industry": [
        "references/WORKBUDDY-COURSE.md",
        "references/COMMUNICATIONS-SERIES.md",
    ],
}

ROUTE_OUTPUTS = {
    "office-management": MOBILE / "博AI课纲-手机参考包-通用办公与管理.md",
    "marketing-agent": MOBILE / "博AI课纲-手机参考包-营销增长与智能体.md",
    "industry": MOBILE / "博AI课纲-手机参考包-行业专项.md",
}

ROUTE_TITLES = {
    "office-management": "博AI课纲·手机参考包｜通用办公与管理",
    "marketing-agent": "博AI课纲·手机参考包｜营销增长与智能体",
    "industry": "博AI课纲·手机参考包｜行业专项",
}

ROUTE_GUIDANCE = {
    "office-management": "与手机核心规则包一起加载。适用于职场办公、数据、高管、HR与飞书定制。",
    "marketing-agent": "与手机核心规则包一起加载。适用于营销内容、业务智能体、自然语言开发与OPC。",
    "industry": "与手机核心规则包一起加载。适用于电网、电力及通讯行业定制。",
}


def _path(relative):
    path = ROOT / relative
    if (
        not path.is_file()
        or path.is_symlink()
        or not path.resolve().is_relative_to(ROOT.resolve())
    ):
        raise ValueError(f"缺失或不安全的手机包来源: {relative}")
    return path


def _unique(paths):
    result = []
    seen = set()
    for path in paths:
        path = path.resolve()
        if path not in seen:
            result.append(path)
            seen.add(path)
    return result


def current_course_manifest():
    manifest = json.loads(
        _path("references/CURRENT-COURSE-PACK.json").read_text(encoding="utf-8")
    )
    courses = manifest.get("courses")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("reference_basis") != "outputs/catalog"
        or not isinstance(courses, list)
    ):
        raise ValueError("当前课程包清单格式错误")
    required = {
        "id",
        "family",
        "title",
        "path",
        "sha256",
        "duration",
        "primary_tool",
    }
    for entry in courses:
        if not isinstance(entry, dict) or not required.issubset(entry):
            raise ValueError("当前课程包条目缺少必要字段")
        course_path = _path(entry["path"])
        digest = hashlib.sha256(
            _canonical_text(course_path).encode("utf-8")
        ).hexdigest()
        if entry["sha256"] != digest:
            raise ValueError(f"当前课纲SHA256已变化，请更新清单: {entry['path']}")
    return manifest


def current_course_entries():
    return current_course_manifest()["courses"]


def course_basis_sha256():
    """Hash current-course metadata plus all 13 normalized course bodies."""
    manifest = current_course_manifest()
    basis = {
        "schema_version": manifest["schema_version"],
        "reference_basis": manifest["reference_basis"],
        "courses": manifest["courses"],
    }
    payload = json.dumps(
        basis,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def current_course_paths(family=None):
    entries = current_course_entries()
    if family is not None:
        entries = [entry for entry in entries if entry.get("family") == family]
    return [_path(entry["path"]) for entry in entries]


def core_paths():
    return [_path(relative) for relative in CORE_RELATIVE]


def route_paths(family):
    return _unique(
        current_course_paths(family)
        + [_path(relative) for relative in ROUTE_EXTRAS[family]]
    )


def source_paths():
    """Return the full compatibility pack sources in priority order."""
    primary = core_paths() + current_course_paths()
    supporting = [
        _path(relative)
        for relative in [
            "references/WORKBUDDY-COURSE.md",
            "references/COMMUNICATIONS-SERIES.md",
            "CROSS-PLATFORM.md",
            "delivery-pack/DELIVERY-WORKFLOW.md",
            "delivery-pack/STYLE-GUIDE-WORD.md",
            "outputs/博AI增效-课程销售矩阵.md",
            "outputs/博AI增效-课程销售客服Q&A.md",
        ]
    ]
    historical = [
        path
        for path in sorted((ROOT / "references").glob("[0-9][0-9]-*.md"))
        if path.name != "01-三天综合办公-语言标杆.md"
    ]
    return _unique(primary + supporting + historical)


def pack_specs():
    specs = [
        {
            "key": "core",
            "output": MOBILE / "博AI课纲-手机核心规则包.md",
            "title": "博AI课纲·手机核心规则包",
            "guidance": "每次手机写稿都加载本包，再按课程方向加载一个参考包。这里不重复课程全文。",
            "sources": core_paths(),
        }
    ]
    for family in ("office-management", "marketing-agent", "industry"):
        specs.append(
            {
                "key": family,
                "output": ROUTE_OUTPUTS[family],
                "title": ROUTE_TITLES[family],
                "guidance": ROUTE_GUIDANCE[family],
                "sources": route_paths(family),
            }
        )
    specs.append(
        {
            "key": "full",
            "output": FULL_OUTPUT,
            "title": "博AI课纲·手机全量兼容包",
            "guidance": "仅用于支持大附件与长上下文的客户端。普通手机写稿优先使用核心规则包加一个方向包。",
            "sources": source_paths(),
        }
    )
    return specs


def _canonical_text(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()


def render_sources(title, guidance, paths):
    version = _path("VERSION").read_text(encoding="utf-8").strip()
    text = (
        f"# {title}\n\n"
        f"Skill版本：{version}\n\n"
        f"{guidance}\n\n"
        "GitHub自动生成，只读。用户要求与当前13份成稿优先；缺文件或截断须说明。\n"
    )
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        body = _canonical_text(path)
        def rebase_link(match):
            target = match.group(1)
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path or target.startswith('/'):
                return match.group(0)
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(relative), url.path))
            mobile_path = posixpath.relpath(resolved, 'mobile')
            return '](' + urlunsplit(('', '', mobile_path, url.query, url.fragment)) + ')'
        body = re.sub(r'\]\(([^\n)]+)\)', rebase_link, body)
        text += f"\n\n---\n\n## 文件：{relative}\n\n{body}\n"
    return text


def render():
    """Backward-compatible rendering of the full pack."""
    spec = next(spec for spec in pack_specs() if spec["key"] == "full")
    return render_sources(spec["title"], spec["guidance"], spec["sources"])


def rendered_packs():
    return {
        spec["output"]: render_sources(
            spec["title"], spec["guidance"], spec["sources"]
        )
        for spec in pack_specs()
    }


def _mobile_manifest(rendered):
    import layout_identity

    specs = {spec["output"]: spec for spec in pack_specs()}
    packs = {}
    for output, text in rendered.items():
        spec = specs[output]
        packs[output.name] = {
            "key": spec["key"],
            "characters": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "sources": [
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(
                        _canonical_text(path).encode("utf-8")
                    ).hexdigest(),
                }
                for path in spec["sources"]
            ],
        }
    return json.dumps(
        {
            "name": "boai-kegang-mobile-packs",
            "version": _path("VERSION").read_text(encoding="utf-8").strip(),
            "reference_basis": "outputs/catalog",
            "basis_sha256": course_basis_sha256(),
            "layout_basis_sha256": layout_identity.layout_basis_sha256(),
            "packs": packs,
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def build(check=False):
    rendered = rendered_packs()
    manifest = _mobile_manifest(rendered)
    if check:
        for output, text in rendered.items():
            if not output.exists() or output.read_text(encoding="utf-8") != text:
                raise ValueError(f"手机包与源文件不一致，请重新生成: {output.name}")
        if (
            not MANIFEST_PATH.exists()
            or MANIFEST_PATH.read_text(encoding="utf-8") != manifest
        ):
            raise ValueError("手机包清单与源文件不一致，请重新生成")
    else:
        MOBILE.mkdir(parents=True, exist_ok=True)
        for output, text in rendered.items():
            output.write_text(text, encoding="utf-8")
        MANIFEST_PATH.write_text(manifest, encoding="utf-8")
    summary = {
        output.name: {
            "sources": len(next(s for s in pack_specs() if s["output"] == output)["sources"]),
            "characters": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
        for output, text in rendered.items()
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return FULL_OUTPUT


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    build(parser.parse_args().check)
