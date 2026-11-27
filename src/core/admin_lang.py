"""Unfold language tabs: Українська (uk + shared) / English (*_en) / Français (*_fr)."""

from __future__ import annotations

from src.core.admin_hints import EMPTY_LOCALE_HINT

UK_TAB = "Українська"
EN_TAB = "English"
FR_TAB = "Français"


def _fr_name(name):
    if isinstance(name, str):
        if name.endswith("_en"):
            return name[:-3] + "_fr"
        return name
    parts = []
    for part in name:
        parts.append(part[:-3] + "_fr" if str(part).endswith("_en") else part)
    return tuple(parts)


def language_tabs(*, uk_fields, en_fields, uk_description="", en_description="", fr_description=""):
    """Three Unfold tabs. Shared/non-language fields belong in uk_fields."""
    uk = {"classes": ("tab",), "fields": tuple(uk_fields)}
    if uk_description:
        uk["description"] = uk_description
    en = {"classes": ("tab",), "fields": tuple(en_fields)}
    if not en_description and en_fields:
        en_description = EMPTY_LOCALE_HINT
    if en_description:
        en["description"] = en_description
    fr_fields = tuple(_fr_name(name) for name in en_fields)
    fr = {"classes": ("tab",), "fields": fr_fields}
    if not fr_description and fr_fields:
        fr_description = EMPTY_LOCALE_HINT
    if fr_description:
        fr["description"] = fr_description
    return ((UK_TAB, uk), (EN_TAB, en), (FR_TAB, fr))


def assert_language_tab_fieldsets(fieldsets) -> None:
    """Raise AssertionError if fieldsets violate the three-tab language rule."""
    if len(fieldsets) != 3:
        raise AssertionError(f"expected exactly 3 fieldsets, got {len(fieldsets)}")
    (uk_title, uk_opts), (en_title, en_opts), (fr_title, fr_opts) = fieldsets
    if uk_title != UK_TAB:
        raise AssertionError(f"first tab must be {UK_TAB!r}, got {uk_title!r}")
    if en_title != EN_TAB:
        raise AssertionError(f"second tab must be {EN_TAB!r}, got {en_title!r}")
    if fr_title != FR_TAB:
        raise AssertionError(f"third tab must be {FR_TAB!r}, got {fr_title!r}")
    for title, opts in ((UK_TAB, uk_opts), (EN_TAB, en_opts), (FR_TAB, fr_opts)):
        if "tab" not in (opts.get("classes") or ()):
            raise AssertionError(f"{title} fieldset must use classes=('tab',)")
    for name in en_opts.get("fields", ()):
        label = name if isinstance(name, str) else ".".join(str(part) for part in name)
        if not str(label).endswith("_en"):
            raise AssertionError(f"English tab may only contain *_en fields, got {label!r}")
    for name in fr_opts.get("fields", ()):
        label = name if isinstance(name, str) else ".".join(str(part) for part in name)
        if not str(label).endswith("_fr"):
            raise AssertionError(f"French tab may only contain *_fr fields, got {label!r}")
    for name in uk_opts.get("fields", ()):
        label = name if isinstance(name, str) else ".".join(str(part) for part in name)
        if str(label).endswith("_en") or str(label).endswith("_fr"):
            raise AssertionError(f"Ukrainian tab must not contain *_en or *_fr fields, got {label!r}")
