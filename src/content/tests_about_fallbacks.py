from django.core.cache import cache
from django.test import TestCase
from django.utils import translation

from src.catalog.models import Category, Product
from src.content.home_slots import about_popular, home_popular
from src.content.models import AboutPage, HomeBlock, Review
from src.content.models_about import AboutPopularSlot
from src.content.models_home_slots import HomePopularSlot


class AboutReviewsDataTests(TestCase):
    """Відгуки більше не рендеряться на /pro-nas/, але дані/фільтри лишаються."""

    def setUp(self):
        cache.clear()
        translation.activate("uk")
        AboutPage.load()

    def test_about_placement_reviews_exist_separately_from_home(self):
        Review.objects.create(
            placement=Review.Placement.HOME,
            author_uk="Дім Автор",
            text_uk="Текст головної",
            sort=1,
        )
        Review.objects.create(
            placement=Review.Placement.ABOUT,
            author_uk="Про Нас Автор",
            text_uk="Текст про нас",
            sort=1,
        )
        about = Review.objects.filter(placement=Review.Placement.ABOUT)
        home = Review.objects.filter(placement=Review.Placement.HOME)
        self.assertEqual(about.count(), 1)
        self.assertEqual(about.first().author_uk, "Про Нас Автор")
        self.assertEqual(home.first().author_uk, "Дім Автор")


class AboutPopularFallbackTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.page = AboutPage.load()
        self.popular_block = HomeBlock.objects.get_or_create(
            key=HomeBlock.Key.POPULAR,
            defaults={"sort": 4},
        )[0]
        self.category = Category.objects.create(
            slug="about-fb-cat",
            name_uk="Категорія",
            is_active=True,
        )
        self.products = []
        for index in range(6):
            product = Product.objects.create(
                category=self.category,
                sku=f"AFB{index}",
                slug=f"about-fb-{index}",
                name_uk=f"Товар {index}",
                price_uah="10",
                price_eur="1",
                is_popular=True,
                is_active=True,
                sort=index,
            )
            self.products.append(product)

    def test_about_popular_caps_at_four_and_keeps_about_order(self):
        for index, product in enumerate(self.products[:5]):
            AboutPopularSlot.objects.create(page=self.page, product=product, sort=index)
        result = about_popular()
        self.assertEqual(result, self.products[:4])
        self.assertEqual(len(result), 4)

    def test_about_popular_tops_up_from_home_skipping_duplicates(self):
        AboutPopularSlot.objects.create(page=self.page, product=self.products[0], sort=0)
        AboutPopularSlot.objects.create(page=self.page, product=self.products[1], sort=1)
        for index, product in enumerate(self.products[1:5]):
            HomePopularSlot.objects.create(
                block=self.popular_block,
                product=product,
                sort=index,
            )
        home = home_popular()
        self.assertEqual(home, self.products[1:5])
        result = about_popular()
        self.assertEqual(result[0], self.products[0])
        self.assertEqual(result[1], self.products[1])
        self.assertEqual(result[2], self.products[2])
        self.assertEqual(result[3], self.products[3])
        self.assertEqual(len(result), 4)
        self.assertEqual(len({product.pk for product in result}), 4)

    def test_about_popular_empty_slots_use_home_max_four(self):
        for index, product in enumerate(self.products[:5]):
            HomePopularSlot.objects.create(
                block=self.popular_block,
                product=product,
                sort=index,
            )
        self.assertFalse(AboutPopularSlot.objects.filter(page=self.page).exists())
        result = about_popular()
        self.assertEqual(result, self.products[:4])
        self.assertEqual(len(result), 4)
