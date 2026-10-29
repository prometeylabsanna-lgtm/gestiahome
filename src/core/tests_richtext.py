from decimal import Decimal

from django.conf import settings
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse

from src.catalog.models import Category, Product
from src.core.html_sanitize import sanitize_rich_html


class RichTextSanitizeTests(TestCase):
    def test_allowlist_keeps_formatting(self):
        raw = (
            "<h2>Заголовок</h2><p>Текст <strong>жирний</strong> <em>курсив</em> "
            '<u>підкреслення</u></p><blockquote>цитата</blockquote>'
            '<ul><li>пункт</li></ul><span style="color:red">акцент</span>'
        )
        cleaned = sanitize_rich_html(raw)
        self.assertIn("<h2>Заголовок</h2>", cleaned)
        self.assertIn("<strong>жирний</strong>", cleaned)
        self.assertIn("<em>курсив</em>", cleaned)
        self.assertIn("<u>підкреслення</u>", cleaned)
        self.assertIn("<blockquote>цитата</blockquote>", cleaned)
        self.assertIn("<li>пункт</li>", cleaned)
        self.assertIn("<span>акцент</span>", cleaned)
        self.assertNotIn("style", cleaned)

    def test_strips_script_handlers_and_bad_links(self):
        raw = (
            '<p onclick="alert(1)">ok</p><script>alert(1)</script>'
            '<a href="javascript:alert(1)" target="_blank">bad</a>'
            '<a href="https://gestia.example/katalog/" target="_blank" style="color:red">good</a>'
            "<img src=x onerror=alert(1)><h1>ні</h1>"
        )
        cleaned = sanitize_rich_html(raw)
        self.assertNotIn("script", cleaned)
        self.assertNotIn("onclick", cleaned)
        self.assertNotIn("javascript:", cleaned)
        self.assertNotIn("<img", cleaned)
        self.assertNotIn("<h1", cleaned)
        self.assertIn("ні", cleaned)
        self.assertIn('href="https://gestia.example/katalog/"', cleaned)
        self.assertIn('target="_blank"', cleaned)
        self.assertIn('rel="noopener noreferrer"', cleaned)
        self.assertNotIn("style", cleaned)

    def test_empty_value(self):
        self.assertEqual(sanitize_rich_html(None), "")
        self.assertEqual(sanitize_rich_html("   "), "")

    def test_template_filter_renders_cleaned_html(self):
        html = Template("{% load richtext %}{{ body|richhtml }}").render(
            Context({"body": "<script>x</script><p>ok</p>"})
        )
        self.assertIn("<p>ok</p>", html)
        self.assertNotIn("script", html)

    def test_richhtml_preserves_plain_linebreaks(self):
        html = Template("{% load richtext %}{{ body|richhtml }}").render(
            Context({"body": "рядок один\n\nрядок два"})
        )
        self.assertIn("<p>", html)
        self.assertIn("рядок один", html)
        self.assertIn("рядок два", html)

    def test_richinline_unwraps_single_paragraph(self):
        html = Template("{% load richtext %}{{ body|richinline }}").render(
            Context({"body": "<p>коротко <strong>тут</strong></p>"})
        )
        self.assertEqual(html, "коротко <strong>тут</strong>")

    def test_signal_sanitizes_product_description(self):
        category = Category.objects.create(slug="box", name_uk="Бокс")
        kept = Product.objects.create(
            category=category,
            sku="PLAIN",
            slug="plain",
            name_uk="Plain",
            price_uah=Decimal("10"),
            price_eur=Decimal("1"),
            description_uk="<p>keep</p>",
        )
        self.assertEqual(kept.description_uk, "<p>keep</p>")

        marked = Product.objects.create(
            category=category,
            sku="MARKED",
            slug="marked",
            name_uk="Marked",
            price_uah=Decimal("10"),
            price_eur=Decimal("1"),
            description_uk='<script>bad</script><p onclick="x">ok</p>',
        )
        marked.refresh_from_db()
        self.assertEqual(marked.description_uk, "<p>ok</p>")

    def test_tinymce_is_configured_and_not_on_the_storefront(self):
        config = settings.TINYMCE_DEFAULT_CONFIG
        self.assertEqual(config["language"], "uk")
        self.assertEqual(config["width"], "100%")
        self.assertFalse(config["menubar"])
        self.assertIn("blockquote", config["toolbar"])
        self.assertNotIn("image", config["toolbar"])
        self.assertIn("h2", config["valid_elements"])
        self.assertNotIn("style", config["valid_elements"])
        self.assertEqual(reverse("tinymce-filebrowser"), "/tinymce/filebrowser/")
        home = self.client.get("/")
        self.assertNotContains(home, "tinymce.min.js")
        self.assertNotContains(home, "char_counter.js")

    def test_force_tinymce_overrides_custom_form_widgets(self):
        from django import forms
        from tinymce.widgets import TinyMCE

        from src.content.models import HomeBlock
        from src.core.admin_tinymce import force_tinymce

        class WeirdForm(forms.ModelForm):
            class Meta:
                model = HomeBlock
                fields = ("text_uk", "text_en")
                widgets = {
                    "text_uk": forms.Textarea(attrs={"rows": 2}),
                    "text_en": forms.Textarea(attrs={"rows": 2}),
                }

        form = WeirdForm()
        self.assertNotIsInstance(form.fields["text_uk"].widget, TinyMCE)
        force_tinymce(form, ("text_uk", "text_en"), short=True)
        self.assertIsInstance(form.fields["text_uk"].widget, TinyMCE)
        self.assertIsInstance(form.fields["text_en"].widget, TinyMCE)
