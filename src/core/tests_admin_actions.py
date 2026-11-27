"""Один тест масової дії адмінки."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from src.catalog.models import Category, Product


class ProductBulkActionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("actions", "actions@example.com", "pass-word-9")
        self.client.force_login(self.user)
        category = Category.objects.create(slug="cat-actions", name_uk="Каталог")
        self.product = Product.objects.create(
            category=category,
            sku="ACT-1",
            slug="act-1",
            name_uk="Тестовий товар",
            price_uah=Decimal("10"),
            price_eur=Decimal("1"),
            stock_qty=2,
            is_active=True,
        )
        self.url = reverse("admin:catalog_product_changelist")

    def test_deactivate_products_hides_selected(self):
        response = self.client.post(
            self.url,
            {
                "action": "deactivate_products",
                "_selected_action": [str(self.product.pk)],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)
