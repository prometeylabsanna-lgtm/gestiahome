from types import SimpleNamespace

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import Exists, OuterRef
from django.urls import reverse

from src.catalog.models import Category, Product
from src.core.middleware import language_enabled
from src.core.seo import configured_origin

STATIC_PAGES = (
    "home",
    "catalog",
    "about",
    "faq",
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


class StaticSitemap(LocalizedSitemap):
    def items(self):
        return list(STATIC_PAGES)

    def location(self, item):
        return reverse(item)


class CategorySitemap(LocalizedSitemap):
    def items(self):
        own = Product.objects.filter(category=OuterRef("pk"), is_active=True)
        nested = Product.objects.filter(
            category__parent=OuterRef("pk"),
            category__is_active=True,
            is_active=True,
        )
        return Category.objects.filter(is_active=True).filter(Exists(own) | Exists(nested))

    def lastmod(self, item):
        return item.updated_at


class ProductSitemap(LocalizedSitemap):
    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, item):
        return item.updated_at


SITEMAPS = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
}
