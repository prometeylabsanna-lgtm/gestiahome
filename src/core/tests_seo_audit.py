import re

from src.content.models import HomeBlock, SiteSettings
from src.core.seo import is_placeholder_contact
from src.core.tests_seo import SeoFixture, _h1_count, _ld, _meta_description

_UK_TITLE = "Декор для дому, текстиль і флористика"
_EN_TITLE = "Home decor, textiles and floristry"
_SEO_TITLE_UK = "Святкові бокси для сервірування столу"
_SEO_TITLE_EN = "Festive boxes for a table from Gestia"
_SEO_DESC_UK = (
    "Святкові бокси, свічки й текстиль для сервірування святкового столу від Gestia Home."
)
_SEO_DESC_EN = "Festive table boxes, candles and home textiles from Gestia Home."
_PHONE = "+380 67 123 45 67"
_EMAIL = "hello@gestia-shop.com.ua"
_ADDRESS_UK = "Київ, вул. Тестова, 1"
_ADDRESS_EN = "Kyiv, Testova St, 1"
_INSTAGRAM = "https://instagram.com/gestia.home"
_PINTEREST = "https://www.pinterest.com/gestia/"


def _title(response):
    return re.search(r"<title>(.*?)</title>", response.content.decode()).group(1)


def _organization(response):
    for payload in _ld(response):
        for node in payload.get("@graph") or []:
            if node.get("@type") == "Organization":
                return node
    return {}


def _h1_nodes(response):
    return re.findall(r"<h1\b([^>]*)>(.*?)</h1>", response.content.decode(), flags=re.I | re.S)


def _save_site(**fields):
    site = SiteSettings.objects.get(pk=1)
    for name, value in fields.items():
        setattr(site, name, value)
    site.save()
    return site


class CategorySeoTests(SeoFixture):
    def test_category_meta_uses_translation_or_current_fallback(self):
        path = self.category.get_absolute_url()
        page = self.client.get(path)
        self.assertEqual(_title(page), "Святкові бокси — Gestia")
        self.assertEqual(_meta_description(page), "Святкові бокси. Gestia")

        self.category.seo_title_uk = _SEO_TITLE_UK
        self.category.seo_title_en = _SEO_TITLE_EN
        self.category.seo_description_uk = _SEO_DESC_UK
        self.category.seo_description_en = _SEO_DESC_EN
        self.category.save()

        uk = self.client.get(path)
        en = self.client.get(f"/en{path}")
        self.assertEqual(_title(uk), _SEO_TITLE_UK)
        self.assertEqual(_meta_description(uk), _SEO_DESC_UK)
        self.assertEqual(_title(en), _SEO_TITLE_EN)
        self.assertEqual(_meta_description(en), _SEO_DESC_EN)
        self.assertIn(
            f'<h1 class="visually-hidden">{self.category.name_uk}</h1>',
            uk.content.decode(),
        )

        self.category.seo_title_en = ""
        self.category.seo_description_en = ""
        self.category.save()
        en_fallback = self.client.get(f"/en{path}")
        self.assertEqual(_title(en_fallback), _SEO_TITLE_UK)
        self.assertEqual(_meta_description(en_fallback), _SEO_DESC_UK)

        self.category.seo_title_uk = "   "
        self.category.seo_description_uk = "   "
        self.category.save()
        cleared = self.client.get(f"/en{path}")
        self.assertEqual(_title(cleared), "Festive boxes — Gestia")
        self.assertEqual(_meta_description(cleared), "Festive boxes. Gestia")


