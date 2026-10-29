from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from src.catalog.admin import (
    CategoryAdmin,
    ProductAdmin,
    ProductAttributeAdmin,
    ProductAttributeGroupAdmin,
    ProductSetAdmin,
)
from src.catalog.models import Category, Product, ProductAttribute, ProductAttributeGroup, ProductSet
from src.content.admin import AdvantageAdmin, FooterLinkAdmin, HomeBlockAdmin, ReviewAdmin, SiteSettingsAdmin
from src.content.admin_about import AboutPageAdmin, FooterChromeAdmin
from src.content.admin_blocks import (
    ContactFormsAdmin,
    HomeAdvantagesAdmin,
    HomeCallbackAdmin,
    HomeCategoriesAdmin,
    HomeHeroAdmin,
    HomePopularAdmin,
    HomeReviewsAdmin,
)
from src.content.admin_discount import DiscountModalAdmin
from src.content.admin_legal import LegalPageAdmin
from src.content.models import Advantage, FooterLink, HomeBlock, Review, SiteSettings
from src.content.models_discount import DiscountModal
from src.core.admin_lang import assert_language_tab_fieldsets, language_tabs
from src.core.html_sanitize import (
    strip_outer_p,
    visible_max_length,
    visible_text,
    visible_text_length,
)


class LanguageTabHelperTests(TestCase):
    def test_language_tabs_shape(self):
        fieldsets = language_tabs(uk_fields=("title_uk", "image"), en_fields=("title_en",))
        assert_language_tab_fieldsets(fieldsets)

    def test_rejects_shared_fields_in_english_tab(self):
        with self.assertRaises(AssertionError):
            assert_language_tab_fieldsets(
                language_tabs(uk_fields=("title_uk",), en_fields=("title_en", "image"))
            )

    def test_rejects_en_fields_in_ukrainian_tab(self):
        with self.assertRaises(AssertionError):
            assert_language_tab_fieldsets(
                language_tabs(uk_fields=("title_uk", "title_en"), en_fields=("text_en",))
            )


class VisibleTextHelperTests(TestCase):
    def test_visible_length_strips_tags(self):
        self.assertEqual(visible_text_length("<p>Привіт <strong>світе</strong></p>"), len("Привіт світе"))
        self.assertEqual(visible_text("<p>a&nbsp;b</p>"), "a b")

    def test_visible_max_length_validator(self):
        validate = visible_max_length(5)
        validate("<p>abcd</p>")
        with self.assertRaises(Exception):
            validate("<p>abcdef</p>")

    def test_strip_outer_p(self):
        self.assertEqual(strip_outer_p("<p>один рядок</p>"), "один рядок")
        self.assertEqual(strip_outer_p("<p>a</p><p>b</p>"), "<p>a</p><p>b</p>")


class AdminLanguageTabFieldsetTests(TestCase):
    def test_static_fieldsets_follow_the_rule(self):
        for admin_cls in (
            DiscountModalAdmin,
            LegalPageAdmin,
            AboutPageAdmin,
            FooterChromeAdmin,
            HomeHeroAdmin,
            HomeCategoriesAdmin,
            HomePopularAdmin,
            HomeAdvantagesAdmin,
            HomeReviewsAdmin,
            HomeCallbackAdmin,
            ContactFormsAdmin,
            SiteSettingsAdmin,
            HomeBlockAdmin,
            AdvantageAdmin,
            ReviewAdmin,
            FooterLinkAdmin,
            CategoryAdmin,
            ProductAdmin,
            ProductAttributeGroupAdmin,
            ProductAttributeAdmin,
            ProductSetAdmin,
        ):
            assert_language_tab_fieldsets(admin_cls.fieldsets)

    def test_categories_video_fields_land_in_ukrainian_tab(self):
        admin = HomeCategoriesAdmin(HomeBlock, None)
        fieldsets = admin.get_fieldsets(request=None)
        assert_language_tab_fieldsets(fieldsets)
        uk_fields = fieldsets[0][1]["fields"]
        self.assertIn("page_video_media_kind", uk_fields)
        self.assertIn("page_video_video", uk_fields)

    def test_advantages_video_fields_land_in_ukrainian_tab(self):
        admin = HomeAdvantagesAdmin(HomeBlock, None)
        fieldsets = admin.get_fieldsets(request=None)
        assert_language_tab_fieldsets(fieldsets)
        self.assertTrue(any(str(name).startswith("page_video_") for name in fieldsets[0][1]["fields"]))


class AdminLanguageTabRenderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("langtabs", "lang@example.com", "pass-word-9")
        self.client.force_login(self.user)
        self.category = Category.objects.create(slug="lang-cat", name_uk="Кат")
        self.product = Product.objects.create(
            category=self.category,
            sku="LANG1",
            slug="lang-prod",
            name_uk="Товар",
            price_uah=Decimal("10"),
            price_eur=Decimal("1"),
        )
        self.callback = HomeBlock.objects.create(key=HomeBlock.Key.CALLBACK, sort=8, title_uk="Заявка")
        self.discount = DiscountModal.load()
        SiteSettings.load()

    def test_change_forms_render_two_tabs_and_tinymce(self):
        urls = (
            reverse("admin:content_homecallbackblock_change", args=[self.callback.pk]),
            reverse("admin:content_discountmodal_change", args=[self.discount.pk]),
            reverse("admin:catalog_category_change", args=[self.category.pk]),
            reverse("admin:catalog_product_change", args=[self.product.pk]),
        )
        for url in urls:
            page = self.client.get(url)
            self.assertEqual(page.status_code, 200, url)
            self.assertContains(page, "Українська")
            self.assertContains(page, "English")
            self.assertContains(page, "activeFieldsetTab")
            body = page.content.decode()
            uk_pos = body.find("Українська")
            en_pos = body.find(">English<")
            if en_pos < 0:
                en_pos = body.find("English")
            self.assertGreater(uk_pos, 0, url)
            self.assertGreater(en_pos, uk_pos, url)

        callback_page = self.client.get(
            reverse("admin:content_homecallbackblock_change", args=[self.callback.pk])
        )
        body = callback_page.content.decode()
        self.assertContains(callback_page, "tinymce")
        self.assertContains(callback_page, "data-mce-conf")
        self.assertContains(callback_page, 'name="text_uk"')
        self.assertContains(callback_page, 'name="text_en"')
        self.assertContains(callback_page, 'name="text_mobile_uk"')
        self.assertContains(callback_page, "data-gestia-visible-count")
        self.assertIn('class="tinymce"', body)
        self.assertIn("django_tinymce/init_tinymce.js", body)
        self.assertIn("char_counter.js", body)

        product_page = self.client.get(reverse("admin:catalog_product_change", args=[self.product.pk]))
        self.assertContains(product_page, 'name="description_uk"')
        self.assertContains(product_page, "tinymce")
        self.assertContains(product_page, "data-mce-conf")
