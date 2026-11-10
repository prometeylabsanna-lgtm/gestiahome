import re

from django.core.cache import cache
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase
from django.utils import translation
from django.utils.html import escape

from src.content.models_thankyou import ThankYouPage


def _render_richhtml_number(body: str, number) -> str:
    return Template("{% load richtext %}{{ body|richhtml_number:number }}").render(
        Context({"body": body, "number": number})
    )


def _next_input_values(html: str) -> list[str]:
    return re.findall(
        r'<input[^>]*\bname=["\']next["\'][^>]*\bvalue=["\']([^"\']*)["\']',
        html,
        flags=re.I,
    ) + re.findall(
        r'<input[^>]*\bvalue=["\']([^"\']*)["\'][^>]*\bname=["\']next["\']',
        html,
        flags=re.I,
    )


class RichHtmlNumberSecurityTests(SimpleTestCase):
    def test_number_in_text_becomes_span(self):
        html = _render_richhtml_number("<p>Замовлення № {number}</p>", "G-42")
        self.assertIn('<span data-qa="order-number">G-42</span>', html)
        self.assertIn("Замовлення № ", html)

    def test_number_in_href_and_title_keeps_attrs_without_span(self):
        body = (
            '<a href="https://example.com/o/{number}" title="№{number}">'
            "текст {number}</a>"
        )
        html = _render_richhtml_number(body, "G-7")

        self.assertNotIn('"<span', html)
        self.assertRegex(
            html,
            r'<a\b[^>]*href="https://example\.com/o/"[^>]*>',
        )
        self.assertRegex(html, r'<a\b[^>]*title="№"[^>]*>')
        for tag in re.findall(r"<[^>]+>", html):
            self.assertNotIn('"<span', tag)
            self.assertNotIn("{number}", tag)
        self.assertIn('<span data-qa="order-number">G-7</span>', html)

    def test_dangerous_number_is_escaped(self):
        evil = '<script>alert(1)</script>'
        html = _render_richhtml_number("<p>№ {number}</p>", evil)
        self.assertIn(f'<span data-qa="order-number">{escape(evil)}</span>', html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


class NextPathSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        page = ThankYouPage.load()
        page.order_text_uk = "<p>Замовлення № {number} оформлено.</p>"
        page.order_text_en = "<p>Order No. {number} placed.</p>"
        page.order_text_nonum_uk = "<p>Замовлення оформлено.</p>"
        page.order_text_nonum_en = "<p>Order placed.</p>"
        page.save()

    def test_thank_you_shows_number_but_next_omits_it(self):
        session = self.client.session
        session["orders_done"] = ["G-1"]
        session.save()

        response = self.client.get("/thank-you/?kind=order&number=G-1")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('data-qa="order-number"', html)
        self.assertIn("G-1", html)

        next_values = _next_input_values(html)
        self.assertTrue(next_values)
        for value in next_values:
            self.assertNotIn("number=", value)
            self.assertNotIn("G-1", value)

    def test_catalog_next_keeps_other_query(self):
        response = self.client.get("/katalog/?sort=price")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        next_values = _next_input_values(html)
        self.assertTrue(next_values)
        self.assertTrue(
            any(v == "/katalog/?sort=price" or v.endswith("/katalog/?sort=price") for v in next_values),
            next_values,
        )
        for value in next_values:
            if "katalog" in value:
                self.assertIn("sort=price", value)
