from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from src.core.sitemaps import SITEMAPS
from src.core.views import (
    chrome_css,
    healthz,
    llm_txt,
    llms_txt,
    page_not_found,
    robots_txt,
    set_currency,
    set_language,
    theme_css,
)

urlpatterns = [
    path("tinymce/", include("tinymce.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    path("theme.css", theme_css, name="theme_css"),
    path("chrome.css", chrome_css, name="chrome_css"),
    path("robots.txt", robots_txt, name="robots"),
    path("llms.txt", llms_txt, name="llms"),
    path("llm.txt", llm_txt, name="llm_legacy"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("i18n/setlang/", set_language, name="set_language"),
    path("i18n/setcurrency/", set_currency, name="set_currency"),
]

urlpatterns += i18n_patterns(
    path("", include("src.core.urls")),
    prefix_default_language=False,
)

handler404 = "src.core.views.page_not_found"
handler500 = "django.views.defaults.server_error"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
