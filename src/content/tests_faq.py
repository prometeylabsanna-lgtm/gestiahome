from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.content.models import FooterLink, SiteSettings
from src.content.models_faq import FaqItem, FaqPage


class FaqPageRenderTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.page = FaqPage.load()
        self.page.title_uk = "Актуальні<br>питання"
        self.page.crumb_uk = "Актуальні питання"
        self.page.contact_title_uk = "Залишились питання?"
        self.page.contact_text_uk = "<p>Напишіть нам — ми допоможемо підібрати бокс.</p>"
        self.page.seo_title_uk = "FAQ SEO"
        self.page.save()
        FaqItem.objects.filter(page=self.page).delete()
        self.items = [
            FaqItem.objects.create(
                page=self.page,
                question_uk="Питання одне",
                answer_uk="<p>Відповідь одне</p>",
                sort=0,
                is_active=True,
            ),
            FaqItem.objects.create(
                page=self.page,
                question_uk="Питання два",
                answer_uk="<p>Відповідь два</p>",
                sort=1,
                is_active=True,
            ),
            FaqItem.objects.create(
                page=self.page,
                question_uk="Приховане",
                answer_uk="<p>Немає</p>",
                sort=2,
                is_active=False,
            ),
        ]
        self.site = SiteSettings.load()
        self.site.email = "gestiahome.company@gmail.com"
        self.site.instagram_url = "https://instagram.com/gestia"
        self.site.save()

    def test_faq_page_renders_active_items_in_sort_order(self):
        response = self.client.get(reverse("faq"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Питання одне", html)
        self.assertIn("Питання два", html)
        self.assertNotIn("Приховане", html)
        self.assertLess(html.index("Питання одне"), html.index("Питання два"))
        self.assertContains(response, 'aria-expanded=')
        self.assertContains(response, 'aria-controls="faq-a0"')
        self.assertContains(response, 'id="faq-a0"')
        self.assertContains(response, 'role="region"')
        self.assertContains(response, "Залишились питання?")
        self.assertContains(response, "gestiahome.company@gmail.com")
        self.assertContains(response, "https://instagram.com/gestia")
        self.assertContains(response, "css/nd/faq.css")
        self.assertContains(response, "js/nd/faq.js")

    def test_footer_and_header_contain_faq_link(self):
        FooterLink.objects.get_or_create(
            column="info",
            url_name="faq",
            defaults={
                "label_uk": "Актуальні питання",
                "label_en": "FAQ",
                "sort": 4,
            },
        )
        home = self.client.get(reverse("home"))
        self.assertContains(home, reverse("faq"))
        self.assertContains(home, "Актуальні питання")
        self.assertContains(home, 'class="nd-mega__faq"')


class FaqSeedMigrationTests(TestCase):
    def test_data_migration_seeded_four_questions(self):
        page = FaqPage.load()
        items = list(FaqItem.objects.filter(page=page).order_by("sort", "id"))
        self.assertEqual(len(items), 4)
        self.assertEqual(items[0].question_uk, "Що входить у святковий бокс?")
        self.assertIn("<ul>", items[0].answer_uk)
        self.assertIn("<li>", items[0].answer_uk)
        self.assertTrue(
            FooterLink.objects.filter(column="info", url_name="faq").exists()
        )


class FaqAdminTests(TestCase):
    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_superuser(
            username="faq-admin",
            email="faq-admin@example.com",
            password="pass",
        )
        self.client.force_login(self.user)
        FaqPage.load()

    def test_faq_admin_pages_open(self):
        for name in (
            "admin:content_faqheader_changelist",
            "admin:content_faqitem_changelist",
            "admin:content_faqcontact_changelist",
            "admin:content_faqseo_changelist",
        ):
            response = self.client.get(reverse(name), follow=True)
            self.assertEqual(response.status_code, 200, name)

    def test_faq_item_change_opens(self):
        item = FaqItem.objects.create(
            page=FaqPage.load(),
            question_uk="Адмін питання",
            answer_uk="<p>Так</p>",
            sort=0,
        )
        response = self.client.get(
            reverse("admin:content_faqitem_change", args=[item.pk])
        )
        self.assertEqual(response.status_code, 200)
