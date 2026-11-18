"""Один файл хрома замість окремих stylesheet у head."""

from __future__ import annotations

import hashlib
from pathlib import Path

from django.contrib.staticfiles import finders

CHROME_FILES = (
    "css/variables.css",
    "css/reset.css",
    "css/base.css",
    "css/layout.css",
    "css/figma/tokens.css",
    "css/nd/tokens.css",
    "css/nd/header.css",
    "css/nd/header-2.css",
    "css/nd/search-suggest.css",
    "css/nd/header-groups.css",
    "css/nd/footer.css",
    "css/nd/wish.css",
    "css/nd/cart.css",
    "css/nd/cart-drawer.css",
    "css/components/buttons.css",
    "css/components/forms.css",
    "css/components/cards.css",
    "css/components/modal.css",
    "css/components/net-toast.css",
    "css/components/crumbs.css",
)

_CACHE: dict[str, str] = {}


def _sources() -> list[tuple[str, Path]]:
    rows = []
    for name in CHROME_FILES:
        found = finders.find(name)
        if found:
            rows.append((name, Path(found)))
    return rows


def chrome_payload() -> tuple[str, str]:
    sources = _sources()
    digest = hashlib.sha256()
    for name, path in sources:
        stat = path.stat()
        digest.update(f"{name}:{stat.st_mtime_ns}:{stat.st_size}".encode())
    token = digest.hexdigest()[:12]
    cached = _CACHE.get(token)
    if cached is not None:
        return cached, token
    chunks = [path.read_text(encoding="utf-8") + "\n" for _name, path in sources]
    body = "".join(chunks)
    _CACHE.clear()
    _CACHE[token] = body
    return body, token
