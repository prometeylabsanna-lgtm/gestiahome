from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category
from src.content.models import HomeCollection
from src.content.models_menu import MenuGroup, MenuGroupItem


class MenuGroupRenderTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.category = Category.objects.create(
            name_uk="Тест-кат",
            name_en="Test cat",
            slug="test-cat-menu",
            is_active=True,
        )
        self.collection = HomeCollection.objects.create(
            title_uk="Квітка-душа",
            title_en="Soul Flower",
            category=self.category,
            is_active=True,
            sort=1,
        )
        self.open_group = MenuGroup.objects.create(
            title_uk="Святкові бокси",
            title_en="Festive boxes",
            sort=1,
            is_active=True,
            open_by_default=True,
        )
        self.closed_group = MenuGroup.objects.create(
            title_uk="Столові аксесуари",
            title_en="Table accessories",
            sort=2,
            is_active=True,
            open_by_default=False,
        )
        self.hidden_group = MenuGroup.objects.create(
            title_uk="Прихована",
            title_en="Hidden",
            sort=3,
            is_active=False,
        )
        self.collection_item = MenuGroupItem.objects.create(
            group=self.open_group,
            label_uk="«Квітка-душа»",
            label_en="«Soul Flower»",
            collection=self.collection,
            sort=1,
            is_active=True,
        )
        self.category_item = MenuGroupItem.objects.create(
            group=self.open_group,
            label_uk="Категорійний пункт",
            label_en="Category item",
            category=self.category,
            sort=2,
            is_active=True,
        )
        self.catalog_item = MenuGroupItem.objects.create(
            group=self.closed_group,
            label_uk="Підсвічники",
            label_en="Candle holders",
            sort=1,
            is_active=True,
        )
        MenuGroupItem.objects.create(
            group=self.open_group,
            label_uk="Неактивний",
            label_en="Inactive",
            sort=9,
            is_active=False,
        )
        MenuGroupItem.objects.create(
            group=self.hidden_group,
            label_uk="У прихованій",
            label_en="In hidden",
            sort=1,
            is_active=True,
        )

    def test_header_renders_active_groups_and_items(self):
        page = self.client.get(reverse("home"))
        self.assertEqual(page.status_code, 200)
        html = page.content.decode()
        self.assertIn("Святкові бокси", html)
        self.assertIn("Столові аксесуари", html)
        self.assertIn("«Квітка-душа»", html)
        self.assertIn("Підсвічники", html)
        self.assertNotIn("Прихована", html)
        self.assertNotIn("Неактивний", html)
        self.assertNotIn("У прихованій", html)
        self.assertIn('class="nd-mega__group is-open"', html)
        self.assertIn('class="nd-burger__group is-open"', html)

    def test_item_href_collection_category_catalog(self):
        self.assertEqual(self.collection_item.get_href(), self.category.get_absolute_url())
        self.assertEqual(self.category_item.get_href(), self.category.get_absolute_url())
        self.assertEqual(self.catalog_item.get_href(), reverse("catalog"))
        orphan = HomeCollection.objects.create(
            title_uk="Без категорії",
            title_en="No category",
            is_active=True,
            sort=2,
        )
        item = MenuGroupItem.objects.create(
            group=self.open_group,
            label_uk="Орфан",
            collection=orphan,
            sort=3,
            is_active=True,
        )
        self.assertEqual(item.get_href(), reverse("catalog"))
        self.assertEqual(orphan.get_absolute_url(), reverse("catalog"))

    def test_header_links_point_to_expected_urls(self):
        page = self.client.get(reverse("home"))
        html = page.content.decode()
        self.assertIn(f'href="{self.category.get_absolute_url()}"', html)
        self.assertIn(f'href="{reverse("catalog")}"', html)
