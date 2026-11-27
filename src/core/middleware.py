from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.utils import translation

from src.core.i18n import collapse_double_prefix, localize_path, strip_retired_language_prefix


def language_enabled(lang: str) -> bool:
    allowed = {code for code, _label in settings.LANGUAGES}
    if lang not in allowed:
        return False
    if lang == settings.LANGUAGE_CODE:
        return True
    try:
        from src.content.models import SiteSettings

        site = SiteSettings.load()
    except (OperationalError, ProgrammingError):
        return True
    if lang == "en":
        return site.en_enabled
    if lang == "fr":
        return site.fr_enabled
    return False


class AdminRobotsTagMiddleware:
    """Закриває префікс адмінки від індексації, не згадуючи його в robots.txt."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        admin = str(getattr(settings, "ADMIN_URL", "") or "").strip("/")
        if not admin:
            return response
        root = "/" + admin
        path = request.path or "/"
        if path == root or path.startswith(root + "/"):
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if _is_staff_ui(request.path):
            policy = getattr(settings, "CSP_POLICY_ADMIN", "") or ""
            if policy:
                response["Content-Security-Policy"] = policy
            return response
        policy = getattr(settings, "CSP_POLICY", "") or ""
        if not policy:
            return response
        header = (
            "Content-Security-Policy-Report-Only"
            if getattr(settings, "CSP_REPORT_ONLY", True)
            else "Content-Security-Policy"
        )
        response[header] = policy
        return response


class AdminUkrainianMiddleware:
    """Адмінка і TinyMCE лишаються українською, навіть якщо на вітрині обрано English."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if _is_staff_ui(request.path):
            translation.activate("uk")
            request.LANGUAGE_CODE = "uk"
        return self.get_response(request)


def _is_staff_ui(path: str) -> bool:
    admin_root = "/" + str(settings.ADMIN_URL or "").strip("/")
    if _under(path, admin_root):
        return True
    return _under(path, "/tinymce")


def _under(path: str, root: str) -> bool:
    normalized = (path or "/").rstrip("/") or "/"
    base = (root or "/").rstrip("/") or "/"
    return normalized == base or path.startswith(base + "/")


class LanguagePrefixMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        retired = strip_retired_language_prefix(request.path_info)
        if retired is not None:
            target = collapse_double_prefix(retired)
            query = request.META.get("QUERY_STRING", "")
            if query:
                target = f"{target}?{query}"
            return HttpResponsePermanentRedirect(target)
        collapsed = collapse_double_prefix(request.path_info)
        if collapsed != request.path_info:
            query = request.META.get("QUERY_STRING", "")
            target = collapsed if not query else f"{collapsed}?{query}"
            return HttpResponseRedirect(target)
        lang = translation.get_language() or settings.LANGUAGE_CODE
        lang = lang.split("-")[0]
        if not language_enabled(lang):
            query = request.META.get("QUERY_STRING", "")
            target = localize_path(request.get_full_path(), settings.LANGUAGE_CODE)
            if query and "?" not in target:
                target = f"{target}?{query}"
            return HttpResponseRedirect(target)
        return self.get_response(request)
