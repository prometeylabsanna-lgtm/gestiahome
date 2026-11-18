import tempfile
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from src.catalog.admin import GALLERY_HINT, ProductImageInline
from src.catalog.models import (
    Category,
    Product,
    ProductAttribute,
    ProductAttributeGroup,
    ProductImage,
    ProductSet,
)


class CatalogLanguageTabTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.media = override_settings(MEDIA_ROOT=self.tmp.name)
        self.media.enable()
        self.user = User.objects.create_superuser("catalog", "catalog@example.com", "pass-word-9")
        self.client.force_login(self.user)
        self.category = Category.objects.create(slug="cat", name_uk="Каталог")
        self.group = ProductAttributeGroup.objects.create(slug="style", name_uk="Стиль")
        self.attribute = ProductAttribute.objects.create(group=self.group, slug="scandi", name_uk="Сканді")
        self.product_set = ProductSet.objects.create(slug="set", name_uk="Сет")
        self.product = Product.objects.create(
            category=self.category,
            product_set=self.product_set,
            sku="BOX",
            slug="box",
            name_uk="Бокс",
            price_uah=Decimal("10"),
            price_eur=Decimal("1"),
            stock_qty=1,
        )

    def tearDown(self):
        self.media.disable()
        self.tmp.cleanup()

    def test_translated_forms_use_language_tabs(self):
        pages = (
            reverse("admin:catalog_product_change", args=[self.product.pk]),
            reverse("admin:catalog_category_change", args=[self.category.pk]),
            reverse("admin:catalog_productattribute_change", args=[self.attribute.pk]),
            reverse("admin:catalog_productattributegroup_change", args=[self.group.pk]),
        )
        for url in pages:
            page = self.client.get(url)
            self.assertEqual(page.status_code, 200, url)
            self.assertContains(page, "Українська")
            self.assertContains(page, "English")
            self.assertContains(page, "activeFieldsetTab")

    def test_product_gallery_is_stacked_and_sortable(self):
        self.assertEqual(ProductImageInline.ordering_field, "sort")
        self.assertTrue(ProductImageInline.hide_ordering_field)
        raw = BytesIO()
        Image.new("RGB", (4, 4), (1, 2, 3)).save(raw, format="PNG")
        ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile("shot.png", raw.getvalue(), content_type="image/png"),
            sort=0,
        )
        page = self.client.get(reverse("admin:catalog_product_change", args=[self.product.pk]))
        self.assertContains(page, "gestia-product-gallery")
        self.assertContains(page, 'data-ordering-field="sort"')
        self.assertContains(page, "x-sort:handle")
        self.assertContains(page, "gestia-admin-thumb")
        self.assertContains(page, GALLERY_HINT)
        self.assertContains(page, "product_gallery.css")

    def test_collection_bucket_is_hidden_from_the_category_list(self):
        hidden = Category.objects.get(slug="kolektsiini-dodatky")
        page = self.client.get(reverse("admin:catalog_category_changelist"))
        self.assertContains(page, "Каталог")
        self.assertNotContains(page, "Доповнення колекцій")
        change = self.client.get(reverse("admin:catalog_category_change", args=[hidden.pk]))
        self.assertEqual(change.status_code, 302)
        self.assertEqual(change.url, "/admin/")

    def test_filter_group_shows_existing_values_and_a_blank_row(self):
        group = ProductAttributeGroup.objects.create(slug="color-admin", name_uk="Колір")
        ProductAttribute.objects.create(group=group, slug="white", name_uk="Білий", sort=1)
        page = self.client.get(reverse("admin:catalog_productattributegroup_change", args=[group.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Білий")
        self.assertContains(page, "gestia-value-add")
        self.assertContains(page, "Додати")
        self.assertNotContains(page, 'name="values-0-name_uk"')
        add = self.client.get(reverse("admin:catalog_productattribute_add") + f"?group={group.pk}")
        self.assertContains(add, 'name="sort"')
        self.assertContains(add, "gestia-sort")
        self.assertContains(add, 'maxlength="3"')
