from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

from src.commerce.forms import ContactForm, WaitlistForm, style_form
from src.content.form_labels import apply_labels
from src.content.theme import page_style_key, theme_font_family
from src.core.i18n import localize_path
from src.core.middleware import language_enabled
from src.core.seo import build_head


def _next_path(request) -> str:
    """Full path for language/currency next, without sensitive ?number=."""
    params = request.GET.copy()
    params.pop("number", None)
    query = params.urlencode()
    if query:
        return f"{request.path}?{query}"
    return request.path


def shop(request):
    currency = request.session.get("currency", "uah")
    if currency not in {"uah", "eur"}:
        currency = "uah"
    site = None
    home_blocks = {}
    nav_categories = []
    menu_categories = []
    menu_groups = []
    menu_cards = []
    footer_columns = {"category": [], "info": [], "legal": []}
    cart_count = 0
    wishlist_count = 0
    form_copy = None
    discount_modal = None
    try:
        from src.catalog.models import Category, Product
        from src.catalog.selectors import nav_categories as load_nav
        from src.commerce.cart import item_count
        from src.commerce.wishlist import item_count as wish_count
        from src.content.footer_nav import build_footer_columns
        from src.content.models import ContactForms, HomeBlock, SiteSettings
        from django.db.models import Prefetch

        from src.content.models_menu import MenuGroup, MenuGroupItem

        site = SiteSettings.load()
        form_copy = ContactForms.load()
        home_blocks = {block.key: block for block in HomeBlock.objects.all()}
        nav_categories = list(load_nav())
        menu_categories = list(
            Category.objects.filter(parent__isnull=True, is_active=True).order_by("sort", "name_uk")
        )
        try:
            menu_groups = list(
                MenuGroup.objects.filter(is_active=True)
                .prefetch_related(
                    Prefetch(
                        "items",
                        queryset=MenuGroupItem.objects.filter(is_active=True)
                        .select_related("collection", "collection__category", "category")
                        .order_by("sort", "id"),
                        to_attr="active_items",
                    )
                )
                .order_by("sort", "id")
            )
        except (OperationalError, ProgrammingError):
            menu_groups = []
        card_slugs = (
            "boks-rizdvyanyi-shyshky",
            "velykodnii-hnizdo",
            "velykodnii-ukrainskyi",
        )
        featured = {
            product.slug: product
            for product in Product.objects.filter(slug__in=card_slugs, is_active=True).prefetch_related("images")
        }
        menu_cards = [featured[slug] for slug in card_slugs if slug in featured]
        # #region agent log
        try:
            import json
            import time
            with open("/Users/olegbonislavskyi/Sites/Gestia/Gestia/.cursor/debug-3759d8.log", "a", encoding="utf-8") as _log:
                _log.write(json.dumps({
                    "sessionId": "3759d8",
                    "hypothesisId": "A",
                    "location": "context_processors.py:shop",
                    "message": "mega menu context",
                    "data": {
                        "groups": len(menu_groups),
                        "group_titles": [g.title_uk for g in menu_groups],
                        "cards": len(menu_cards),
                        "card_slugs": [p.slug for p in menu_cards],
                    },
                    "timestamp": int(time.time() * 1000),
                }, ensure_ascii=False) + "\n")
        except OSError:
            pass
        # #endregion
        footer_columns = build_footer_columns()
        cart_count = item_count(request)
        wishlist_count = wish_count(request)
    except (OperationalError, ProgrammingError) as exc:
        # #region agent log
        try:
            import json
            import time
            with open("/Users/olegbonislavskyi/Sites/Gestia/Gestia/.cursor/debug-3759d8.log", "a", encoding="utf-8") as _log:
                _log.write(json.dumps({
                    "sessionId": "3759d8",
                    "hypothesisId": "B",
                    "location": "context_processors.py:shop:except",
                    "message": "shop context aborted",
                    "data": {"error": type(exc).__name__, "detail": str(exc)[:300]},
                    "timestamp": int(time.time() * 1000),
                }, ensure_ascii=False) + "\n")
        except OSError:
            pass
        # #endregion
    try:
        from src.content.models_discount import DiscountModal

        discount_modal = DiscountModal.load()
    except (OperationalError, ProgrammingError):
        discount_modal = None
    next_path = _next_path(request)
    switch = {
        code: localize_path(next_path, code)
        for code, _label in settings.LANGUAGES
    }
    return {
        "site_settings": site,
        "home_blocks": home_blocks,
        "nav_categories": nav_categories,
        "menu_categories": menu_categories,
        "menu_groups": menu_groups,
        "menu_cards": menu_cards,
        "footer_columns": footer_columns,
        "currency": currency,
        "cart_count": cart_count,
        "wishlist_count": wishlist_count,
        "next_path": next_path,
        "lang_switch_urls": switch,
        "lang_enabled": {
            code: language_enabled(code) for code, _label in settings.LANGUAGES
        },
        "form_copy": form_copy,
        "discount_modal": discount_modal,
        "page_style_key": page_style_key(request),
        "theme_font": theme_font_family(),
        "contact_form": apply_labels(style_form(ContactForm()), form_copy),
        "waitlist_form": apply_labels(style_form(WaitlistForm()), form_copy),
        "seo": build_head(request, site),
    }
