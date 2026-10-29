"""Дерево сайдбара Unfold.

Новий пункт — dict у NAV_TREE:

    {"key": "stable-id", "title": "Назва", "icon": "home", "url_name": "admin:app_model_changelist"}

Порожній url_name або неіснуючий admin URL у меню не потрапляє.
query додається до changelist (фільтр існуючої моделі).
"""

from django.http import QueryDict
from django.urls import NoReverseMatch, reverse, reverse_lazy


NAV_TREE = [
    {
        "title": "Головна",
        "items": [
            {
                "key": "home_banner",
                "title": "Банер",
                "icon": "image",
                "url_name": "admin:content_homebannermedia_changelist",
            },
            {
                "key": "home_banner_text",
                "title": "Текст банера",
                "icon": "title",
                "url_name": "admin:content_homebannertext_changelist",
            },
            {
                "key": "home_categories",
                "title": "Категорії",
                "icon": "grid_view",
                "url_name": "admin:content_homecategoriesblock_changelist",
            },
            {
                "key": "home_mid_banner",
                "title": "Банер середній",
                "icon": "movie",
                "url_name": "admin:content_homemidbanner_changelist",
            },
            {
                "key": "home_popular",
                "title": "Популярні товари",
                "icon": "star",
                "url_name": "admin:content_homepopularblock_changelist",
            },
            {
                "key": "home_advantages",
                "title": "Чому обирають",
                "icon": "verified",
                "url_name": "admin:content_homeadvantagesblock_changelist",
            },
            {
                "key": "home_bottom_banner",
                "title": "Банер нижній",
                "icon": "videocam",
                "url_name": "admin:content_homebottombanner_changelist",
            },
            {
                "key": "home_reviews",
                "title": "Відгуки",
                "icon": "reviews",
                "url_name": "admin:content_homereviewsblock_changelist",
            },
            {
                "key": "home_review_list",
                "title": "Список відгуків",
                "icon": "format_quote",
                "url_name": "admin:content_review_changelist",
            },
            {
                "key": "home_callback",
                "title": "Зворотній дзвінок",
                "icon": "call",
                "url_name": "admin:content_homecallbackblock_changelist",
            },
        ],
    },
    {
        "title": "Про нас",
        "items": [
            {
                "key": "about_intro",
                "title": "Інтро",
                "icon": "info",
                "url_name": "admin:content_aboutintro_changelist",
            },
            {
                "key": "about_gallery",
                "title": "Галерея",
                "icon": "photo_library",
                "url_name": "admin:content_aboutgallery_changelist",
            },
            {
                "key": "about_story",
                "title": "Історія",
                "icon": "menu_book",
                "url_name": "admin:content_aboutstory_changelist",
            },
            {
                "key": "about_banner",
                "title": "Банер",
                "icon": "image",
                "url_name": "admin:content_aboutbanner_changelist",
            },
            {
                "key": "about_reviews",
                "title": "Відгуки",
                "icon": "reviews",
                "url_name": "admin:content_homereviewsblock_changelist",
            },
            {
                "key": "about_picks",
                "title": "Картки під відгуками",
                "icon": "style",
                "url_name": "admin:content_aboutpicksblock_changelist",
            },
        ],
    },
    {
        "title": "Каталог",
        "items": [
            {
                "key": "catalog_products",
                "title": "Товари",
                "icon": "inventory_2",
                "url_name": "admin:catalog_product_changelist",
            },
            {
                "key": "catalog_categories",
                "title": "Категорії",
                "icon": "category",
                "url_name": "admin:catalog_category_changelist",
            },
            {
                "key": "catalog_sets",
                "title": "Сети",
                "icon": "layers",
                "url_name": "admin:catalog_productset_changelist",
            },
            {
                "key": "catalog_attributes",
                "title": "Атрибути",
                "icon": "tune",
                "url_name": "admin:catalog_productattribute_changelist",
                "items": [
                    {
                        "key": "catalog_attribute_groups",
                        "title": "Групи атрибутів",
                        "icon": "account_tree",
                        "url_name": "admin:catalog_productattributegroup_changelist",
                    },
                ],
            },
            {
                "key": "catalog_frames",
                "title": "Фрейми каталогу",
                "icon": "grid_on",
                "url_name": "admin:catalog_catalogcell_changelist",
            },
        ],
    },
    {
        "title": "Знижка",
        "items": [
            {
                "key": "discount",
                "title": "Знижка",
                "icon": "percent",
                "url_name": "admin:content_discountmodal_changelist",
            },
        ],
    },
    {
        "title": "Юридичні сторінки",
        "items": [
            {
                "key": "legal_offer",
                "title": "Публічний договір",
                "icon": "gavel",
                "url_name": "admin:content_offerpage_changelist",
            },
            {
                "key": "legal_privacy",
                "title": "Політика конфіденційності",
                "icon": "policy",
                "url_name": "admin:content_privacypolicypage_changelist",
            },
            {
                "key": "legal_cookies",
                "title": "Політика cookies",
                "icon": "cookie",
                "url_name": "admin:content_cookiepolicypage_changelist",
            },
            {
                "key": "legal_shipping",
                "title": "Доставка та оплата",
                "icon": "local_shipping",
                "url_name": "admin:content_shippingpage_changelist",
            },
        ],
    },
    {
        "title": "Хедер і футер",
        "items": [
            {
                "key": "chrome_header",
                "title": "Шапка і контакти",
                "icon": "web_asset",
                "url_name": "admin:content_sitesettings_changelist",
            },
            {
                "key": "chrome_footer",
                "title": "Тексти підвалу",
                "icon": "notes",
                "url_name": "admin:content_footerchrome_changelist",
            },
            {
                "key": "chrome_footer_links",
                "title": "Посилання футера",
                "icon": "link",
                "url_name": "admin:content_footerlink_changelist",
            },
            {
                "key": "home_cta",
                "title": "CTA та контактні форми",
                "icon": "mail",
                "url_name": "admin:content_contactforms_changelist",
            },
        ],
    },
    {
        "title": "Стилі",
        "items": [
            {
                "key": "styles",
                "title": "Стилі",
                "icon": "palette",
                "url_name": "admin:content_globalpagestyle_changelist",
                "items": [
                    {
                        "key": "style_global",
                        "title": "Увесь сайт",
                        "icon": "public",
                        "url_name": "admin:content_globalpagestyle_changelist",
                    },
                    {
                        "key": "style_home",
                        "title": "Головна",
                        "icon": "home",
                        "url_name": "admin:content_homepagestyle_changelist",
                    },
                    {
                        "key": "style_catalog",
                        "title": "Каталог",
                        "icon": "grid_view",
                        "url_name": "admin:content_catalogpagestyle_changelist",
                    },
                    {
                        "key": "style_product",
                        "title": "Товар",
                        "icon": "inventory_2",
                        "url_name": "admin:content_productpagestyle_changelist",
                    },
                    {
                        "key": "style_cart",
                        "title": "Кошик",
                        "icon": "shopping_cart",
                        "url_name": "admin:content_cartpagestyle_changelist",
                    },
                    {
                        "key": "style_checkout",
                        "title": "Оформлення",
                        "icon": "payments",
                        "url_name": "admin:content_checkoutpagestyle_changelist",
                    },
                    {
                        "key": "style_about",
                        "title": "Про нас",
                        "icon": "info",
                        "url_name": "admin:content_aboutpagestyle_changelist",
                    },
                    {
                        "key": "style_legal",
                        "title": "Юридичні",
                        "icon": "gavel",
                        "url_name": "admin:content_legalpagestyle_changelist",
                    },
                ],
            },
        ],
    },
    {
        "title": "Замовлення і заявки",
        "items": [
            {
                "key": "orders",
                "title": "Замовлення",
                "icon": "receipt_long",
                "url_name": "admin:commerce_order_changelist",
            },
            {
                "key": "inquiries",
                "title": "Заявки",
                "icon": "inbox",
                "url_name": "admin:commerce_inquiry_changelist",
            },
        ],
    },
    {
        "title": "Користувачі",
        "items": [
            {
                "key": "users",
                "title": "Користувачі",
                "icon": "person",
                "url_name": "admin:auth_user_changelist",
            },
            {
                "key": "groups",
                "title": "Групи",
                "icon": "group",
                "url_name": "admin:auth_group_changelist",
            },
        ],
    },
]


