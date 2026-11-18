from django.core.cache import cache
from django.test import TestCase
from django.utils import translation

from src.commerce.models import Inquiry
from src.content.models import SiteSettings
from src.core.ratelimit import HONEYPOT_FIELD


def _save_site(**fields):
    site = SiteSettings.load()
    for name, value in fields.items():
        setattr(site, name, value)
    site.save()
    cache.clear()
    return site


class ContactsPageTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        cache.clear()

    def test_page_is_indexable_and_lists_real_contacts_only(self):
        _save_site(
            phone="+380 67 123 45 67",
            email="hello@gestia-shop.com.ua",
            address_uk="Київ, майстерня Gestia",
            address_en="Kyiv, Gestia studio",
            instagram_url="https://www.instagram.com/",
            pinterest_url="https://www.pinterest.com/gestia/",
            telegram_url="https://t.me/",
        )
        page = self.client.get("/kontakty/")
        html = page.content.decode()
        main = html.split("<main", 1)[1].split("</main>", 1)[0]
        self.assertEqual(page.status_code, 200)
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn("Контакти Gestia Home — телефон, пошта та майстерня", html)
        self.assertIn('rel="canonical" href="http://testserver/kontakty/"', html)
        self.assertIn('hreflang="en" href="http://testserver/en/kontakty/"', html)
        self.assertIn('"@type":"ContactPage"', html)
        self.assertIn("BreadcrumbList", html)
        self.assertNotIn("noindex", html)
        self.assertIn("+380 67 123 45 67", main)
        self.assertIn("hello@gestia-shop.com.ua", main)
        self.assertIn("Київ, майстерня Gestia", main)
        self.assertIn("https://www.pinterest.com/gestia/", main)
        self.assertNotIn("instagram.com/", main)
        self.assertNotIn("https://www.instagram.com/", html.split('application/ld+json">', 1)[1].split("</script>", 1)[0])
        self.assertIn("Зв'язатись з нами", html)
        self.assertIn('href="/katalog/"', html)
        self.assertIn('href="/dostavka-ta-oplata/"', html)
        self.assertIn('href="/aktualni-pytannia/"', html)

    def test_placeholder_phone_stays_hidden(self):
        _save_site(phone="+380000000000", email="editor@example.com", address_uk="", instagram_url="")
        page = self.client.get("/kontakty/")
        main = page.content.decode().split("<main", 1)[1].split("</main>", 1)[0]
        self.assertNotIn("+380000000000", main)
        self.assertNotIn("editor@example.com", main)
        self.assertNotIn(">Адреса<", main)

    def test_sitemap_robots_and_llms_include_the_page(self):
        robots = self.client.get("/robots.txt").content.decode()
        self.assertIn("Allow: /kontakty/\n", robots)
        self.assertIn("Allow: /en/kontakty/\n", robots)
        self.assertIn("/kontakty/", self.client.get("/sitemap.xml").content.decode())
        self.assertIn("/kontakty/", self.client.get("/llms.txt").content.decode())
        self.assertIn("/en/kontakty/", self.client.get("/llms.txt").content.decode())

    def test_valid_post_saves_inquiry_and_redirects(self):
        response = self.client.post(
            "/kontakty/",
            {"name": "Оля", "phone": "+380671112233", "message": "Питання про бокс", "consent": "on"},
        )
        self.assertRedirects(response, "/thank-you/?kind=contact", fetch_redirect_response=False)
        self.assertEqual(Inquiry.objects.filter(kind=Inquiry.Kind.CONTACT).count(), 1)

    def test_invalid_post_keeps_the_page(self):
        response = self.client.post("/kontakty/", {"name": "", "phone": "", "consent": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1")
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_honeypot_pretends_success(self):
        response = self.client.post(
            "/kontakty/",
            {
                "name": "Оля",
                "phone": "+380671112233",
                "consent": "on",
                HONEYPOT_FIELD: "bot",
            },
        )
        self.assertRedirects(response, "/thank-you/?kind=contact", fetch_redirect_response=False)
        self.assertEqual(Inquiry.objects.count(), 0)
