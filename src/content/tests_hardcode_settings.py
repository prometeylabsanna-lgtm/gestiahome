from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from django.utils import translation

from src.content.models import HomeBlock, SiteSettings
from src.core.utils import currency_labels, format_money


class SiteSettingsHardcodeTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.site = SiteSettings.load()
        self.site.logo = ""
        self.site.instagram_url = ""
        self.site.pinterest_url = ""
        self.site.telegram_url = ""
        self.site.save()
        cache.clear()
        HomeBlock.objects.get_or_create(key="hero", defaults={"title_uk": "Hero", "sort": 1})

    def test_h1_falls_back_to_site_name_when_logo_empty(self):
        self.site.site_name_uk = "Тестова назва бренду"
        self.site.logo = ""
        self.site.save()
        cache.clear()
        page = self.client.get("/")
        self.assertContains(page, "Тестова назва бренду")
        html = page.content.decode()
        self.assertRegex(
            html,
            r'<h1 class="nd-hero__brand">\s*Тестова назва бренду\s*</h1>',
        )

    def test_empty_social_url_is_not_rendered(self):
        self.site.instagram_url = ""
        self.site.pinterest_url = "https://pinterest.com/gestia-test"
        self.site.telegram_url = ""
        self.site.save()
        cache.clear()
        html = self.client.get("/").content.decode()
        self.assertNotIn("instagram.com", html.lower())
        self.assertNotIn(">Instagram<", html)
        self.assertIn("https://pinterest.com/gestia-test", html)
        self.assertNotIn("t.me/", html)

    def test_currency_suffix_comes_from_site_settings(self):
        self.site.currency_uah = "ABC"
        self.site.currency_uah_sign = "@@"
        self.site.currency_eur = "EE"
        self.site.save()
        cache.clear()
        self.assertEqual(currency_labels(), ("ABC", "@@", "EE"))
        self.assertTrue(format_money(Decimal("10"), "uah").endswith(" @@"))
        self.assertTrue(format_money(Decimal("10"), "eur").endswith(" EE"))
