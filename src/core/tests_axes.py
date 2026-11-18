from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from src.commerce.models import Inquiry


@override_settings(AXES_ENABLED=True)
class AdminLockoutTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user(
            "staff",
            "staff@example.com",
            "correct-horse",
            is_staff=True,
        )

    def _login(self, password):
        return self.client.post(
            reverse("admin:login"),
            {"username": "staff", "password": password},
        )

    def test_fifth_failure_locks_and_sixth_stays_locked(self):
        for _ in range(4):
            response = self._login("wrong-pass")
            self.assertEqual(response.status_code, 200)
        fifth = self._login("wrong-pass")
        self.assertEqual(fifth.status_code, 429)
        sixth = self._login("wrong-pass")
        self.assertEqual(sixth.status_code, 429)

    def test_success_resets_failure_counter(self):
        for _ in range(4):
            self.assertEqual(self._login("wrong-pass").status_code, 200)
        signed_in = self._login("correct-horse")
        self.assertEqual(signed_in.status_code, 302)
        self.client.logout()
        self.assertEqual(self._login("wrong-pass").status_code, 200)

    def test_lockout_does_not_block_contact_form(self):
        for _ in range(5):
            self._login("wrong-pass")
        response = self.client.post(
            "/zvorotnyi-zvyazok/",
            {
                "name": "Оля",
                "phone": "+380671112233",
                "message": "Питання щодо доставки",
                "consent": "on",
            },
        )
        self.assertContains(response, "Дякуємо")
        self.assertEqual(Inquiry.objects.count(), 1)