class ContactSeoTests(SeoFixture):
    def test_placeholder_rules(self):
        for phone in ("", "   ", "+380 00 000 00 00", "+380000000000", "000 000 0000", "+380 000"):
            self.assertTrue(is_placeholder_contact(phone, "phone"), phone)
        self.assertFalse(is_placeholder_contact(_PHONE, "phone"))
        for email in (
            "",
            "editor@example.com",
            "editor@example.org",
            "editor@example.net",
            "editor@sub.example.com",
            "staff@mail.local",
            "staff@name.example",
            "staff@name.test",
        ):
            self.assertTrue(is_placeholder_contact(email, "email"), email)
        self.assertFalse(is_placeholder_contact(_EMAIL, "email"))
        self.assertFalse(is_placeholder_contact("hello@example.com.ua", "email"))

    def test_placeholder_contacts_stay_out_of_llms_and_jsonld(self):
        _save_site(
            phone="+380 00 000 00 00",
            email="editor@example.com",
            address_uk=_ADDRESS_UK,
            address_en="",
            instagram_url=_INSTAGRAM,
            pinterest_url="",
        )
        llms = self.client.get("/llms.txt").content.decode()
        org = _organization(self.client.get("/"))
        self.assertNotIn("Телефон:", llms)
        self.assertNotIn("Email:", llms)
        self.assertNotIn("+380 00 000 00 00", llms)
        self.assertNotIn("editor@example.com", llms)
        self.assertNotIn("telephone", org)
        self.assertNotIn("email", org)
        self.assertIn(f"- Адреса: {_ADDRESS_UK}", llms)
        self.assertIn(f"- {_INSTAGRAM}", llms)
        self.assertEqual(org["address"]["streetAddress"], _ADDRESS_UK)
        self.assertEqual(org["sameAs"], [_INSTAGRAM])

    def test_real_contacts_appear_in_llms_and_jsonld(self):
        _save_site(
            phone=_PHONE,
            email=_EMAIL,
            address_uk=_ADDRESS_UK,
            address_en=_ADDRESS_EN,
            instagram_url=_INSTAGRAM,
            pinterest_url=_PINTEREST,
        )
        llms = self.client.get("/llms.txt").content.decode()
        uk = _organization(self.client.get("/"))
        en = _organization(self.client.get("/en/"))
        self.assertIn(f"- Телефон: {_PHONE}", llms)
        self.assertIn(f"- Email: {_EMAIL}", llms)
        self.assertIn(f"- Адреса: {_ADDRESS_UK}", llms)
        self.assertIn(f"- Адреса: {_ADDRESS_EN}", llms)
        self.assertIn(f"- {_INSTAGRAM}", llms)
        self.assertIn(f"- {_PINTEREST}", llms)
        self.assertEqual(uk["telephone"], _PHONE)
        self.assertEqual(uk["email"], _EMAIL)
        self.assertEqual(en["telephone"], _PHONE)
        self.assertEqual(en["email"], _EMAIL)
        self.assertEqual(uk["address"]["streetAddress"], _ADDRESS_UK)
        self.assertEqual(en["address"]["streetAddress"], _ADDRESS_EN)
        self.assertEqual(uk["sameAs"], [_INSTAGRAM, _PINTEREST])


class HeadingSeoTests(SeoFixture):
    def test_one_h1_when_home_has_no_hero(self):
        self.assertFalse(HomeBlock.objects.filter(key="hero").exists())
        for path in ("/", "/en/", "/katalog/", "/en/katalog/"):
            page = self.client.get(path)
            nodes = _h1_nodes(page)
            self.assertEqual(len(nodes), 1, path)
            self.assertEqual(_h1_count(page), 1, path)
            self.assertIn("visually-hidden", nodes[0][0])
        self.assertIn("Gestia Home", _h1_nodes(self.client.get("/"))[0][1])
        self.assertIn("Gestia Home", _h1_nodes(self.client.get("/en/"))[0][1])
        self.assertIn("Каталог", _h1_nodes(self.client.get("/katalog/"))[0][1])
        self.assertIn("Catalogue", _h1_nodes(self.client.get("/en/katalog/"))[0][1])

    def test_visible_hero_is_the_only_h1(self):
        HomeBlock.objects.create(key="hero", title_uk=_UK_TITLE, title_en=_EN_TITLE)
        for path, slogan in ({"/": _UK_TITLE, "/en/": _EN_TITLE}).items():
            page = self.client.get(path)
            nodes = _h1_nodes(page)
            self.assertEqual(len(nodes), 1, path)
            self.assertEqual(_h1_count(page), 1, path)
            self.assertNotIn("visually-hidden", nodes[0][0])
            self.assertIn('alt="Gestia Home"', nodes[0][1])
            self.assertIn(slogan, page.content.decode())
        for path in ("/katalog/", "/en/katalog/"):
            page = self.client.get(path)
            nodes = _h1_nodes(page)
            self.assertEqual(len(nodes), 1, path)
            self.assertEqual(_h1_count(page), 1, path)
            self.assertIn("visually-hidden", nodes[0][0])
