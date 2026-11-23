from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from src.catalog.models import CatalogCell, Category, Product
from src.content.models import HomeBlock, SiteSettings
from src.content.models_faq import FaqItem, FaqPage
from src.content.models_home_slots import HomePopularSlot
from src.content.models_thankyou import ThankYouPage
from src.content.models_ui import InterfaceCopy
from src.content.ui_text import text
from src.core.utils import localized


class FrenchLocaleTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        cache.clear()
        SiteSettings.objects.update_or_create(pk=1, defaults={"en_enabled": True, "fr_enabled": True})
        SiteSettings.objects.filter(pk=1).update(en_enabled=True, fr_enabled=True)
        cache.clear()
        self.hero, _ = HomeBlock.objects.get_or_create(key="hero", defaults={"sort": 1})
        self.hero.title_fr = "Art of modern hospitality"
        self.hero.text_fr = "Coffrets de fête pour décorer votre table vous-même"
        self.hero.save()
        popular, _ = HomeBlock.objects.get_or_create(key="popular", defaults={"sort": 4})
        popular.title_fr = "Produits populaires"
        popular.save()
        self.category = Category.objects.create(slug="fr-cat", name_uk="Бокси", name_fr="Coffrets", is_active=True)
        self.product = Product.objects.create(
            category=self.category,
            sku="FRBOX",
            slug="fr-box",
            name_uk="Святковий бокс",
            name_en="Festive box",
            name_fr="Coffret de fête",
            price_uah=Decimal("100"),
            price_eur=Decimal("3"),
            is_active=True,
            is_popular=True,
            stock_qty=100,
        )
        HomePopularSlot.objects.create(block=popular, product=self.product, sort=1)
        faq = FaqPage.load()
        faq.title_fr = "Bon à<br>savoir"
        faq.save()
        FaqItem.objects.create(
            page=faq,
            question_uk="Що в боксі?",
            question_fr="Que contient un coffret ?",
            answer_uk="<p>Українська відповідь</p>",
            answer_fr="<p>Le coffret de fête.</p>",
            sort=0,
            is_active=True,
        )
        thanks = ThankYouPage.load()
        thanks.order_title_fr = "Heureux de faire partie de vos traditions !"
        thanks.save()

    def tearDown(self):
        translation.activate("uk")
        cache.clear()

    def test_languages_include_french(self):
        self.assertEqual([code for code, _label in settings.LANGUAGES], ["uk", "en", "fr"])

    def test_home_is_french(self):
        page = self.client.get("/fr/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'lang="fr"')
        self.assertContains(page, "Art of modern hospitality")
        self.assertContains(page, "Coffrets de fête pour décorer votre table vous-même")
        self.assertContains(page, "Coffret de fête")
        self.assertContains(page, "UA")
        self.assertContains(page, "EN")
        self.assertContains(page, "FR")

    def test_product_faq_thanks_and_404(self):
        card = self.client.get("/fr/tovar/fr-box/")
        self.assertContains(card, "Coffret de fête")
        faq = self.client.get("/fr/aktualni-pytannia/")
        self.assertContains(faq, "Que contient un coffret ?")
        session = self.client.session
        session["orders_done"] = ["G-FR"]
        session.save()
        thanks = self.client.get("/fr/thank-you/?kind=order&number=G-FR")
        self.assertContains(thanks, "Heureux de faire partie de vos traditions !")

    @override_settings(DEBUG=False)
    def test_french_404(self):
        missing = self.client.get("/fr/no-such-gestia-page/")
        self.assertContains(missing, "Page introuvable", status_code=404)

    def test_empty_french_falls_back_to_ukrainian_not_english(self):
        self.product.name_fr = ""
        self.product.save(update_fields=["name_fr"])
        translation.activate("fr")
        self.assertEqual(localized(self.product, "name"), "Святковий бокс")
        page = self.client.get("/fr/tovar/fr-box/")
        self.assertContains(page, "Святковий бокс")
        self.assertNotContains(page, "Festive box")
        copy = InterfaceCopy.load()
        copy.cart_uk = "Кошик"
        copy.cart_en = "Basket"
        copy.cart_fr = ""
        copy.save()
        translation.activate("fr")
        self.assertEqual(text("cart"), "Кошик")

    def test_disabled_french_redirects_home(self):
        SiteSettings.objects.filter(pk=1).update(fr_enabled=False)
        cache.clear()
        response = self.client.get("/fr/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    def test_checkout_error_is_french(self):
        session = self.client.session
        session["cart"] = {"FRBOX": 1}
        session.save()
        page = self.client.get("/fr/zamovlennia/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Ce champ est obligatoire")
        posted = self.client.post("/fr/zamovlennia/", {"name": "", "consent": ""})
        self.assertEqual(posted.status_code, 200)
        self.assertContains(posted, "Ce champ est obligatoire")

    def test_product_admin_has_french_tab(self):
        user = User.objects.create_superuser("fr-admin", "fr@example.com", "pass-word-9")
        self.client.force_login(user)
        page = self.client.get(reverse("admin:catalog_product_change", args=[self.product.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Français")
        self.assertContains(page, 'name="name_fr"')

    def test_french_guillemets_have_no_inner_space(self):
        from pathlib import Path

        from src.content.french_copy import MENU_ITEMS, PRODUCTS, tighten_fr_guillemets

        self.assertEqual(tighten_fr_guillemets("« Ukrainien »"), "«Ukrainien»")
        self.assertEqual(tighten_fr_guillemets("«Ukrainien»"), "«Ukrainien»")
        for data in PRODUCTS.values():
            for value in data.values():
                if isinstance(value, str):
                    self.assertNotIn("« ", value)
                    self.assertNotIn(" »", value)
        for fr in MENU_ITEMS.values():
            self.assertNotIn("« ", fr)
            self.assertNotIn(" »", fr)
        root = Path(settings.BASE_DIR)
        for rel in (
            "src/content/french_copy.py",
            "src/content/french_copy_pages.py",
            "src/content/legal_copy_fr.py",
            "locale/fr/LC_MESSAGES/django.po",
        ):
            blob = (root / rel).read_text(encoding="utf-8")
            self.assertNotIn("« ", blob, rel)
            self.assertNotIn(" »", blob, rel)

    def test_english_copy_uses_guillemets(self):
        from pathlib import Path

        from src.core.utils import curly_to_guillemets

        self.assertEqual(curly_to_guillemets("Easter box “Ukrainian”"), "Easter box «Ukrainian»")
        blob = (Path(settings.BASE_DIR) / "locale" / "en" / "LC_MESSAGES" / "django.po").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("“", blob)
        self.assertNotIn("”", blob)

    def test_french_copy_covers_collection_addons(self):
        from src.content.french_copy import CATEGORY_NAMES, PRODUCTS

        self.assertEqual(CATEGORY_NAMES["kolektsiini-dodatky"], "Compléments de collections")
        for sku, slug in (
            ("COL-KVITKA", "kvitka-dusha"),
            ("COL-KORINNIA", "korinnia"),
            ("COL-KRYSHTAL", "rodynnyi-kryshtal"),
            ("COL-TARTAN", "tartan"),
            ("COL-DYTYNSTVO", "dytynstvo"),
            ("COL-SPADSHCHYNA", "spadshchyna"),
            ("ADD-HOLDERS", "addon-pidsvichnyky"),
            ("ADD-HOLDERS-2", "addon-pidsvichnyky-2"),
            ("ADD-HOLDERS-EXTRA", "addon-pidsvichnyky-extra"),
            ("ADD-NAPKIN", "addon-llyani-servetky"),
            ("ADD-NAPKIN-PLAID", "addon-servetky-klitynka"),
            ("ADD-RINGS", "addon-kiltsia"),
        ):
            self.assertEqual(PRODUCTS[sku]["slug"], slug)
            self.assertTrue(PRODUCTS[sku]["name_fr"].strip())

        from src.content.french_copy import STUDIO_ADDRESS
        from src.content.french_copy_pages import ABOUT_FR

        self.assertEqual(ABOUT_FR["title_fr"], "Salut, je suis Gestia")
        self.assertIn("Gestia", ABOUT_FR["title_fr"])
        self.assertNotEqual(ABOUT_FR["title_fr"], "À propos")
        self.assertEqual(STUDIO_ADDRESS["fr"], "Kyiv, atelier Gestia")

    def test_cell_stamp_gets_french_label(self):
        import importlib

        copy = importlib.import_module("src.catalog.migrations.0025_fill_catalogcell_label_fr")
        cell = CatalogCell.objects.create(
            product=self.product,
            band=0,
            layout=CatalogCell.Layout.ROW,
            role=CatalogCell.Role.GRID,
            sort=1,
            price_uah=Decimal("10"),
            label_uk="Бокс Великодній «Український»",
        )
        kept = CatalogCell.objects.create(
            product=self.product,
            band=0,
            layout=CatalogCell.Layout.ROW,
            role=CatalogCell.Role.GRID,
            sort=2,
            price_uah=Decimal("10"),
            label_uk="Бокс Великодній «Український»",
            label_fr="Personnalisé",
        )
        copy.fill_catalogcell_label_fr(apps, None)
        cell.refresh_from_db()
        kept.refresh_from_db()
        self.assertEqual(cell.label_fr, "Coffret de Pâques «Ukrainien»")
        self.assertEqual(kept.label_fr, "Personnalisé")
        with translation.override("fr"):
            self.assertEqual(cell.label, "Coffret de Pâques «Ukrainien»")
        with translation.override("uk"):
            self.assertEqual(cell.label, "Бокс Великодній «Український»")
