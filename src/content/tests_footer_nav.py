from django.test import TestCase
from django.utils import translation

from src.catalog.models import Category
from src.content.footer_nav import FOOTER_CATEGORY_LIMIT, build_footer_columns


class FooterNavTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        for index in range(1, 6):
            Category.objects.create(
                slug=f"cat-{index}",
                name_uk=f"Кат {index}",
                sort=index,
                is_active=True,
            )

    def test_category_column_matches_design_limit(self):
        columns = build_footer_columns()
        labels = [item.label for item in columns["category"]]
        self.assertEqual(labels[0], "Усі товари")
        self.assertEqual(len(labels), 1 + FOOTER_CATEGORY_LIMIT)
        self.assertEqual(labels[1:], ["Кат 1", "Кат 2", "Кат 3"])
        self.assertNotIn("Кат 4", labels)
        self.assertNotIn("Кат 5", labels)
