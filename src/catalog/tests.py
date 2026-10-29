import importlib
from decimal import Decimal

from django.apps import apps
from django.http import QueryDict
from django.test import TestCase
from django.utils import translation

from src.catalog.models import (
    CatalogCell,
    Category,
    Product,
    ProductAttribute,
    ProductAttributeGroup,
    ProductSet,
)
from src.catalog.selectors import filter_catalog, parse_catalog_filters


class FacetTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.category = Category.objects.create(slug="cat", name_uk="Каталог")
        style = ProductAttributeGroup.objects.create(slug="style", name_uk="Стиль")
        color = ProductAttributeGroup.objects.create(slug="color", name_uk="Колір")
        self.scandi = ProductAttribute.objects.create(group=style, slug="scandi", name_uk="Скандинавський")
        self.classic = ProductAttribute.objects.create(group=style, slug="classic", name_uk="Класичний")
        self.white = ProductAttribute.objects.create(group=color, slug="white", name_uk="Білий")
        self.green = ProductAttribute.objects.create(group=color, slug="green", name_uk="Зелений")
        self.a = self._product("A", "a", "scandi", "white")
        self.b = self._product("B", "b", "scandi", "green")
        self.c = self._product("C", "c", "classic", "white")

    def _product(self, sku, slug, style, color):
        product = Product.objects.create(
            category=self.category,
            sku=sku,
            slug=slug,
            name_uk=sku,
            price_uah=Decimal("10"),
            price_eur=Decimal("1"),
            stock_qty=100,
        )
        product.filter_attrs.add(
            ProductAttribute.objects.get(slug=style),
            ProductAttribute.objects.get(slug=color),
        )
        return product

    def test_or_inside_group_and_between_groups(self):
        query = QueryDict(mutable=True)
        query.setlist("style", ["scandi", "classic"])
        query.setlist("color", ["white"])
        parsed = parse_catalog_filters(query)
        skus = set(filter_catalog(Product.objects.all(), parsed).values_list("sku", flat=True))
        self.assertEqual(skus, {"A", "C"})

    def test_sort_by_price_asc(self):
        self.a.price_uah = Decimal("300")
        self.a.save(update_fields=["price_uah"])
        self.b.price_uah = Decimal("100")
        self.b.save(update_fields=["price_uah"])
        self.c.price_uah = Decimal("200")
        self.c.save(update_fields=["price_uah"])
        query = QueryDict(mutable=True)
        query["sort"] = "price_asc"
        parsed = parse_catalog_filters(query)
        skus = list(filter_catalog(Product.objects.all(), parsed).values_list("sku", flat=True))
        self.assertEqual(skus[:3], ["B", "C", "A"])
        page = self.client.get("/katalog/?sort=price_asc&in_stock=1")
        self.assertContains(page, 'data-sort-value="price_asc"')
        self.assertContains(page, "Спочатку дешевші")

    def test_catalog_mosaic_uses_cell_price_until_filter(self):
        CatalogCell.objects.create(
            product=self.a,
            band=2,
            layout=CatalogCell.Layout.ROW,
            role=CatalogCell.Role.GRID,
            sort=1,
            price_uah=Decimal("8990"),
            crop=CatalogCell.Crop.UKR,
            name_width=127,
        )
        page = self.client.get("/katalog/")
        self.assertContains(page, "8 990 UAH")
        filtered = self.client.get("/katalog/?in_stock=1")
        self.assertNotContains(filtered, "8 990 UAH")
        self.assertContains(filtered, "data-qa=\"product-grid\"")

    def test_category_page_shows_grid_not_mosaic(self):
        CatalogCell.objects.create(
            product=self.a,
            band=1,
            layout=CatalogCell.Layout.ROW,
            role=CatalogCell.Role.GRID,
            sort=1,
            price_uah=Decimal("8990"),
            crop=CatalogCell.Crop.UKR,
            name_width=127,
        )
        other = Category.objects.create(slug="other", name_uk="Інше")
        self.b.category = other
        self.b.save(update_fields=["category"])
        page = self.client.get("/katalog/cat/")
        self.assertContains(page, 'data-qa="product-grid"')
        self.assertNotContains(page, "catalog-row")
        self.assertContains(page, "/tovar/a/")
        self.assertNotContains(page, "/tovar/b/")

    def test_category_narrows_with_style(self):
        other = Category.objects.create(slug="other", name_uk="Інше")
        self.c.category = other
        self.c.save(update_fields=["category"])
        query = QueryDict(mutable=True)
        query.setlist("category", ["cat"])
        query.setlist("style", ["scandi"])
        parsed = parse_catalog_filters(query)
        skus = set(filter_catalog(Product.objects.all(), parsed).values_list("sku", flat=True))
        self.assertEqual(skus, {"A", "B"})

    def test_filter_panel_lists_figma_actions(self):
        page = self.client.get("/katalog/")
        self.assertContains(page, "Застосувати")
        self.assertContains(page, "Скандинавський")
        self.assertContains(page, 'data-catalog-open')
        self.assertContains(page, 'data-catalog-sheet')
        self.assertContains(page, 'data-sheet-open')

    def test_product_page_shows_figma_purchase(self):
        page = self.client.get("/tovar/a/")
        self.assertContains(page, "Додати в кошик")
        self.assertContains(page, "Замовити одразу")
        self.assertContains(page, 'name="qty"')
        self.assertContains(page, 'max="99"')
        self.assertContains(page, "data-qty-label")
        self.assertContains(page, "Арт. A")

    def test_search_keeps_name(self):
        query = QueryDict(mutable=True)
        query["q"] = "A"
        parsed = parse_catalog_filters(query)
        skus = list(filter_catalog(Product.objects.all(), parsed).values_list("sku", flat=True))
        self.assertEqual(skus, ["A"])


class EnglishCatalogCopyTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.copy = importlib.import_module("src.catalog.migrations.0009_english_catalog_copy")
        self.category = Category.objects.create(slug="svichky", name_uk="Свічки", name_en="")
        Category.objects.create(slug="tekstyl", name_uk="Текстиль ", name_en="Already translated")
        Category.objects.create(slug="not-in-shop", name_uk="Інше", name_en="")
        ProductSet.objects.create(slug="velykodni", name_uk="Великодній", name_en="")
        style = ProductAttributeGroup.objects.create(slug="style", name_uk="Стиль", name_en="Kept style")
        ProductAttribute.objects.create(group=style, slug="scandi", name_uk="Скандинавський", name_en="")
        self.product = Product.objects.create(
            category=self.category,
            sku="GH-04",
            slug="vesilnyi",
            name_uk="Бокс «Весільний»",
            name_en="",
            price_uah=Decimal("14980.00"),
            price_eur=Decimal("320.00"),
            stock_qty=100,
        )
        Product.objects.create(
            category=self.category,
            sku="GH-01",
            slug="velykodnii-ukrainskyi",
            name_uk="Бокс Великодній «Український»",
            name_en="Custom English name",
            price_uah=Decimal("8990.00"),
            price_eur=Decimal("190.00"),
            stock_qty=100,
        )
        self.nest = Product.objects.create(
            category=self.category,
            sku="TL-0012",
            slug="velykodnii-hnizdo",
            name_uk="Бокс Великодній «Гніздо»",
            description_uk="Великодній бокс «Гніздо» — святкова композиція",
            name_en="",
            description_en="",
            price_uah=Decimal("2450.00"),
            price_eur=Decimal("52.00"),
            stock_qty=100,
        )

    def test_fill_writes_empty_english_and_skips_existing_or_unknown(self):
        self.copy.fill_english_catalog(apps, None)
        self.category.refresh_from_db()
        self.product.refresh_from_db()
        self.nest.refresh_from_db()
        self.assertEqual(self.category.name_en, "Candles")
        self.assertEqual(Category.objects.get(slug="tekstyl").name_en, "Already translated")
        self.assertEqual(Category.objects.get(slug="not-in-shop").name_en, "")
        self.assertEqual(self.product.name_en, "Wedding box")
        self.assertEqual(Product.objects.get(sku="GH-01").name_en, "Custom English name")
        self.assertEqual(self.nest.name_en, "Easter box “The Nest”")
        self.assertIn("flower-shaped candle holders", self.nest.description_en)
        self.assertEqual(ProductAttributeGroup.objects.get(slug="style").name_en, "Kept style")
        self.assertEqual(ProductAttribute.objects.get(slug="scandi").name_en, "Scandinavian")
        self.assertEqual(ProductSet.objects.get(slug="velykodni").name_en, "Easter")

    def test_english_product_page_shows_english_name(self):
        self.copy.fill_english_catalog(apps, None)
        page = self.client.get("/en/tovar/vesilnyi/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'lang="en"')
        self.assertContains(page, "<h1>Wedding box</h1>")
        self.assertNotContains(page, "Бокс «Весільний»")
        nest = self.client.get("/en/tovar/velykodnii-hnizdo/")
        self.assertContains(nest, "Easter box “The Nest”")
        self.assertContains(nest, "flower-shaped candle holders")
        self.assertNotContains(nest, "Бокс Великодній «Гніздо»")


class MenuNameEnTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.copy = importlib.import_module("src.catalog.migrations.0011_fill_product_menu_name_en")
        self.category = Category.objects.create(slug="rizdvo", name_uk="Різдво", name_en="Christmas")
        self.cones = Product.objects.create(
            category=self.category,
            sku="GH-02",
            slug="boks-rizdvyanyi-shyshky",
            name_uk="Бокс «Різдвяний Шишки»",
            name_en="Christmas box “Pine Cones”",
            menu_name_uk="Бокс Різдвяний Шишки",
            price_uah=Decimal("4980.00"),
            price_eur=Decimal("110.00"),
            stock_qty=10,
        )

    def _product(self, sku, slug, **extra):
        defaults = {
            "category": self.category,
            "sku": sku,
            "slug": slug,
            "name_uk": sku,
            "price_uah": Decimal("10.00"),
            "price_eur": Decimal("1.00"),
            "stock_qty": 5,
        }
        defaults.update(extra)
        return Product.objects.create(**defaults)

    def test_menu_name_always_uses_product_name(self):
        with translation.override("uk"):
            self.assertEqual(self.cones.menu_name, "Бокс «Різдвяний Шишки»")
        with translation.override("en"):
            self.assertEqual(self.cones.menu_name, "Christmas box “Pine Cones”")
        self.cones.menu_name_uk = "Інша в меню"
        self.cones.menu_name_en = "Other menu"
        with translation.override("uk"):
            self.assertEqual(self.cones.menu_name, "Бокс «Різдвяний Шишки»")
        with translation.override("en"):
            self.assertEqual(self.cones.menu_name, "Christmas box “Pine Cones”")

    def test_fill_copies_same_name_and_translates_by_sku(self):
        same = self._product(
            "SAME",
            "same-name",
            name_uk="Те саме",
            name_en="The same",
            menu_name_uk="Те саме",
        )
        kept = self._product(
            "KEEP",
            "kept-menu",
            name_uk="Інша",
            name_en="Other",
            menu_name_uk="Своя",
            menu_name_en="Custom menu",
        )
        blank = self._product(
            "GH-05",
            "vesnianyi",
            name_uk="Бокс «Весняний»",
            name_en="Spring box",
        )
        self.copy.fill_menu_name_en(apps, None)
        self.cones.refresh_from_db()
        same.refresh_from_db()
        kept.refresh_from_db()
        blank.refresh_from_db()
        self.assertEqual(self.cones.menu_name_en, "Christmas box “Pine Cones”")
        self.assertEqual(same.menu_name_en, "The same")
        self.assertEqual(kept.menu_name_en, "Custom menu")
        self.assertEqual(blank.menu_name_en, "")

    def test_english_menu_shows_product_name_en(self):
        page = self.client.get("/en/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Christmas box “Pine Cones”")
        self.assertNotContains(page, "Бокс Різдвяний Шишки")


class EnglishFrameLabelTests(TestCase):
    def test_filter_label_always_uses_category_name(self):
        textiles = Category.objects.create(
            slug="tekstyl-en",
            name_uk="Текстиль",
            name_en="Textiles",
            filter_name_uk="Інша мітка",
        )
        with translation.override("uk"):
            self.assertEqual(textiles.filter_label, "Текстиль")
        with translation.override("en"):
            self.assertEqual(textiles.filter_label, "Textiles")

    def test_cell_stamp_gets_english_label(self):
        copy = importlib.import_module("src.catalog.migrations.0013_fill_catalogcell_label_en")
        category = Category.objects.create(slug="boxes", name_uk="Бокси", name_en="Boxes")
        product = Product.objects.create(
            category=category,
            sku="CELL",
            slug="cell-box",
            name_uk="Інший",
            name_en="Other",
            price_uah=Decimal("10"),
            price_eur=Decimal("1"),
            stock_qty=1,
        )
        cell = CatalogCell.objects.create(
            product=product,
            band=0,
            layout=CatalogCell.Layout.ROW,
            role=CatalogCell.Role.GRID,
            sort=1,
            price_uah=Decimal("10"),
            label_uk="Бокс Великодній «Український»",
        )
        kept = CatalogCell.objects.create(
            product=product,
            band=0,
            layout=CatalogCell.Layout.ROW,
            role=CatalogCell.Role.GRID,
            sort=2,
            price_uah=Decimal("10"),
            label_uk="Бокс Великодній «Український»",
            label_en="Custom",
        )
        copy.fill_catalogcell_label_en(apps, None)
        cell.refresh_from_db()
        kept.refresh_from_db()
        self.assertEqual(cell.label_en, "Easter box “Ukrainian”")
        self.assertEqual(kept.label_en, "Custom")
        with translation.override("en"):
            self.assertEqual(cell.label, "Easter box “Ukrainian”")
        with translation.override("uk"):
            self.assertEqual(cell.label, "Бокс Великодній «Український»")


SALE_BADGE_MARKERS = (
    "sale-badge",
    "product-sale",
    "is-sale",
    "badge--sale",
    ">Акція<",
    ">Sale<",
)


class SaleBadgeTests(TestCase):
    def test_public_pages_omit_sale_badge_when_flag_is_set(self):
        category = Category.objects.create(slug="sale-cat", name_uk="Бокси", name_en="Boxes")
        product = Product.objects.create(
            category=category,
            sku="SALE-1",
            slug="sale-box",
            name_uk="Бокс без бейджа",
            name_en="Box without a badge",
            price_uah=Decimal("100.00"),
            price_eur=Decimal("3.00"),
            stock_qty=10,
            stock_status=Product.Stock.IN_STOCK,
            is_sale=True,
        )
        self.assertTrue(product.is_sale)
        pages = (
            self.client.get("/tovar/sale-box/"),
            self.client.get("/katalog/", {"q": "SALE-1"}),
            self.client.get("/en/tovar/sale-box/"),
            self.client.get("/en/katalog/", {"q": "SALE-1"}),
        )
        for page in pages:
            self.assertEqual(page.status_code, 200)
            for marker in SALE_BADGE_MARKERS:
                self.assertNotContains(page, marker)
        self.assertContains(pages[0], "Бокс без бейджа")
        self.assertContains(pages[1], "Бокс без бейджа")
        self.assertContains(pages[2], "Box without a badge")
        self.assertContains(pages[3], "Box without a badge")
