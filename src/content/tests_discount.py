from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import translation

from src.content.models_discount import DiscountModal
from src.core.fields import WebPImageField


class DiscountModalRemovedTests(TestCase):
    def tearDown(self):
        translation.activate("uk")

    def test_popup_is_gone_even_when_enabled(self):
        modal = DiscountModal.load()
        modal.enabled = True
        modal.text_uk = "<p>Знижка на сет</p>"
        modal.save()
        home = self.client.get("/")
        self.assertNotContains(home, 'id="waitlist-modal"')
        self.assertNotContains(home, "waitlist-modal.js")
        self.assertNotContains(home, "Знижка на сет")

    def test_admin_is_unregistered(self):
        user = User.objects.create_superuser("editor", "editor@example.com", "pass-word-9")
        self.client.force_login(user)
        with self.assertRaises(NoReverseMatch):
            reverse("admin:content_discountmodal_changelist")

    def test_image_field_is_webp(self):
        self.assertIsInstance(DiscountModal._meta.get_field("image"), WebPImageField)
