"""Canonical fingerprints for the shared BOPAI layout runtime."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEXT_SUFFIXES = {".md", ".py", ".txt", ".yaml", ".json"}


def layout_asset_paths(root: Path = ROOT) -> list[Path]:
    """Return every source file that defines the fixed Word/PDF appearance."""
    root = root.resolve()
    paths = [
        root / "delivery-pack/课纲模板.docx",
        root / "delivery-pack/STYLE-GUIDE-WORD.md",
        root / "delivery-pack/scripts/课纲排版toWord带图版.py",
    ]
    paths.extend(sorted((root / "delivery-pack/images").glob("*.png")))
    for path in paths:
        if (
            not path.is_file()
            or path.is_symlink()
            or not path.resolve().is_relative_to(root)
        ):
            raise ValueError(f"缺失或不安全的排版资源: {path}")
    return paths


def canonical_bytes(path: Path) -> bytes:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    return path.read_bytes()


def layout_asset_hashes(root: Path = ROOT) -> dict[str, str]:
    root = root.resolve()
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(canonical_bytes(path)).hexdigest()
        for path in layout_asset_paths(root)
    }


def layout_basis_sha256(root: Path = ROOT) -> str:
    payload = json.dumps(
        layout_asset_hashes(root),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


if __name__ == "__main__":
    print(layout_basis_sha256())
