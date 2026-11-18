from django.conf import settings
from django.http import HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.i18n import check_for_language

from src.content.theme import build_theme_css
from src.core.i18n import collapse_double_prefix, localize_path, safe_next
from src.core.middleware import language_enabled


def healthz(request):
    return HttpResponse("ok")


def page_not_found(request, exception):
    request.seo_noindex = True
    return render(request, "404.html", status=404)


def robots_txt(request):
    from src.core.seo import robots_text

    return HttpResponse(robots_text(request), content_type="text/plain")


def llms_txt(request):
    from src.core.seo_llms import llms_text

    return HttpResponse(llms_text(request), content_type="text/plain; charset=utf-8")


def llm_txt(request):
    return HttpResponsePermanentRedirect(reverse("llms"))


def theme_css(request):
    return HttpResponse(build_theme_css(), content_type="text/css")


def chrome_css(request):
    from src.core.chrome_css import chrome_payload

    body, token = chrome_payload()
    response = HttpResponse(body, content_type="text/css; charset=utf-8")
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    response["ETag"] = token
    return response


def _extract_next(request) -> str:
    raw = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    if not url_has_allowed_host_and_scheme(
        raw,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        raw = safe_next(raw)
    else:
        raw = safe_next(raw)
    return raw


@require_POST
def set_language(request):
    lang = request.POST.get("language", "")
    if not check_for_language(lang) or not language_enabled(lang):
        lang = settings.LANGUAGE_CODE
    target = collapse_double_prefix(localize_path(_extract_next(request), lang))
    response = HttpResponseRedirect(target)
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
    return response


@require_POST
def set_currency(request):
    currency = request.POST.get("currency", "uah")
    if currency not in {"uah", "eur"}:
        currency = "uah"
    request.session["currency"] = currency
    # Currency only — never touches language cookie / URL prefix.
    target = safe_next(request.POST.get("next") or "/")
    return HttpResponseRedirect(target)
