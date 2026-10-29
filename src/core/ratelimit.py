from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext as _

# Не "website"/"url" — Safari/автозаповнення часто заповнюють їх і глушать заявки.
HONEYPOT_FIELD = "gestia_hp"
_LEGACY_HONEYPOT = "website"
_FALLBACK = {"limit": 5, "window": 600}


def client_ip(request) -> str:
    raw = ""
    if getattr(settings, "TRUST_X_FORWARDED_FOR", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            raw = forwarded.split(",")[0].strip()
    if not raw:
        raw = (request.META.get("REMOTE_ADDR") or "").strip()
    return raw[:64] or "unknown"


def honeypot_filled(request, field: str = HONEYPOT_FIELD) -> bool:
    if bool((request.POST.get(field) or "").strip()):
        return True
    if field == HONEYPOT_FIELD:
        return bool((request.POST.get(_LEGACY_HONEYPOT) or "").strip())
    return False


def _quota(form_name: str) -> tuple[int, int]:
    table = getattr(settings, "RATE_LIMITS", None) or {}
    spec = table.get(form_name)
    if not isinstance(spec, dict):
        spec = table.get("default")
    if not isinstance(spec, dict):
        spec = _FALLBACK
    limit = int(spec.get("limit", _FALLBACK["limit"]))
    window = int(spec.get("window", _FALLBACK["window"]))
    return limit, max(window, 1)


def is_rate_limited(request, form_name: str) -> bool:
    """Count this submission. True when the form is over its quota."""
    limit, window = _quota(form_name)
    key = f"gestia-rl:{form_name}:{client_ip(request)}"
    if cache.add(key, 1, timeout=window):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=window)
            count = 1
    return count > limit


def reject_if_limited(request, form, form_name: str) -> bool:
    if not is_rate_limited(request, form_name):
        return False
    form.add_error(None, _("Забагато спроб. Спробуйте трохи пізніше."))
    return True
