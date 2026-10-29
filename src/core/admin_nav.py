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
                "items": [
                    {
                        "key": "home_advantages_list",
                        "title": "Список переваг",
                        "icon": "format_list_bulleted",
                        "url_name": "admin:content_advantage_changelist",
                    },
                ],
                "dynamic": "advantages",
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
                "items": [
                    {
                        "key": "home_review_list",
                        "title": "Список відгуків",
                        "icon": "format_quote",
                        "url_name": "admin:content_homereview_changelist",
                    },
                ],
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
                "url_name": "admin:content_aboutreviewsblock_changelist",
                "items": [
                    {
                        "key": "about_review_list",
                        "title": "Список відгуків",
                        "icon": "format_quote",
                        "url_name": "admin:content_aboutreview_changelist",
                    },
                ],
            },
            {
                "key": "about_popular",
                "title": "Популярні товари",
                "icon": "star",
                "url_name": "admin:content_aboutpopularblock_changelist",
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
                "title": "Фільтри",
                "icon": "tune",
                "url_name": "admin:catalog_productattribute_changelist",
                "items": [
                    {
                        "key": "catalog_attribute_groups",
                        "title": "Групи фільтрів",
                        "icon": "account_tree",
                        "url_name": "admin:catalog_productattributegroup_changelist",
                    },
                ],
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
    {
        "title": "Система",
        "items": [
            {
                "key": "recent_actions",
                "title": "Недавні дії",
                "icon": "history",
                "url_name": "admin:admin_logentry_changelist",
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
            visible = _visible_item(_with_dynamic_children(entry))
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


def _with_dynamic_children(entry):
    kind = entry.get("dynamic") or ""
    if kind != "advantages":
        return entry
    children = list(entry.get("items") or [])
    children.extend(_advantage_nav_items())
    expanded = dict(entry)
    expanded["items"] = children
    return expanded


def _advantage_nav_items():
    try:
        from src.content.models import Advantage
    except Exception:
        return []
    try:
        rows = list(Advantage.objects.order_by("sort", "id").only("id", "title_uk"))
    except Exception:
        return []
    items = []
    for row in rows:
        title = (row.title_uk or "").strip() or f"Перевага #{row.pk}"
        items.append(
            {
                "key": f"home_advantage_{row.pk}",
                "title": title[:48],
                "icon": "workspace_premium",
                "url_name": "admin:content_advantage_change",
                "url_args": (row.pk,),
            }
        )
    return items


def _safe_reverse(url_name, url_args=None):
    if not url_name:
        return None
    args = tuple(url_args or ())
    try:
        reverse(url_name, args=args)
    except NoReverseMatch:
        return None
    if args:
        return reverse_lazy(url_name, args=args)
    return reverse_lazy(url_name)


def _link(url_name, query, url_args=None):
    lazy_link = _safe_reverse(url_name, url_args=url_args)
    if lazy_link is None:
        return None
    if not query:
        return lazy_link

    def href(request=None, name=url_name, extra=query, args=tuple(url_args or ())):
        return f"{reverse(name, args=args)}?{extra}"

    return href


def _active(url_name, query, url_args=None):
    def active(request):
        args = tuple(url_args or ())
        try:
            path = reverse(url_name, args=args)
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
        visible = _visible_item(_with_dynamic_children(child))
        if visible:
            children.append(visible)
    url_name = entry.get("url_name") or ""
    query = entry.get("query") or ""
    url_args = entry.get("url_args")
    link = _link(url_name, query, url_args=url_args)
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
        item["active"] = _active(url_name, query, url_args=url_args)
    if children:
        item["items"] = children
    return item
