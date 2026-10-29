from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

from src.commerce.forms import ContactForm, WaitlistForm, style_form
from src.content.form_labels import apply_labels
from src.content.theme import page_style_key, theme_font_family
from src.core.i18n import localize_path
from src.core.middleware import language_enabled
from src.core.seo import build_head


def shop(request):
    currency = request.session.get("currency", "uah")
    if currency not in {"uah", "eur"}:
        currency = "uah"
    site = None
    home_blocks = {}
    nav_categories = []
    menu_categories = []
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

        site = SiteSettings.load()
        form_copy = ContactForms.load()
        home_blocks = {block.key: block for block in HomeBlock.objects.all()}
        nav_categories = list(load_nav())
        menu_categories = list(
            Category.objects.filter(parent__isnull=True, is_active=True).order_by("sort", "name_uk")
        )
        featured = Product.objects.filter(slug="boks-rizdvyanyi-shyshky", is_active=True).prefetch_related("images").first()
        if featured is not None:
            menu_cards = [featured, featured, featured]
        footer_columns = build_footer_columns()
        cart_count = item_count(request)
        wishlist_count = wish_count(request)
    except (OperationalError, ProgrammingError):
        pass
    try:
        from src.content.models_discount import DiscountModal

        discount_modal = DiscountModal.load()
    except (OperationalError, ProgrammingError):
        discount_modal = None
    full = request.get_full_path()
    switch = {
        code: localize_path(full, code)
        for code, _label in settings.LANGUAGES
    }
    return {
        "site_settings": site,
        "home_blocks": home_blocks,
        "nav_categories": nav_categories,
        "menu_categories": menu_categories,
        "menu_cards": menu_cards,
        "footer_columns": footer_columns,
        "currency": currency,
        "cart_count": cart_count,
        "wishlist_count": wishlist_count,
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
