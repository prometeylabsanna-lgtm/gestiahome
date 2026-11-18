from django.http import QueryDict
from django.test import TestCase

from src.catalog.models import Product
from src.catalog.selectors import filter_catalog, parse_catalog_filters


class MenuCatalogFilterTests(TestCase):
    def test_facet_uses_header_menu(self):
        page = self.client.get("/katalog/")
        self.assertContains(page, "Святкові бокси")
        self.assertContains(page, "«Квітка-душа»")
        self.assertContains(page, "Столові аксесуари")
        self.assertContains(page, "Підсвічники")
        self.assertContains(page, "Серветки")
        self.assertContains(page, "Кільця для серветок")
        self.assertContains(page, 'name="menu"')
        self.assertContains(page, 'value="svyatkovi-boksy"')
        self.assertContains(page, 'value="kvitka-dusha"')
        self.assertContains(page, 'value="stolovi-aksesuary"')
        self.assertNotContains(page, 'name="category"')

    def test_group_and_child_filter_boxes(self):
        group = parse_catalog_filters(QueryDict("menu=svyatkovi-boksy"))
        group_skus = set(filter_catalog(Product.objects.all(), group).values_list("sku", flat=True))
        self.assertIn("COL-KVITKA", group_skus)
        self.assertIn("COL-KORINNIA", group_skus)
        self.assertNotIn("ADD-NAPKIN", group_skus)

        child = parse_catalog_filters(QueryDict("menu=kvitka-dusha"))
        child_skus = set(filter_catalog(Product.objects.all(), child).values_list("sku", flat=True))
        self.assertEqual(child_skus, {"COL-KVITKA"})

        napkins = parse_catalog_filters(QueryDict("menu=servetky"))
        napkin_skus = set(filter_catalog(Product.objects.all(), napkins).values_list("sku", flat=True))
        self.assertIn("ADD-NAPKIN", napkin_skus)
        self.assertNotIn("COL-KVITKA", napkin_skus)

    def test_addon_crumb_follows_accessory_group(self):
        page = self.client.get("/tovar/addon-llyani-servetky/")
        self.assertContains(page, "Столові аксесуари")
        self.assertContains(page, "Серветки")
        self.assertContains(page, 'href="/katalog/?menu=stolovi-aksesuary"')
