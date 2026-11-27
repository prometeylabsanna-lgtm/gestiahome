"""Canonical, robots, hreflang і Open Graph з наявного вмісту сайту."""

from __future__ import annotations

import re
from html import unescape
from urllib.parse import urlsplit

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.templatetags.static import static
from django.utils.translation import get_language, gettext

from src.core.utils import localized

TITLE_MAX = 60
DESCRIPTION_MAX = 160
ELLIPSIS = "…"
def _site_name() -> str:
    try:
        from src.content.models import SiteSettings

        return (SiteSettings.load().site_name or "").strip()
    except (OperationalError, ProgrammingError):
        return ""


def META_BRAND() -> str:
    return _site_name()


_COPY_FIELDS = ("seo_description", "short_description", "description")
_HIDDEN_BLOCK = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[^>]+>")
_TRAILING = " .,;:—-–"

NOINDEX_URL_NAMES = frozenset(
    {
        "cart",
        "checkout",
        "thanks",
        "thanks_legacy",
        "wishlist",
        "callback",
        "buy_now",
    }
)
CATALOG_URL_NAMES = frozenset({"catalog", "category"})
PRIVATE_PREFIXES = (
    "/koshik/",
    "/zamovlennia/",
    "/thank-you/",
    "/diakuiemo/",
    "/obrane/",
    "/zayavka/",
    "/zamovyty-odrazu/",
    "/i18n/",
    "/tinymce/",
    "/healthz/",
)
SUGGEST_PREFIXES = ("/katalog/pidkazky/",)
_OG_WIDTH = 1200
_OG_HEIGHT = 630
_RASTER = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
def BRAND() -> str:
    return _site_name()


_OG_LOCALES = {"uk": "uk_UA", "en": "en_US", "fr": "fr_FR"}
_RESERVED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")
_FAKE_EMAIL_SUFFIXES = (".local", ".example", ".test")
_EMPTY_CONTACTS = {
    "phone": "",
    "email": "",
    "address": "",
    "addresses": (),
    "same_as": (),
}


def plain_text(value) -> str:
    raw = _HIDDEN_BLOCK.sub(" ", str(value or ""))
    raw = _TAG.sub(" ", raw)
    return " ".join(unescape(raw).split())


def _splits_word(text: str, index: int) -> bool:
    if index <= 0 or index >= len(text):
        return False
    return text[index - 1].isalnum() and text[index].isalnum()


def clip_text(value, limit: int) -> str:
    text = plain_text(value)
    if limit <= 0 or not text:
        return ""
    if len(text) <= limit:
        return text
    if limit <= len(ELLIPSIS):
        return ELLIPSIS[:limit]
    budget = limit - len(ELLIPSIS)
    trimmed = text[:budget]
    if _splits_word(text, budget) and " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0]
    trimmed = trimmed.rstrip(_TRAILING)
    if not trimmed:
        return ELLIPSIS
    return trimmed + ELLIPSIS


def product_meta_description(product) -> str:
    for field in _COPY_FIELDS:
        text = plain_text(localized(product, field))
        if text:
            return text
    parts = [plain_text(getattr(product, "name", ""))]
    if getattr(product, "category_id", None):
        parts.append(plain_text(product.category.name))
    parts.append(META_BRAND())
    return ". ".join(part for part in parts if part)


def category_meta_description(category) -> str:
    custom = plain_text(localized(category, "seo_description"))
    if custom:
        return custom
    parts = []
    for node in reversed(category.chain()):
        label = plain_text(node.name)
        if label and label not in parts:
            parts.append(label)
    if not parts or parts[-1] != META_BRAND():
        parts.append(META_BRAND())
    return ". ".join(parts)


def collection_meta_description(collection) -> str:
    custom = plain_text(localized(collection, "seo_description"))
    if custom:
        return custom
    for field in ("text", "story"):
        text = plain_text(localized(collection, field))
        if text:
            return text
    title = plain_text(localized(collection, "title"))
    if not title:
        return BRAND()
    return gettext("Колекція «%(title)s». %(brand)s") % {
        "title": title.replace("%", "%%"),
        "brand": BRAND(),
    }


def collection_meta_title(collection) -> str:
    custom = plain_text(localized(collection, "seo_title"))
    if custom:
        return custom
    title = plain_text(localized(collection, "title"))
    if not title:
        return BRAND()
    return gettext("Колекція «%(title)s» — Gestia Home") % {
        "title": title.replace("%", "%%"),
    }


def configured_origin() -> tuple[str, str] | None:
    raw = str(getattr(settings, "SITE_URL", "") or "").strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "https://" + raw.lstrip("/")
    parts = urlsplit(raw)
    if not parts.netloc:
        return None
    return (parts.scheme or "https", parts.netloc)


def public_base(request) -> str:
    origin = configured_origin()
    if origin is not None:
        scheme, netloc = origin
        return f"{scheme}://{netloc}"
    return f"{request.scheme}://{request.get_host()}"


