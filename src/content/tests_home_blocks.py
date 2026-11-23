from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product
from src.content.home_slots import home_categories, home_popular
from src.content.models import Advantage, HomeBlock
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

    def test_empty_title_does_not_fall_back_to_a_code_literal(self):
        _block("popular", title_uk="", title_en="", cta_uk="", cta_en="", sort=3)
        page = self.client.get("/")
        self.assertNotContains(page, ">Популярні товари<")
        self.assertNotContains(page, ">Перейти до каталогу<")

    def test_english_block_uses_the_english_field(self):
        _block("popular", title_uk="Популярні товари", title_en="Guest picks", sort=4)
        page = self.client.get("/en/")
        self.assertContains(page, "Guest picks")
        self.assertNotContains(page, ">Популярні товари<")


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

    def test_legacy_home_sections_are_not_rendered(self):
        block = _block("advantages", title_uk="Чому", sort=5)
        for index in range(5):
            Advantage.objects.create(
                block=block,
                title_uk=f"Пункт {index}",
                text_uk="Текст",
                sort=index,
            )
        _block("categories", title_uk="Категорії секція", sort=2)
        _block("reviews", title_uk="Відгуки секція", sort=7)
        _block("callback", title_uk="Зворотний секція", sort=8)
        page = self.client.get("/")
        self.assertNotContains(page, "benefit-list")
        self.assertNotContains(page, "Пункт 4")
        self.assertNotContains(page, "Категорії секція")
        self.assertNotContains(page, "Відгуки секція")
        self.assertNotContains(page, "Зворотний секція")


def _block(key, **values):
    block, _created = HomeBlock.objects.get_or_create(key=key, defaults=values)
    for name, value in values.items():
        setattr(block, name, value)
    block.save()
    return block
