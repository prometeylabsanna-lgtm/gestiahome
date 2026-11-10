import importlib
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.test import TestCase
from django.utils import translation

from src.content.models import Advantage, FooterLink, HomeBlock, Review


class PublicPageTests(TestCase):
    def test_pages_render(self):
        translation.activate("uk")
        for url in (
            "/",
            "/pro-nas/",
            "/katalog/",
            "/koshik/",
            "/polityka-konfidentsiynosti/",
            "/publichnyi-dogovir/",
            "/polityka-cookies/",
            "/dostavka-ta-oplata/",
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_legal_pages_have_full_copy(self):
        translation.activate("uk")
        privacy = self.client.get("/polityka-konfidentsiynosti/")
        self.assertContains(privacy, "Політика конфіденційності")
        self.assertContains(privacy, "Які дані ми збираємо")
        self.assertContains(privacy, "css/pages/legal.css")
        self.assertGreater(len(privacy.content), 2000)
        offer = self.client.get("/publichnyi-dogovir/")
        self.assertContains(offer, "Публічний договір")
        self.assertContains(offer, "Повернення та обмін")
        cookies = self.client.get("/polityka-cookies/")
        self.assertContains(cookies, "Політика cookies")
        self.assertContains(cookies, "Як керувати cookies")
        shipping = self.client.get("/dostavka-ta-oplata/")
        self.assertContains(shipping, "Доставка та оплата")
        self.assertContains(shipping, "Нова пошта")
        self.assertContains(shipping, "Онлайн карткою")

    def test_about_frame_copy(self):
        translation.activate("uk")
        response = self.client.get("/pro-nas/")
        body = response.content.decode()
        self.assertContains(response, "Hi, I’m Gestia")
        self.assertContains(response, "GESTIA HOME")
        self.assertContains(response, "надихати, об’єднувати")
        self.assertContains(response, "жінкою, яка створює дім")
        self.assertContains(response, "Перейти до каталогу")
        self.assertContains(response, "css/nd/about.css")
        self.assertNotContains(response, "css/pages/about.css")
        self.assertNotContains(response, "js/pages/about.js")
        self.assertNotContains(response, "Наша філософія")
        self.assertNotContains(response, "Всесвіт Gestia Home")
        self.assertNotIn("&#8203;", body)
        self.assertNotIn("<wbr", body)
        self.assertNotIn("data-reviews-track", body)
        self.assertNotIn("data-about-pop", body)
        self.assertNotIn("vbanner__img", body)
        self.assertIn("family=Inter:wght@400;500", body)
        self.assertIn("Cormorant+Garamond", body)
        self.assertIn("флористикою", body)
        self.assertNotIn("figma.com/api/mcp/asset", body)
        css = (
            Path(settings.BASE_DIR) / "src" / "core" / "static" / "css" / "nd" / "about.css"
        ).read_text(encoding="utf-8")
        self.assertIn("--nd-", css)
        self.assertNotIn("!important", css)


class EnglishContentCopyTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.copy = importlib.import_module("src.content.migrations.0007_english_content_copy")
        HomeBlock.objects.create(key="popular", title_uk="Популярні товари", cta_uk="Перейти до каталогу")
        HomeBlock.objects.create(key="mega", cta_uk="Дивитись все", cta_en="Keep this")
        Advantage.objects.create(
            title_uk="Унікальний дизайн",
            text_uk="Декор, що поєднує сучасну естетику та природну красу",
        )
        Review.objects.create(
            author_uk="Марія\u00a0К.",
            author_en="Kept",
            text_uk=self.copy.REVIEW_TEXT_UK,
        )
        FooterLink.objects.create(column="info", label_uk="Про нас", url_name="about", sort=1)
        FooterLink.objects.create(
            column="info",
            label_uk="Вже",
            label_en="Already",
            url_name="about",
            url_arg="x",
            sort=2,
        )

    def test_fill_writes_empty_english_and_skips_existing(self):
        self.copy.fill_english_content(apps, None)
        popular = HomeBlock.objects.get(key="popular")
        self.assertEqual(popular.title_en, "Popular products")
        self.assertEqual(popular.cta_en, "Go to the catalogue")
        self.assertEqual(HomeBlock.objects.get(key="mega").cta_en, "Keep this")
        self.assertEqual(Advantage.objects.get().text_en, "Decor that combines a contemporary look with natural beauty")
        review = Review.objects.get()
        self.assertEqual(review.author_en, "Kept")
        self.assertIn("special atmosphere", review.text_en)
        self.assertEqual(
            FooterLink.objects.get(url_name="about", url_arg="", sort=1).label_en,
            "About",
        )
        self.assertEqual(FooterLink.objects.get(url_arg="x").label_en, "Already")

    def test_english_home_shows_translated_block(self):
        self.copy.fill_english_content(apps, None)
        page = self.client.get("/en/")
        self.assertContains(page, "Popular products")
        self.assertNotContains(page, "Популярні товари")