def absolute_media(request, url: str) -> str:
    value = str(url or "").strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    if not value.startswith("/"):
        value = "/" + value
    return public_base(request) + value


def _language() -> str:
    return (get_language() or settings.LANGUAGE_CODE).split("-")[0]


def _language_enabled(code: str) -> bool:
    from src.core.middleware import language_enabled

    return language_enabled(code)


def _url_name(request) -> str:
    match = getattr(request, "resolver_match", None)
    if match is None:
        return ""
    return match.url_name or ""


def _page_number(raw) -> int | None:
    text = str(raw or "").strip()
    if not text.isdigit():
        return None
    number = int(text)
    if number < 1:
        return None
    return number


def _is_tracking(key: str) -> bool:
    return key == "utm" or key.startswith("utm_")


def _query_parts(request):
    page = _page_number(request.GET.get("page")) if "page" in request.GET else None
    extras = []
    for key in request.GET.keys():
        if key == "page" and page is not None:
            continue
        if _is_tracking(key):
            continue
        extras.append(key)
    return page, extras


def _indexable(request, url_name: str, extras: list[str]) -> bool:
    if getattr(request, "seo_noindex", False):
        return False
    if getattr(request, "resolver_match", None) is None:
        return False
    if url_name in NOINDEX_URL_NAMES:
        return False
    if url_name in CATALOG_URL_NAMES and extras:
        return False
    return True


def _canonical_query(indexable: bool, page: int | None) -> str:
    if indexable and page and page > 1:
        return f"?page={page}"
    return ""


def build_head(request, site=None) -> dict:
    url_name = _url_name(request)
    page, extras = _query_parts(request)
    indexable = _indexable(request, url_name, extras)
    query = _canonical_query(indexable, page)
    canonical = public_base(request) + request.path + query
    robots = "" if indexable else "noindex,follow"
    return {
        "canonical": canonical,
        "robots": robots,
        "alternates": _alternates(request, query) if indexable else [],
        "og_type": getattr(request, "seo_og_type", "")
        or ("product" if url_name == "product" else "website"),
        "og_locale": _OG_LOCALES.get(_language(), "uk_UA"),
        "image": _default_image(request, site),
        "indexable": indexable,
    }


def _alternates(request, query: str) -> list[dict]:
    from src.core.i18n import localize_path

    base = public_base(request)
    full = request.path + query
    links = []
    default_href = ""
    for code, _label in settings.LANGUAGES:
        if not _language_enabled(code):
            continue
        href = base + localize_path(full, code)
        links.append({"code": code, "href": href})
        if code == settings.LANGUAGE_CODE:
            default_href = href
    if default_href:
        links.append({"code": "x-default", "href": default_href})
    return links


def _default_image(request, site) -> str:
    og = getattr(site, "og_image", None) if site is not None else None
    if og:
        try:
            return absolute_media(request, og.url)
        except ValueError:
            pass
    logo = getattr(site, "logo", None) if site is not None else None
    if logo:
        try:
            return absolute_media(request, logo.url)
        except ValueError:
            pass
    return absolute_media(request, static("figma/desktop/5493c.png"))


def _image_type(url: str) -> str:
    path = urlsplit(url).path.lower()
    for ext, mime in _RASTER.items():
        if path.endswith(ext):
            return mime
    return ""


def _stored_size(field):
    if not field:
        return None
    try:
        width = int(field.width)
        height = int(field.height)
    except (OSError, ValueError, TypeError):
        return None
    if width < 1 or height < 1:
        return None
    return width, height


def _bundle(url: str, alt: str, field=None, fallback_size=None) -> dict:
    size = _stored_size(field) if field is not None else fallback_size
    payload = {
        "url": url,
        "alt": plain_text(alt),
        "type": _image_type(url),
        "width": "",
        "height": "",
    }
    if size:
        payload["width"], payload["height"] = size
    return payload


def _default_og(request) -> dict:
    from django.utils.translation import gettext

    url = absolute_media(request, static("images/og-default.jpg"))
    alt = gettext("Святковий стіл Gestia Home")
    try:
        from src.content.models import SiteSettings

        site = SiteSettings.load()
        image = site.og_image
    except (OperationalError, ProgrammingError):
        image = None
        site = None
    if image:
        try:
            url = absolute_media(request, image.url)
        except ValueError:
            image = None
        else:
            alt = (site.og_image_alt or "").strip() or alt
    return _bundle(
        url,
        alt,
        fallback_size=(_OG_WIDTH, _OG_HEIGHT),
    )


def _product_picture(product):
    if getattr(product, "card_image", None):
        return product.card_image
    cover = getattr(product, "cover", None)
    if cover is not None and getattr(cover, "image", None):
        return cover.image
    return None


