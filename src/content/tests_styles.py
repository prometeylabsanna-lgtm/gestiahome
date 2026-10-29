from decimal import Decimal

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from src.catalog.models import Category, Product
from src.content.colors import TOKEN_ACCENT, TOKEN_CHROME, TOKEN_INK, TOKEN_PAPER
from src.content.models import SiteSettings
from src.content.models_styles import FONT_GEORGIA, FONT_INTER, PageStyle
from src.core.admin_nav import build_navigation


class PageStyleTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_global_style_drives_theme_css(self):
        row = PageStyle.objects.get(page=PageStyle.Key.GLOBAL)
        row.background_color = "#112233"
        row.chrome_background_color = "#445566"
        row.text_color = "#778899"
        row.hover_color = "#abcdef"
        row.font_family = FONT_GEORGIA
        row.save()
        css = self.client.get(reverse("theme_css")).content.decode()
        self.assertIn("--paper:#112233", css)
        self.assertIn("--chrome:#445566", css)
        self.assertIn("--ink:#778899", css)
        self.assertIn("--accent:#abcdef", css)
        self.assertIn("Georgia", css)
        self.assertIn(".site-header,.site-header__bar{background:var(--chrome)}", css)
        self.assertIn(".site-footer{background:var(--chrome);color:var(--chrome-fg)}", css)
        self.assertIn("--chrome-fg:", css)
        row.chrome_background_color = TOKEN_CHROME
        row.save()
        default_css = self.client.get(reverse("theme_css")).content.decode()
        self.assertIn(".site-header,.site-header__bar{background:var(--chrome)}", default_css)
        self.assertNotIn(".site-footer{background:var(--chrome)", default_css)
        site = SiteSettings.load()
        self.assertEqual(site.color_paper, "#112233")
        self.assertEqual(site.color_ink, "#778899")
        self.assertEqual(site.color_accent, "#abcdef")

    def test_reset_defaults_via_admin(self):
        user = User.objects.create_superuser("styles", "styles@example.com", "pass-word-9")
        self.client.force_login(user)
        row = PageStyle.objects.get(page=PageStyle.Key.GLOBAL)
        row.background_color = "#111111"
        row.chrome_background_color = "#222222"
        row.text_color = "#333333"
        row.hover_color = "#444444"
        row.font_family = FONT_GEORGIA
        row.save()
        url = reverse("admin:content_globalpagestyle_change", args=[row.pk])
        page = self.client.get(url)
        self.assertContains(page, "Дефолт")
        self.assertContains(page, 'name="font_family"')
        self.assertContains(page, 'name="chrome_background_color"')
        response = self.client.post(url, {"_reset_defaults": "1"})
        self.assertEqual(response.status_code, 302)
        row.refresh_from_db()
        self.assertEqual(row.background_color, TOKEN_PAPER)
        self.assertEqual(row.chrome_background_color, TOKEN_CHROME)
        self.assertEqual(row.text_color, TOKEN_INK)
        self.assertEqual(row.hover_color, TOKEN_ACCENT)
        self.assertEqual(row.font_family, FONT_INTER)

    def test_invalid_hex_is_rejected(self):
        row = PageStyle.objects.get(page=PageStyle.Key.GLOBAL)
        row.background_color = "blue"
        with self.assertRaises(ValidationError):
            row.full_clean()

    def test_pages_expose_their_style_key(self):
        category = Category.objects.create(name_uk="Стилі", slug="styli-test")
        product = Product.objects.create(
            category=category,
            sku="STYLE-1",
            slug="style-1",
            name_uk="Стіл",
            price_uah=Decimal("10.00"),
            price_eur=Decimal("1.00"),
            stock_qty=3,
        )
        expected = {
            "/": "home",
            reverse("catalog"): "catalog",
            reverse("product", kwargs={"slug": product.slug}): "product",
            reverse("about"): "about",
            reverse("offer"): "legal",
        }
        for path, key in expected.items():
            page = self.client.get(path)
            self.assertEqual(page.status_code, 200, path)
            self.assertContains(page, f'data-page="{key}"')

    def test_sidebar_has_single_styles_item(self):
        labels = []
        for group in build_navigation(None):
            if group["title"] != "Стилі":
                continue
            for item in group["items"]:
                labels.append(item["title"])
                self.assertFalse(item.get("items"))
        self.assertEqual(labels, ["Стилі"])
