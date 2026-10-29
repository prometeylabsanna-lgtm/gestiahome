from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.content.media import MediaChoice
from src.content.models import AboutPage, HomeBlock, SiteSettings


class AboutRenderTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.page = AboutPage.load()

    def test_model_lead_replaces_the_literal(self):
        self.page.lead_uk = "Короткий рядок"
        self.page.lead_en = "A short line"
        self.page.save()
        page = self.client.get(reverse("about"))
        self.assertContains(page, "Короткий рядок")
        self.assertNotContains(page, "Сучасна жінка може все.")

    def test_empty_lead_falls_back(self):
        self.page.lead_uk = ""
        self.page.lead_en = ""
        self.page.body_uk = ""
        self.page.body_en = ""
        self.page.save()
        page = self.client.get(reverse("about"))
        self.assertContains(page, "Сучасна жінка може все.")
        self.assertContains(page, "Вона будує кар’єру")

    def test_english_story_uses_the_english_field(self):
        page = self.client.get("/en/pro-nas/")
        self.assertContains(page, "A modern woman can do anything.")
        self.assertContains(page, "She builds a career")
        self.assertContains(page, "About Gestia Home")
        self.assertContains(page, "All products")
        self.assertContains(page, "Privacy Policy")
        self.assertNotContains(page, "Сучасна жінка може все.")


class HeaderFooterRenderTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.site = SiteSettings.load()

    def test_nav_labels_use_fixed_literals(self):
        self.site.nav_about_uk = "Історія"
        self.site.nav_about_en = "Story"
        self.site.nav_all_uk = "Все"
        self.site.menu_title_uk = "Бокси"
        self.site.menu_title_en = "Boxes"
        self.site.save()
        page = self.client.get("/")
        self.assertContains(page, 'class="head-nav__about"')
        self.assertContains(page, ">Про нас</a>")
        self.assertContains(page, ">Усі товари</a>")
        self.assertContains(page, "<span>Каталог</span>")
        self.assertContains(page, 'class="head-nav__catalog"')
        self.assertNotContains(page, ">Історія</a>")
        self.assertNotContains(page, "<span>Бокси</span>")
        english = self.client.get("/en/")
        self.assertContains(english, ">About</a>")
        self.assertContains(english, ">All products</a>")
        self.assertContains(english, "<span>Catalogue</span>")
        self.assertContains(english, "Catalogue")
        self.assertNotContains(english, ">Story</a>")

    def test_credit_and_logo_fall_back(self):
        self.site.credit_uk = ""
        self.site.credit_en = ""
        self.site.logo = ""
        self.site.save()
        page = self.client.get("/")
        self.assertContains(page, "Зроблено")
        self.assertContains(page, "figma/desktop/5493c.png")
        english = self.client.get("/en/")
        self.assertContains(english, "Made by")

    def test_telegram_url_in_social_row(self):
        self.site.telegram_url = "https://t.me/gestia_home"
        self.site.save()
        page = self.client.get("/")
        self.assertContains(page, 'href="https://t.me/gestia_home"')
        self.assertContains(page, ">Telegram</span>")



class MediaChoiceTests(TestCase):
    def test_photo_keeps_a_video_file_hidden(self):
        block = HomeBlock(media_kind=MediaChoice.Kind.PHOTO, video="home/video/clip.mp4")
        self.assertFalse(block.shows_video)
        block.media_kind = MediaChoice.Kind.VIDEO
        self.assertTrue(block.shows_video)
