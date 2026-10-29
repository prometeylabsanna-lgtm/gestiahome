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
        self.assertIn(">Головна</a>/<span", body)
        self.assertContains(response, "Сучасна жінка може все.")
        self.assertContains(response, "GESTIA HOME")
        self.assertContains(response, "Всесвіт Gestia Home")
        self.assertContains(response, "Красиві речі для дому")
        self.assertContains(response, "Мистецтво сервірування")
        self.assertContains(response, "надихати, об’єднувати")
        self.assertNotContains(response, "Наша філософія")
        self.assertNotContains(response, "інше єр")
        self.assertNotContains(response, "ОБ ЄДНУВАТИ")
        self.assertNotIn("&#8203;", body)
        self.assertNotIn("<wbr", body)
        self.assertNotIn("about-lead__copy--mob", body)
        self.assertNotIn("about-lead__copy--desk", body)
        self.assertIn("data-reviews-track", body)
        self.assertNotIn("data-about-reviews-prev", body)
        self.assertNotIn("data-about-reviews-next", body)
        self.assertIn("js/pages/about.js", body)
        self.assertIn("e6ffe24a-dab5-4cc2-8155-190e3c001158.png", body)
        self.assertNotIn("figma/about/fe172e1f-21be-4583-9078-519fd841cb25.svg", body)
        self.assertIn("vbanner__img--mob", body)
        self.assertIn("vbanner__img--desk", body)
        self.assertNotIn("figma/about/m/1c65c9d9-7443-4409-aeec-78269a2a6038.png", body)
        self.assertNotIn("figma/about/m/65445179-2967-4089-8231-e953ba0592e1.svg", body)
        self.assertIn("figma/about/m/0bb23f7c-e2ab-4658-a731-ca841f4df6c2.svg", body)
        self.assertIn("data-about-pop", body)
        self.assertIn("Inter:wght@100;400;500", body)
        self.assertIn("флористикою", body)
        self.assertNotIn("figma.com/api/mcp/asset", body)
        css_dir = Path(settings.BASE_DIR) / "src" / "core" / "static" / "css" / "pages"
        sheets = "".join((css_dir / name).read_text(encoding="utf-8") for name in ("about.css", "about-2.css", "about-1440.css"))
        self.assertNotIn("font-weight: 100", sheets)
        self.assertNotIn("overflow-wrap: anywhere", sheets)
        self.assertNotIn("word-break: break-word", sheets)
        self.assertIn("word-break: normal", sheets)
        self.assertIn("overflow-wrap: normal", sheets)
        self.assertIn("font-family: var(--font)", sheets)
        self.assertIn("max-width: 708px", sheets)
        self.assertIn("overflow-x: auto", sheets)
        self.assertIn("scroll-snap-type: x mandatory", sheets)
        self.assertIn("touch-action: pan-x", sheets)
        script = (Path(settings.BASE_DIR) / "src" / "core" / "static" / "js" / "pages" / "about.js").read_text(encoding="utf-8")
        self.assertIn("addEventListener", script)
        self.assertIn("scrollBy", script)
        self.assertIn("[data-about-pop-prev]", script)
        self.assertIn("[data-about-pop-next]", script)
        self.assertIn(".disabled", script)
        self.assertNotIn("[data-reviews-track]", script)
        self.assertNotIn("data-about-reviews-prev", script)
        self.assertNotIn("data-about-reviews-next", script)
        self.assertNotIn(".review-card", script)


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
        self.assertEqual(FooterLink.objects.get(url_arg="").label_en, "About")
        self.assertEqual(FooterLink.objects.get(url_arg="x").label_en, "Already")

    def test_english_home_shows_translated_block(self):
        self.copy.fill_english_content(apps, None)
        page = self.client.get("/en/")
        self.assertContains(page, "Popular products")
        self.assertNotContains(page, "Популярні товари")
