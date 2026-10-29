from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.content.models_discount import DiscountModal
from src.core.fields import WebPImageField


class DiscountModalTests(TestCase):
    def tearDown(self):
        translation.activate("uk")

    def test_disabled_hides_waitlist_popup(self):
        modal = DiscountModal.load()
        modal.enabled = False
        modal.save(update_fields=["enabled"])
        home = self.client.get("/")
        self.assertNotContains(home, 'id="waitlist-modal"')
        self.assertNotContains(home, "waitlist-modal.js")

    def test_enabled_modal_shows_single_text(self):
        modal = DiscountModal.load()
        modal.enabled = True
        modal.text_uk = "<p>Знижка на сет</p><p>Лише сьогодні</p>"
        modal.text_en = "<p>Set offer</p><p>Today only</p>"
        modal.delay_seconds = 15
        modal.save()

        translation.activate("uk")
        page = self.client.get("/")
        self.assertContains(page, 'id="waitlist-modal"')
        self.assertContains(page, "Знижка на сет")
        self.assertContains(page, "Лише сьогодні")
        self.assertContains(page, "Повідомити мене")
        self.assertContains(page, "waitlist-modal.js")

        translation.activate("en")
        english = self.client.get("/en/")
        self.assertContains(english, "Set offer")
        self.assertContains(english, "Notify me")

    def test_admin_has_simplified_fields(self):
        user = User.objects.create_superuser("editor", "editor@example.com", "pass-word-9")
        self.client.force_login(user)
        modal = DiscountModal.load()
        page = self.client.get(reverse("admin:content_discountmodal_change", args=[modal.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'name="text_uk"')
        self.assertContains(page, 'name="enabled"')
        self.assertContains(page, 'name="image"')
        self.assertNotContains(page, 'name="waitlist_title_uk"')
        self.assertNotContains(page, 'name="waitlist_p1_uk"')

    def test_image_field_is_webp(self):
        self.assertIsInstance(DiscountModal._meta.get_field("image"), WebPImageField)
