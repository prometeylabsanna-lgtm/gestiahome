"""Адмінка українською: підписи полів і системні рядки Unfold."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product
from src.commerce.models import Order
from src.content.models import HomeCollection, HomeCollectionImage, SiteSettings


ENGLISH_LABELS = (
    "SEO title",
    "SEO description",
    "One item per line",
    "LiqPay payment_id",
    "LiqPay order_id",
    "LiqPay status",
    "Dialog title",
    "Current region",
    "Confirm button",
    "Change link",
    "Region step description",
    "Dialog lines (one per row)",
    "Titre du dialogue",
    "Placeholder {number} is substituted safely.",
)


class AdminUkrainianLabelsTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.user = User.objects.create_superuser("editor", "editor@example.com", "pass-word-9")
        self.client.force_login(self.user)

    def test_language_code_is_uk(self):
        from django.conf import settings

        self.assertEqual(settings.LANGUAGE_CODE, "uk")

    def test_model_verbose_names_are_ukrainian(self):
        self.assertEqual(Category._meta.get_field("seo_title_uk").verbose_name, "SEO-заголовок")
        self.assertEqual(Category._meta.get_field("seo_title_en").verbose_name, "SEO-заголовок (EN)")
        self.assertEqual(Category._meta.get_field("seo_description_fr").verbose_name, "SEO-опис (FR)")
        self.assertEqual(Product._meta.get_field("seo_title_uk").verbose_name, "SEO-заголовок")
        self.assertEqual(SiteSettings._meta.get_field("email").verbose_name, "Електронна пошта")
        self.assertEqual(Order._meta.get_field("email").verbose_name, "Електронна пошта")
        self.assertEqual(Order._meta.get_field("payment_txn").verbose_name, "ID платежу LiqPay")
        self.assertEqual(HomeCollectionImage._meta.get_field("alt_uk").verbose_name, "Alt-текст")
        self.assertEqual(
            HomeCollection._meta.get_field("box_items_en").help_text,
            "Один пункт у рядку.",
        )

    def test_changelists_and_forms_hide_english_labels(self):
        category = Category.objects.create(name_uk="Тест", slug="test-uk-cat")
        settings = SiteSettings.load()
        collection = HomeCollection.objects.create(title_uk="Свято", slug="sviatkova")
        pages = [
            ("категорія", self.client.get(reverse("admin:catalog_category_change", args=[category.pk]))),
            ("налаштування", self.client.get(reverse("admin:content_sitesettings_change", args=[settings.pk]))),
            ("колекція", self.client.get(reverse("admin:content_homecollection_change", args=[collection.pk]))),
            ("замовлення", self.client.get(reverse("admin:commerce_order_changelist"))),
        ]
        for name, page in pages:
            self.assertEqual(page.status_code, 200, name)
            body = page.content.decode("utf-8")
            for label in ENGLISH_LABELS:
                self.assertNotIn(label, body, f"{name}: {label}")
        login = self.client.get(reverse("admin:login"), follow=False)
        # already authenticated — login may redirect; also check anonymous
        anon = self.client_class()
        login = anon.get(reverse("admin:login"))
        self.assertEqual(login.status_code, 200)
        login_body = login.content.decode("utf-8")
        self.assertIn("З поверненням до", login_body)
        for label in ENGLISH_LABELS:
            self.assertNotIn(label, login_body, f"login: {label}")
        settings_page = pages[1][1]
        self.assertContains(settings_page, "Електронна пошта")
        category_page = pages[0][1]
        self.assertContains(category_page, "SEO-заголовок")
        self.assertContains(category_page, "SEO-опис")



class AdminIndexAxesAndTitleTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.user = User.objects.create_superuser("editor", "editor@example.com", "pass-word-9")
        self.client.force_login(self.user)

    def test_index_title_is_site_genitive(self):
        page = self.client.get(reverse("admin:index"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Адміністрування сайту")
        self.assertNotContains(page, "Адміністрування сайта")

    def test_index_hides_english_axes_labels(self):
        page = self.client.get(reverse("admin:index"))
        self.assertEqual(page.status_code, 200)
        body = page.content.decode("utf-8")
        for label in ("Axes", "Access attempts", "Access failures", "Access logs"):
            self.assertNotIn(label, body, label)
        self.assertIn("Доступ", body)
        self.assertIn("Спроби входу", body)
        self.assertIn("Невдалі входи", body)
        self.assertIn("Журнали доступу", body)

    def test_product_changelist_shows_reset_filters(self):
        page = self.client.get(reverse("admin:catalog_product_changelist"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Скинути фільтри")
        self.assertNotContains(page, "Reset filters")
        self.assertNotContains(page, "Clear all filters")
