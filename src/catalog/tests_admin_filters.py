import re
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from src.catalog.models import Category, Product, ProductSet


def _stable(html: bytes) -> str:
    text = html.decode()
    text = re.sub(r'name="csrf-token" content="[^"]*"', 'name="csrf-token" content="x"', text)
    text = re.sub(r'name="csrfmiddlewaretoken" value="[^"]*"', 'name="csrfmiddlewaretoken" value="x"', text)
    text = re.sub(r'value="[^"]*" id="id_idem"', 'value="x" id="id_idem"', text)
    return text


class ProductChangelistTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("filters", "filters@example.com", "pass-word-9")
        self.client.force_login(self.user)
        self.category = Category.objects.create(slug="cat", name_uk="Каталог")
        self.other = Category.objects.create(slug="other", name_uk="Інше")
        self.product_set = ProductSet.objects.create(slug="set", name_uk="Сет")
        self.active = self._product("BOX", "box", "Бокс", is_active=True, is_sale=False)
        self.hidden = self._product("OFF", "off", "Прихований", is_active=False, is_sale=True)
        self.hidden.category = self.other
        self.hidden.stock_status = Product.Stock.OUT
        self.hidden.save(update_fields=["category", "stock_status"])
        self.url = reverse("admin:catalog_product_changelist")

    def _product(self, sku, slug, name, **flags):
        return Product.objects.create(
            category=self.category,
            product_set=self.product_set,
            sku=sku,
            slug=slug,
            name_uk=name,
            price_uah=Decimal("10"),
            price_eur=Decimal("1"),
            stock_qty=2 if flags.get("is_active", True) else 0,
            **flags,
        )

    def test_filters_are_horizontal_and_do_not_hide_rows(self):
        page = self.client.get(self.url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Категорія")
        self.assertContains(page, "Наявність")
        self.assertContains(page, "Активний")
        self.assertContains(page, "Акція")
        self.assertContains(page, "Усі")
        self.assertContains(page, "Так")
        self.assertContains(page, "Ні")
        self.assertContains(page, "Бокс")
        self.assertContains(page, "Прихований")
        self.assertContains(page, 'name="is_active__exact"')
        self.assertContains(page, 'name="is_sale__exact"')
        self.assertContains(page, 'name="category__id__exact"')
        self.assertContains(page, 'name="stock_status__exact"')
        body = page.content.decode()
        active_choices = body.split('name="is_active__exact"', 1)[1].split("</select>", 1)[0]
        self.assertLess(active_choices.find("Усі"), active_choices.find("Так"))
        self.assertLess(active_choices.find("Так"), active_choices.find("Ні"))

    def test_each_filter_narrows_without_a_default(self):
        active_only = self.client.get(self.url, {"is_active__exact": "1"})
        self.assertContains(active_only, "Бокс")
        self.assertNotContains(active_only, "Прихований")
        sale_only = self.client.get(self.url, {"is_sale__exact": "1"})
        self.assertContains(sale_only, "Прихований")
        self.assertNotContains(sale_only, "Бокс")
        by_category = self.client.get(self.url, {"category__id__exact": str(self.other.pk)})
        self.assertContains(by_category, "Прихований")
        self.assertNotContains(by_category, "Бокс")
        out = self.client.get(self.url, {"stock_status__exact": Product.Stock.OUT})
        self.assertContains(out, "Прихований")
        self.assertNotContains(out, "Бокс")

    def test_bulk_actions_include_delete_and_sale(self):
        request = RequestFactory().get(self.url)
        request.user = self.user
        actions = admin.site._registry[Product].get_actions(request)
        self.assertIn("delete_selected", actions)
        self.assertIn("activate_products", actions)
        self.assertIn("deactivate_products", actions)
        self.assertIn("set_sale", actions)
        self.assertIn("unset_sale", actions)

        self.client.post(self.url, {"action": "deactivate_products", "_selected_action": [str(self.active.pk)]})
        self.active.refresh_from_db()
        self.assertFalse(self.active.is_active)

        self.client.post(self.url, {"action": "activate_products", "_selected_action": [str(self.active.pk)]})
        self.active.refresh_from_db()
        self.assertTrue(self.active.is_active)

        self.client.post(self.url, {"action": "set_sale", "_selected_action": [str(self.active.pk)]})
        self.active.refresh_from_db()
        self.assertTrue(self.active.is_sale)

        self.client.post(self.url, {"action": "unset_sale", "_selected_action": [str(self.hidden.pk)]})
        self.hidden.refresh_from_db()
        self.assertFalse(self.hidden.is_sale)

    def test_sale_flag_does_not_change_the_storefront(self):
        before = _stable(self.client.get(self.active.get_absolute_url()).content)
        self.active.is_sale = True
        self.active.save(update_fields=["is_sale"])
        after = _stable(self.client.get(self.active.get_absolute_url()).content)
        self.assertEqual(before, after)
        self.assertIn("Бокс", after)
        self.assertNotIn("is-sale", after)
