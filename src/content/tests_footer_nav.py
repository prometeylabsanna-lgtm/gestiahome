from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category
from src.content.footer_nav import FOOTER_CATEGORY_LIMIT, build_footer_columns
from src.content.models import FooterLink
from src.content.models_legal import LegalPage


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

    def test_legal_column_prefers_footer_link_sort_order(self):
        FooterLink.objects.filter(column="legal").delete()
        FooterLink.objects.create(
            column="legal",
            label_uk="Політика cookies",
            url_name="cookies",
            sort=3,
        )
        FooterLink.objects.create(
            column="legal",
            label_uk="Публічний договір (оферта)",
            url_name="offer",
            sort=1,
        )
        FooterLink.objects.create(
            column="legal",
            label_uk="Політика конфіденційності",
            url_name="privacy",
            sort=2,
        )
        columns = build_footer_columns()
        labels = [item.label for item in columns["legal"]]
        hrefs = [item.href for item in columns["legal"]]
        self.assertEqual(
            labels,
            [
                "Публічний договір (оферта)",
                "Політика конфіденційності",
                "Політика cookies",
            ],
        )
        self.assertEqual(
            hrefs,
            [reverse("offer"), reverse("privacy"), reverse("cookies")],
        )
        self.assertNotIn(reverse("shipping"), hrefs)

    def test_legal_column_falls_back_to_legal_pages(self):
        FooterLink.objects.filter(column="legal").delete()
        self.assertTrue(LegalPage.objects.exists())
        columns = build_footer_columns()
        hrefs = [item.href for item in columns["legal"]]
        self.assertEqual(len(hrefs), LegalPage.objects.count())
        self.assertIn(reverse("shipping"), hrefs)
