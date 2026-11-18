from django.db.utils import OperationalError, ProgrammingError

from src.core.utils import localized


def text(key, **slots):
    from src.content.models_ui import InterfaceCopy

    try:
        raw = localized(InterfaceCopy.load(), key)
    except (OperationalError, ProgrammingError):
        return ""
    for name, value in slots.items():
        raw = raw.replace("{" + name + "}", "" if value is None else str(value))
    return raw
