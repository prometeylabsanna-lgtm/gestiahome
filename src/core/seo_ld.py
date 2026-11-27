"""JSON-LD: Organization, WebSite, BreadcrumbList, Product+Offer."""

from __future__ import annotations

import json
from decimal import Decimal

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext

from src.core.seo import (
    BRAND,
    _default_image,
    _url_name,
    absolute_media,
    public_base,
    public_contacts,
)

CONTENT_URL_NAMES = frozenset(
    {"about", "faq", "contacts", "offer", "privacy", "cookies", "shipping"}
)


def json_ld_script(data: dict) -> str:
    payload = json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, separators=(",", ":"))
    payload = (
        payload.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')


def build_graph(context) -> dict:
    request = context["request"]
    base = public_base(request)
    site = context.get("site_settings")
    image = (context.get("seo") or {}).get("image") or _default_image(request, site)
    graph = [_organization(request, site, image), _website(base)]
    crumbs = _breadcrumbs(context, request)
    if crumbs is not None:
        graph.append(crumbs)
    product = _product_node(context, request)
    if product is not None:
        graph.append(product)
    faq = _faq_node(context, request)
    if faq is not None:
        graph.append(faq)
    contact = _contact_node(context, request)
    if contact is not None:
        graph.append(contact)
    return {"@context": "https://schema.org", "@graph": graph}


def _organization(request, site, image: str) -> dict:
    base = public_base(request)
    node = {
        "@type": "Organization",
        "@id": f"{base}/#organization",
        "name": BRAND,
        "url": f"{base}/",
    }
    if image:
        node["logo"] = image
    contacts = public_contacts() if site is not None else None
    if contacts and contacts["phone"]:
        node["telephone"] = contacts["phone"]
    if contacts and contacts["email"]:
        node["email"] = contacts["email"]
    if contacts and contacts["address"]:
        node["address"] = {"@type": "PostalAddress", "streetAddress": contacts["address"]}
    if contacts and contacts["same_as"]:
        node["sameAs"] = list(contacts["same_as"])
    return node


_LANGUAGE_TAGS = {"uk": "uk-UA", "en": "en-US", "fr": "fr-FR"}


def _in_language() -> list[str]:
    from src.core.middleware import language_enabled

    tags = [
        _LANGUAGE_TAGS.get(code, code)
        for code, _label in settings.LANGUAGES
        if language_enabled(code)
    ]
    return tags or ["uk-UA"]


def _website(base: str) -> dict:
    return {
        "@type": "WebSite",
        "@id": f"{base}/#website",
        "name": BRAND,
        "url": f"{base}/",
        "inLanguage": _in_language(),
        "publisher": {"@id": f"{base}/#organization"},
    }


def _crumb_list(items: list[tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": index, "name": name, "item": url}
            for index, (name, url) in enumerate(items, start=1)
        ],
    }


def _home_crumb(request) -> tuple[str, str]:
    return (gettext("Головна"), public_base(request) + reverse("home"))


def _catalog_crumb(request) -> tuple[str, str]:
    return (gettext("Каталог"), public_base(request) + reverse("catalog"))


def _breadcrumbs(context, request):
    url_name = _url_name(request)
    if url_name == "product" and context.get("product") is not None:
        return _product_crumbs(context["product"], request)
    if url_name == "category" and context.get("category") is not None:
        items = [_home_crumb(request), _catalog_crumb(request)]
        items.extend(_category_chain(context["category"], request))
        return _crumb_list(items)
    if url_name == "catalog":
        return _crumb_list([_home_crumb(request), _catalog_crumb(request)])
    if url_name == "collection" and context.get("collection") is not None:
        return _collection_crumbs(context, request)
    if url_name in CONTENT_URL_NAMES:
        title = _content_title(context, url_name)
        if not title:
            return None
        canonical = (context.get("seo") or {}).get("canonical") or (
            public_base(request) + request.path
        )
        return _crumb_list([_home_crumb(request), (title, canonical)])
    return None


def _category_chain(category, request) -> list[tuple[str, str]]:
    base = public_base(request)
    return [(node.name, base + node.get_absolute_url()) for node in category.chain()]


def _absolute_path(request, path: str) -> str:
    value = str(path or "").strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    if not value.startswith("/"):
        value = "/" + value
    return public_base(request) + value


def _collection_crumbs(context, request) -> dict:
    collection = context["collection"]
    items = [_home_crumb(request), _catalog_crumb(request)]
    group = context.get("menu_group")
    group_url = _absolute_path(request, context.get("crumb_group_url") or "")
    group_name = " ".join(str(getattr(group, "title", "") or "").split()) if group else ""
    if group_name and group_url:
        items.append((group_name, group_url))
    title = " ".join(str(collection.title or "").split()) or BRAND
    canonical = (context.get("seo") or {}).get("canonical") or _absolute_path(
        request, collection.get_absolute_url()
    )
    items.append((title, canonical))
    return _crumb_list(items)


def _product_crumbs(product, request) -> dict:
    items = [_home_crumb(request), _catalog_crumb(request)]
    if product.category_id:
        items.extend(_category_chain(product.category, request))
    items.append((product.name, public_base(request) + product.get_absolute_url()))
    return _crumb_list(items)


def _content_title(context, url_name: str) -> str:
    if url_name == "about":
        page = context.get("page")
        if page is None:
            return ""
        return " ".join(str(getattr(page, "title", "") or "").split()) or gettext("Про нас")
    if url_name == "contacts":
        return gettext("Контакти")
    if url_name == "faq":
        page = context.get("page")
        if page is None:
            return ""
        raw = str(getattr(page, "crumb", "") or getattr(page, "title", "") or "")
        cleaned = (
            raw.replace("<br>", " ")
            .replace("<br/>", " ")
            .replace("<br />", " ")
            .replace("<p>", " ")
            .replace("</p>", " ")
        )
        return " ".join(cleaned.split()) or gettext("Актуальні питання")
    doc = context.get("doc") or {}
    return " ".join(str(doc.get("title") or "").split())


def _contact_node(context, request):
    if _url_name(request) != "contacts":
        return None
    base = public_base(request)
    canonical = (context.get("seo") or {}).get("canonical") or f"{base}{request.path}"
    return {
        "@type": "ContactPage",
        "@id": f"{canonical}#contactpage",
        "url": canonical,
        "name": gettext("Контакти"),
        "isPartOf": {"@id": f"{base}/#website"},
        "mainEntity": {"@id": f"{base}/#organization"},
    }


def _faq_node(context, request):
    if _url_name(request) != "faq":
        return None
    items = list(context.get("items") or [])
    if not items:
        return None
    from django.utils.html import strip_tags

    entities = []
    for item in items:
        question = " ".join(str(getattr(item, "question", "") or "").split())
        answer = " ".join(strip_tags(str(getattr(item, "answer", "") or "")).split())
        if not question or not answer:
            continue
        entities.append(
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
        )
    if not entities:
        return None
    return {"@type": "FAQPage", "mainEntity": entities}


def _offer(canonical: str, product) -> dict:
    return {
        "@type": "Offer",
        "url": canonical,
        "priceCurrency": "UAH",
        "price": f"{Decimal(product.price_uah).quantize(Decimal('0.01'))}",
        "availability": (
            "https://schema.org/InStock"
            if int(product.stock_qty or 0) > 0
            else "https://schema.org/OutOfStock"
        ),
    }


def _media_urls(request, urls) -> list[str]:
    images = []
    for raw in urls:
        try:
            url = absolute_media(request, raw)
        except ValueError:
            continue
        if url and url not in images:
            images.append(url)
    return images


def _product_images(product, request) -> list[str]:
    urls = []
    for shot in product.images.all():
        image = getattr(shot, "image", None)
        if image:
            urls.append(image.url)
    return _media_urls(request, urls)


def _collection_images(collection, request) -> list[str]:
    return _media_urls(request, [photo.get("url") or "" for photo in collection.gallery_photos()])


def _product_node(context, request):
    url_name = _url_name(request)
    if url_name == "product":
        product = context.get("product")
        if product is None:
            return None
        canonical = public_base(request) + product.get_absolute_url()
        name = product.name
        images = _product_images(product, request)
        description = " ".join(str(product.seo_description or "").split())
    elif url_name == "collection":
        collection = context.get("collection")
        product = getattr(collection, "product", None) if collection is not None else None
        if product is None or not product.is_active:
            return None
        canonical = (context.get("seo") or {}).get("canonical") or (
            public_base(request) + collection.get_absolute_url()
        )
        name = " ".join(str(collection.title or "").split()) or product.name
        images = _collection_images(collection, request) or _product_images(product, request)
        description = " ".join(str(collection.seo_description or "").split())
    else:
        return None
    if not images:
        fallback = (context.get("seo") or {}).get("image") or ""
        if fallback:
            images.append(fallback)
    node = {
        "@type": "Product",
        "name": name,
        "url": canonical,
        "brand": {"@type": "Brand", "name": BRAND},
        "offers": _offer(canonical, product),
    }
    sku = str(product.sku or "").strip()
    if sku:
        node["sku"] = sku
    if description:
        node["description"] = description
    if images:
        node["image"] = images
    return node
