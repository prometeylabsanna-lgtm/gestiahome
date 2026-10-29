"""Unfold language tabs: Українська (uk + shared) / English (only *_en)."""

from __future__ import annotations

UK_TAB = "Українська"
EN_TAB = "English"


def language_tabs(*, uk_fields, en_fields, uk_description="", en_description=""):
    """Exactly two Unfold tabs. Shared/non-language fields belong in uk_fields."""
    uk = {"classes": ("tab",), "fields": tuple(uk_fields)}
    if uk_description:
        uk["description"] = uk_description
    en = {"classes": ("tab",), "fields": tuple(en_fields)}
    if en_description:
        en["description"] = en_description
    return ((UK_TAB, uk), (EN_TAB, en))


def assert_language_tab_fieldsets(fieldsets) -> None:
    """Raise AssertionError if fieldsets violate the two-tab language rule."""
    if len(fieldsets) != 2:
        raise AssertionError(f"expected exactly 2 fieldsets, got {len(fieldsets)}")
    (uk_title, uk_opts), (en_title, en_opts) = fieldsets
    if uk_title != UK_TAB:
        raise AssertionError(f"first tab must be {UK_TAB!r}, got {uk_title!r}")
    if en_title != EN_TAB:
        raise AssertionError(f"second tab must be {EN_TAB!r}, got {en_title!r}")
    if "tab" not in (uk_opts.get("classes") or ()):
        raise AssertionError("Ukrainian fieldset must use classes=('tab',)")
    if "tab" not in (en_opts.get("classes") or ()):
        raise AssertionError("English fieldset must use classes=('tab',)")
    for name in en_opts.get("fields", ()):
        label = name if isinstance(name, str) else ".".join(str(part) for part in name)
        if not str(label).endswith("_en"):
            raise AssertionError(f"English tab may only contain *_en fields, got {label!r}")
    for name in uk_opts.get("fields", ()):
        label = name if isinstance(name, str) else ".".join(str(part) for part in name)
        if str(label).endswith("_en"):
            raise AssertionError(f"Ukrainian tab must not contain *_en fields, got {label!r}")
