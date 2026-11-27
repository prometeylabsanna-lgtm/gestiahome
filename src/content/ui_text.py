from django.db.utils import OperationalError, ProgrammingError

from src.core.utils import localized


def text(key, **slots):
    from src.content.models_ui import InterfaceCopy

    try:
        raw = localized(InterfaceCopy.load(), key)
    except (OperationalError, ProgrammingError):
        return ""
    return _fill(raw, slots)


def text_or_default(key, **slots):
    """Як text(), але порожнє значення (або відсутній ключ) бере дефолт мови."""
    raw = text(key)
    if not str(raw or "").strip():
        raw = _ui_default(key)
    return _fill(raw, slots)


def _fill(raw, slots):
    text_value = raw or ""
    for name, value in slots.items():
        text_value = text_value.replace("{" + name + "}", "" if value is None else str(value))
    return text_value


def _ui_default(key):
    from django.utils.translation import get_language

    from src.content.ui_defaults import UI_FIELDS
    from src.content.ui_fr import UI_FR

    lang = (get_language() or "uk").split("-")[0]
    if lang not in ("uk", "en", "fr"):
        lang = "uk"
    for item in UI_FIELDS:
        if item[0] != key:
            continue
        uk, en = item[2], item[3]
        chosen = {"uk": uk, "en": en, "fr": UI_FR.get(key, "")}.get(lang) or ""
        if str(chosen).strip():
            return chosen
        return uk
    return ""
