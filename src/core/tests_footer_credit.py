from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

CREDIT_URL = "https://www.prometeylabs.com/internet-shop-v2/"


class FooterDeveloperLinkTests(TestCase):
    def setUp(self):
        translation.activate("uk")

    def test_home_has_nofollow_credit_link(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, CREDIT_URL)
        self.assertContains(response, 'rel="nofollow noopener noreferrer"')
        self.assertContains(response, ">PrometeyLabs</a>")
        self.assertContains(response, "site-footer__credit-link")
        self.assertContains(response, "Зроблено")

    def test_english_home_keeps_credit_link(self):
        response = self.client.get("/en/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, CREDIT_URL)
        self.assertContains(response, ">PrometeyLabs</a>")

    def test_inner_pages_show_credit_without_link(self):
        for name in ("about", "privacy", "catalog", "shipping"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertContains(response, "PrometeyLabs")
            self.assertContains(response, "site-footer__credit-name")
            self.assertNotContains(response, CREDIT_URL)
            self.assertNotContains(response, "site-footer__credit-link")

    @override_settings(DEBUG=False)
    def test_not_found_has_no_credit_link(self):
        response = self.client.get("/nema-takoyi-storinky-gestia/")
        self.assertEqual(response.status_code, 404)
        html = response.content.decode()
        self.assertIn("PrometeyLabs", html)
        self.assertIn("site-footer__credit-name", html)
        self.assertNotIn(CREDIT_URL, html)
        self.assertNotIn("site-footer__credit-link", html)