def og_image_bundle(context) -> dict:
    request = context.get("request")
    empty = {"url": "", "alt": "", "type": "", "width": "", "height": ""}
    if request is None:
        return empty
    product = context.get("product")
    if product is not None:
        media_url = getattr(product, "card_photo_url", "") or ""
        if media_url:
            try:
                return _bundle(
                    absolute_media(request, media_url),
                    getattr(product, "name", "") or BRAND(),
                    field=_product_picture(product),
                )
            except ValueError:
                pass
    collection = context.get("collection")
    image = getattr(collection, "image_large", None) if collection is not None else None
    if image:
        try:
            return _bundle(
                absolute_media(request, image.url),
                getattr(collection, "title", "") or BRAND(),
                field=image,
            )
        except ValueError:
            pass
    blocks = context.get("home_blocks") or {}
    hero = blocks.get("hero") if hasattr(blocks, "get") else None
    hero_image = getattr(hero, "image", None) if hero is not None else None
    if hero_image and not getattr(hero, "shows_video", False):
        try:
            alt = plain_text(getattr(hero, "text", "") or "") or BRAND()
            return _bundle(absolute_media(request, hero_image.url), alt, field=hero_image)
        except ValueError:
            pass
    return _default_og(request)


def og_image_url(context) -> str:
    return og_image_bundle(context).get("url") or ""


def robots_text(request) -> str:
    from src.catalog.selectors import catalog_filter_query_names

    lines = ["User-agent: *", "Allow: /", "Allow: /kontakty/"]
    for code, _label in settings.LANGUAGES:
        if code == settings.LANGUAGE_CODE:
            continue
        lines.append(f"Allow: /{code}/kontakty/")
    for prefix in PRIVATE_PREFIXES:
        lines.append(f"Disallow: {prefix}")
    for code, _label in settings.LANGUAGES:
        if code == settings.LANGUAGE_CODE:
            continue
        for prefix in PRIVATE_PREFIXES:
            lines.append(f"Disallow: /{code}{prefix}")
    for prefix in SUGGEST_PREFIXES:
        lines.append(f"Disallow: {prefix}")
    for code, _label in settings.LANGUAGES:
        if code == settings.LANGUAGE_CODE:
            continue
        for prefix in SUGGEST_PREFIXES:
            lines.append(f"Disallow: /{code}{prefix}")
    for key in catalog_filter_query_names():
        lines.append(f"Disallow: /*?*{key}=")
    lines.append("Disallow: /*?*utm_")
    lines.append("")
    lines.append(f"Sitemap: {public_base(request)}/sitemap.xml")
    return "\n".join(lines) + "\n"


def is_placeholder_contact(value: str, kind: str) -> bool:
    raw = str(value or "").strip()
    if kind == "phone":
        digits = "".join(ch for ch in raw if ch.isdigit())
        if not digits or set(digits) == {"0"}:
            return True
        if digits.startswith("380"):
            national = digits[3:]
            if not national or set(national) == {"0"}:
                return True
        return False
    if kind == "email":
        if "@" not in raw:
            return True
        domain = raw.rsplit("@", 1)[1].lower().rstrip(".")
        if not domain or domain.endswith(_FAKE_EMAIL_SUFFIXES):
            return True
        return any(domain == name or domain.endswith("." + name) for name in _RESERVED_EMAIL_DOMAINS)
    return not raw


_BARE_PROFILE_HOSTS = {
    "instagram.com",
    "www.instagram.com",
    "pinterest.com",
    "www.pinterest.com",
    "t.me",
    "telegram.me",
    "www.telegram.me",
}


def public_profile_url(url: str) -> str:
    raw = " ".join(str(url or "").split())
    if not raw:
        return ""
    parts = urlsplit(raw if "://" in raw else "https://" + raw)
    host = parts.netloc.lower()
    if host in _BARE_PROFILE_HOSTS and not parts.path.strip("/"):
        return ""
    return raw


def public_contacts() -> dict:
    try:
        from django.db.utils import OperationalError, ProgrammingError

        from src.content.models import SiteSettings

        site = SiteSettings.load()
    except (OperationalError, ProgrammingError, AttributeError):
        return dict(_EMPTY_CONTACTS)
    phone = " ".join(str(site.phone or "").split())
    if is_placeholder_contact(phone, "phone"):
        phone = ""
    email = str(site.email or "").strip()
    if is_placeholder_contact(email, "email"):
        email = ""
    address = " ".join(str(getattr(site, "address", "") or "").split())
    addresses = []
    for code in ("uk", "en", "fr"):
        text = " ".join(str(getattr(site, f"address_{code}", "") or "").split())
        if text and text not in addresses:
            addresses.append(text)
    same = []
    for attr in ("instagram_url", "pinterest_url", "telegram_url"):
        value = public_profile_url(getattr(site, attr, ""))
        if value:
            same.append(value)
    return {
        "phone": phone,
        "email": email,
        "address": address,
        "addresses": tuple(addresses),
        "same_as": tuple(same),
    }