def iter_nav_entries(tree=None):
    for group in tree if tree is not None else NAV_TREE:
        yield from _walk(group.get("items") or [])


def build_navigation(request=None):
    groups = []
    for spec in NAV_TREE:
        items = []
        for entry in spec.get("items") or []:
            visible = _visible_item(entry)
            if visible:
                items.append(visible)
        if not items:
            continue
        groups.append(
            {
                "title": spec["title"],
                "separator": bool(groups),
                "collapsible": True,
                "items": items,
            }
        )
    return groups


def _walk(entries):
    for entry in entries:
        yield entry
        yield from _walk(entry.get("items") or [])


def _safe_reverse(url_name):
    if not url_name:
        return None
    try:
        reverse(url_name)
    except NoReverseMatch:
        return None
    return reverse_lazy(url_name)


def _link(url_name, query):
    lazy_link = _safe_reverse(url_name)
    if lazy_link is None:
        return None
    if not query:
        return lazy_link

    def href(request=None, name=url_name, extra=query):
        return f"{reverse(name)}?{extra}"

    return href


def _active(url_name, query):
    def active(request):
        try:
            path = reverse(url_name)
        except NoReverseMatch:
            return False
        current = request.path.rstrip("/")
        base = path.rstrip("/")
        if query:
            if current != base:
                return False
            wanted = QueryDict(query)
            for key in wanted:
                if request.GET.get(key) != wanted.get(key):
                    return False
            return True
        return current == base or current.startswith(base + "/")

    return active


def _visible_item(entry):
    children = []
    for child in entry.get("items") or []:
        visible = _visible_item(child)
        if visible:
            children.append(visible)
    url_name = entry.get("url_name") or ""
    query = entry.get("query") or ""
    link = _link(url_name, query)
    if link is None and not children:
        return None
    if link is None:
        link = children[0]["link"]
    item = {
        "title": entry["title"],
        "icon": entry.get("icon") or "article",
        "link": link,
    }
    if url_name:
        item["active"] = _active(url_name, query)
    if children:
        item["items"] = children
    return item
