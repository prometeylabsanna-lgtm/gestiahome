from types import SimpleNamespace

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import Max
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse

from src.catalog.models import Category, Product
from src.core.middleware import language_enabled
from src.core.seo import configured_origin

STATIC_PAGES = (
    "home",
    "catalog",
    "about",
    "faq",
    "contacts",
    "shipping",
    "offer",
    "privacy",
    "cookies",
)


class LocalizedSitemap(Sitemap):
    i18n = True
    alternates = True
    x_default = True

    def get_languages_for_item(self, item):
        return [code for code, _label in settings.LANGUAGES if language_enabled(code)]

    def get_urls(self, page=1, site=None, protocol=None):
        items = self.items()
        has_items = items.exists() if hasattr(items, "exists") else bool(items)
        if not has_items:
            return []
        origin = configured_origin()
        if origin is not None:
            scheme, netloc = origin
            site = SimpleNamespace(domain=netloc)
            protocol = scheme
        return super().get_urls(page=page, site=site, protocol=protocol)


def static_lastmods() -> dict:
    from src.content.models import AboutPage, HomeBlock
    from src.content.models_faq import FaqPage
    from src.content.models_legal import LegalPage

    dates = {}
    try:
        home = HomeBlock.objects.aggregate(stamp=Max("updated_at"))["stamp"]
        if home:
            dates["home"] = home
        product_stamp = Product.objects.filter(is_active=True).aggregate(stamp=Max("updated_at"))["stamp"]
        category_stamp = Category.objects.filter(is_active=True).aggregate(stamp=Max("updated_at"))["stamp"]
        catalog_stamp = max(
            (item for item in (product_stamp, category_stamp) if item is not None),
            default=None,
        )
        if catalog_stamp:
            dates["catalog"] = catalog_stamp
        about = AboutPage.objects.order_by("-updated_at").values_list("updated_at", flat=True).first()
        if about:
            dates["about"] = about
        faq = FaqPage.objects.order_by("-updated_at").values_list("updated_at", flat=True).first()
        if faq:
            dates["faq"] = faq
        for row in LegalPage.objects.all().only("key", "updated_at"):
            if row.updated_at:
                dates[row.key] = row.updated_at
    except (OperationalError, ProgrammingError):
        return {}
    return dates


class StaticSitemap(LocalizedSitemap):
    def items(self):
        return list(STATIC_PAGES)

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        if not hasattr(self, "_lastmods"):
            self._lastmods = static_lastmods()
        return self._lastmods.get(item)


class CategorySitemap(LocalizedSitemap):
    def items(self):
        from src.catalog.storefront import indexable_categories

        return indexable_categories()

    def lastmod(self, item):
        return item.updated_at


class CollectionSitemap(LocalizedSitemap):
    def items(self):
        from src.content.models import HomeCollection

        return HomeCollection.objects.filter(is_active=True).exclude(slug="").exclude(slug__isnull=True)

    def lastmod(self, item):
        return item.updated_at


class ProductSitemap(LocalizedSitemap):
    def items(self):
        from src.catalog.storefront import indexable_products

        return indexable_products()

    def lastmod(self, item):
        return item.updated_at


SITEMAPS = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
    "collections": CollectionSitemap,
    "products": ProductSitemap,
}
