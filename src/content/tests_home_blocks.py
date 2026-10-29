from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product
from src.content.admin_blocks import HomeCallbackForm
from src.content.home_slots import home_categories, home_popular
from src.content.literals import LITERALS
from src.content.models import Advantage, HomeBlock
from src.content.models_discount import DiscountModal
from src.content.models_home_slots import HomeCategorySlot, HomePopularSlot


class HomeBlockRenderTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")

    def test_model_title_replaces_the_literal(self):
        _block("popular", title_uk="Наша добірка", title_en="Our edit", sort=3)
        page = self.client.get("/")
        self.assertContains(page, "Наша добірка")
        self.assertNotContains(page, "Популярні товари")

    def test_empty_title_falls_back_to_the_current_copy(self):
        _block("popular", title_uk="", title_en="", cta_uk="", cta_en="", sort=3)
        page = self.client.get("/")
        self.assertContains(page, "Популярні товари")
        self.assertContains(page, "Перейти до каталогу")

    def test_english_block_uses_the_english_field(self):
        _block("reviews", title_uk="Відгуки", title_en="Guest notes", sort=6)
        page = self.client.get("/en/")
        self.assertContains(page, "Guest notes")
        self.assertNotContains(page, ">Відгуки<")


class ContactFormCopyTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")

    def test_waitlist_text_and_english_fallback(self):
        modal = DiscountModal.load()
        modal.enabled = True
        modal.text_uk = "<p>Майже готово</p><p>Лише для підписників</p>"
        modal.text_en = "<p>Almost ready</p><p>Subscribers only</p>"
        modal.save()
        self.assertContains(self.client.get("/"), "Майже готово")
        self.assertContains(self.client.get("/"), "Лише для підписників")
        english = self.client.get("/en/")
        self.assertContains(english, "Almost ready")
        self.assertContains(english, "Subscribers only")

    def test_waitlist_form_uses_fixed_literals(self):
        modal = DiscountModal.load()
        modal.enabled = True
        modal.text_uk = "<p>Оферта</p>"
        modal.waitlist_button_uk = "Інша кнопка"
        modal.waitlist_button_en = "Other button"
        modal.save()
        self.assertContains(self.client.get("/"), "Повідомити мене")
        self.assertNotContains(self.client.get("/"), "Інша кнопка")
        self.assertContains(self.client.get("/en/"), "Notify me")
        self.assertEqual(LITERALS["waitlist_button"][0], "Повідомити мене")


class HomeBlockAdminTests(TestCase):
    def setUp(self):
        cache.clear()
        user = User.objects.create_superuser("editor", "editor@example.com", "pass-word-9")
        self.client.force_login(user)
        _block("hero", title_uk="Банер тест", sort=1)
        _block(
            "callback",
            lines_uk="Ім’я\nНомер телефону\nПовідомлення",
            lines_en="Name\nPhone number\nMessage",
            sort=8,
        )

    def test_banner_text_changelist_opens_the_single_record(self):
        hero = HomeBlock.objects.get(key="hero")
        response = self.client.get(reverse("admin:content_homebannertext_changelist"))
        self.assertRedirects(response, reverse("admin:content_homebannertext_change", args=[hero.pk]))
        page = self.client.get(reverse("admin:content_homebannertext_change", args=[hero.pk]))
        self.assertContains(page, "Банер тест")
        self.assertContains(page, 'maxlength="64"')
        self.assertNotContains(page, 'name="media_kind"')

    def test_banner_media_form_is_media_only(self):
        hero = HomeBlock.objects.get(key="hero")
        page = self.client.get(reverse("admin:content_homebannermedia_change", args=[hero.pk]))
        self.assertContains(page, 'name="media_kind"')
        self.assertContains(page, 'name="video"')
        self.assertContains(page, "Виберіть файл для завантаження")
        self.assertNotContains(page, 'name="title_uk"')

    def test_callback_placeholders_roundtrip(self):
        block = HomeBlock.objects.get(key="callback")
        page = self.client.get(reverse("admin:content_homecallbackblock_change", args=[block.pk]))
        self.assertContains(page, "Номер телефону")
        form = HomeCallbackForm(instance=block)
        data = {name: form[name].value() if form[name].value() is not None else "" for name in form.fields}
        bound = HomeCallbackForm(data, instance=block)
        self.assertTrue(bound.is_valid(), bound.errors)
        bound.save()
        self.assertEqual(block.lines_uk, "Ім’я\nНомер телефону\nПовідомлення")
        self.assertEqual(block.lines_en, "Name\nPhone number\nMessage")

    def test_mid_banner_is_separate_from_categories(self):
        categories = _block("categories", title_uk="Секція", sort=2)
        video = _block(
            "video",
            media_kind="photo",
            sort=3,
            image="home/video-figma.webp",
            image_mobile="home/video-m.webp",
        )
        cats_page = self.client.get(reverse("admin:content_homecategoriesblock_change", args=[categories.pk]))
        self.assertNotContains(cats_page, "page_video_media_kind")
        self.assertNotContains(cats_page, "Відео-блок після категорій")
        mid = self.client.get(reverse("admin:content_homemidbanner_change", args=[video.pk]))
        self.assertContains(mid, "home/video-figma.webp")
        self.assertContains(mid, 'name="media_kind"')

    def test_advantages_inline_and_bottom_banner_split(self):
        advantages = _block("advantages", title_uk="Чому ми", sort=5, image="home/card.webp")
        video = _block(
            "video_2",
            media_kind="photo",
            sort=6,
            image="home/video_2-figma.webp",
        )
        page = self.client.get(reverse("admin:content_homeadvantagesblock_change", args=[advantages.pk]))
        self.assertContains(page, "home/card.webp")
        self.assertNotContains(page, "page_video_media_kind")
        self.assertNotContains(page, "Відео-блок після переваг")
        bottom = self.client.get(reverse("admin:content_homebottombanner_change", args=[video.pk]))
        self.assertContains(bottom, "home/video_2-figma.webp")


class HomeSlotsTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.categories = _block("categories", sort=2)
        self.popular = _block("popular", sort=4)
        self.cat = Category.objects.create(slug="slot-cat", name_uk="Слот", home_sort=1, is_active=True)
        self.product = Product.objects.create(
            category=self.cat,
            sku="SLOT1",
            slug="slot-prod",
            name_uk="Слот товар",
            price_uah="10",
            price_eur="1",
            is_popular=True,
            is_active=True,
        )

    def test_slots_drive_home_querysets(self):
        HomeCategorySlot.objects.create(block=self.categories, category=self.cat, sort=1)
        HomePopularSlot.objects.create(block=self.popular, product=self.product, sort=1)
        self.assertEqual(home_categories(), [self.cat])
        self.assertEqual(home_popular(), [self.product])
        page = self.client.get("/")
        self.assertContains(page, "Слот")
        self.assertContains(page, "Слот товар")

    def test_advantages_scroll_class_when_more_than_four(self):
        block = _block("advantages", title_uk="Чому", sort=5)
        for index in range(5):
            Advantage.objects.create(
                block=block,
                title_uk=f"Пункт {index}",
                text_uk="Текст",
                sort=index,
            )
        page = self.client.get("/")
        self.assertContains(page, "benefit-list--scroll")
        self.assertContains(page, "Пункт 4")


def _block(key, **values):
    block, _created = HomeBlock.objects.get_or_create(key=key, defaults=values)
    for name, value in values.items():
        setattr(block, name, value)
    block.save()
    return block
