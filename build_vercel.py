#!/usr/bin/env python3
"""Vercel build hook: copy demo media → public/media for CDN (outside Python bundle)."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "demo" / "media"
DST = ROOT / "public" / "media"


def main() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    if not SRC.is_dir():
        print("build_vercel: demo/media missing — skip CDN media copy")
        return
    shutil.copytree(SRC, DST)
    count = sum(1 for path in DST.rglob("*") if path.is_file())
    print(f"build_vercel: copied {count} files to public/media/")


if __name__ == "__main__":
    main()
