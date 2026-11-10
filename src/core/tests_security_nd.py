import re

from django.template import Context, Template
from django.test import SimpleTestCase
from django.utils.html import escape


def _render_richhtml_number(body: str, number) -> str:
    return Template("{% load richtext %}{{ body|richhtml_number:number }}").render(
        Context({"body": body, "number": number})
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
