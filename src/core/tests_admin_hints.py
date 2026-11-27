from decimal import Decimal

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from src.catalog.models import Category, Product, ProductAttribute, ProductAttributeGroup
from src.content.models import AboutPage, HomeBlock, HomeCollection, SiteSettings
from src.content.models_faq import FaqItem, FaqPage
from src.content.models_legal import LegalPage
from src.content.models_menu import MenuGroup, MenuGroupItem
from src.content.models_styles import PageStyle
from src.content.models_thankyou import ThankYouPage
from src.core.admin_hints import (
    ABOUT_CTA,
    ADDRESS,
    ALT_HINT,
    APPROACH_TEXT,
    BANNER_TEXT,
    BANNER_TITLE,
    BOX_ITEMS,
    CARD_IMAGE,
    CATEGORY_MEDIA,
    COL_BLOCK_LINK,
    COL_LABEL,
    COL_PRODUCT,
    COL_SLUG,
    COL_STORY,
    CREDIT,
    EMPTY_LOCALE_HINT,
    FAQ_ACTIVE,
    FAQ_CRUMB,
    FAQ_IMAGE,
    FONT_FAMILY,
    FORM_TITLE,
    GESTIA_QUOTE,
    GROUP_SLUG,
    IMAGE_LARGE,
    INTRO_LEFT,
    IS_FILTERABLE,
    IS_POPULAR,
    IS_SALE,
    LANG_OFF,
    LEGAL_BODY,
    LEGAL_DATE,
    MENU_COLLECTION,
    MENU_FEATURED,
    ORDER_TEXT,
    ORDER_TEXT_NONUM,
    PRICE,
    SEO_TITLE,
    SHORT_NAV,
    SHOW_ON_PDP,
    SLUG_AUTO,
    SOCIAL_URL,
    STOCK_QTY,
    TELEGRAM_URL,
    TEXT_COLOR,
    THANKS_LINK,
)
from src.core.admin_lang import language_tabs


class LanguageTabHintTests(SimpleTestCase):
    def test_empty_locale_note_only_on_tabs_with_fields(self):
        filled = language_tabs(uk_fields=("title_uk",), en_fields=("title_en",))
        self.assertEqual(filled[1][1]["description"], EMPTY_LOCALE_HINT)
        self.assertEqual(filled[2][1]["description"], EMPTY_LOCALE_HINT)

        empty = language_tabs(uk_fields=("image",), en_fields=())
        self.assertNotIn("description", empty[1][1])
        self.assertNotIn("description", empty[2][1])

        custom = language_tabs(
            uk_fields=("title_uk",),
            en_fields=("title_en",),
            en_description="Свій опис",
        )
        self.assertEqual(custom[1][1]["description"], "Свій опис")
        self.assertEqual(custom[2][1]["description"], EMPTY_LOCALE_HINT)

    def test_banner_media_tabs_stay_without_fallback_note(self):
        from src.content.admin_home_banners import HomeBannerMediaAdmin

        self.assertNotIn("description", HomeBannerMediaAdmin.fieldsets[1][1])
        self.assertNotIn("description", HomeBannerMediaAdmin.fieldsets[2][1])


class AdminHintRenderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("hints", "hints@example.com", "pass-word-9")
        self.client.force_login(self.user)
        SiteSettings.load()
        AboutPage.load()
        FaqPage.load()
        ThankYouPage.load()
        PageStyle.objects.get_or_create(page=PageStyle.Key.GLOBAL)
        self.category = Category.objects.create(slug="hints-cat", name_uk="Бокси")
        self.product = Product.objects.create(
            category=self.category,
            sku="HINT-1",
            slug="hint-box",
            name_uk="Бокс",
            price_uah=Decimal("10"),
            price_eur=Decimal("1"),
        )
        self.hero, _ = HomeBlock.objects.get_or_create(
            key=HomeBlock.Key.HERO,
            defaults={"sort": 1, "title_uk": "Банер"},
        )
        self.locale, _ = HomeBlock.objects.get_or_create(
            key=HomeBlock.Key.LOCALE,
            defaults={"sort": 8},
        )
        self.collections, _ = HomeBlock.objects.get_or_create(
            key=HomeBlock.Key.COLLECTIONS,
            defaults={"sort": 2, "title_uk": "Колекції"},
        )
        self.popular, _ = HomeBlock.objects.get_or_create(
            key=HomeBlock.Key.POPULAR,
            defaults={"sort": 4, "title_uk": "Популярні"},
        )
        self.collection = HomeCollection.objects.create(title_uk="Свято", slug="sviatkova")
        self.offer = LegalPage.objects.filter(key=LegalPage.Key.OFFER).first()
        if self.offer is None:
            self.offer = LegalPage.objects.create(key=LegalPage.Key.OFFER, title_uk="Договір")
        self.question = FaqItem.objects.create(page=FaqPage.load(), question_uk="Як доглядати?")
        self.group = ProductAttributeGroup.objects.create(slug="hint-color", name_uk="Колір")
        self.attr = ProductAttribute.objects.create(group=self.group, slug="white", name_uk="Білий")
        self.menu = MenuGroup.objects.create(title_uk="Стіл")
        MenuGroupItem.objects.create(group=self.menu, label_uk="Бокси", collection=self.collection)

    def _open(self, url_name, pk, *needles, absent=()):
        page = self.client.get(reverse(url_name, args=[pk]))
        self.assertEqual(page.status_code, 200, url_name)
        for needle in needles:
            self.assertContains(page, needle, msg_prefix=url_name)
        for needle in absent:
            self.assertNotContains(page, needle, msg_prefix=url_name)
        return page

    def test_change_forms_show_editor_hints(self):
        stale = (
            "One item per line",
            "kolektsiia/<slug>",
            "Лише wide",
            "для переносу рядка",
            "підставляється безпечно",
            "substituted safely",
            "створиться з назви",
            "Confirm button label",
            "Opens the region step",
            "Якщо порожньо — на сайті лишається український текст.",
        )
        self._open(
            "admin:content_homebannertext_change",
            self.hero.pk,
            BANNER_TITLE,
            BANNER_TEXT,
            SEO_TITLE,
            EMPTY_LOCALE_HINT,
            absent=stale,
        )
        self._open(
            "admin:content_homebannermedia_change",
            self.hero.pk,
            "1442×871",
            absent=(EMPTY_LOCALE_HINT,),
        )
        self._open(
            "admin:content_homecollection_change",
            self.collection.pk,
            COL_SLUG,
            COL_LABEL,
            COL_STORY,
            COL_PRODUCT,
            BOX_ITEMS,
            IMAGE_LARGE,
            ALT_HINT,
            SEO_TITLE,
            absent=stale,
        )
        self._open(
            "admin:content_homecollectionsblock_change",
            self.collections.pk,
            COL_BLOCK_LINK,
            absent=stale,
        )
        self._open(
            "admin:content_homepopularblock_change",
            self.popular.pk,
            "Заголовок блоку популярних товарів на головній.",
        )
        self._open(
            "admin:content_homelocaleblock_change",
            self.locale.pk,
            "Текст кнопки «Підтвердити».",
            "По одному рядку: 1) Delivery place",
            absent=stale,
        )
        self._open(
            "admin:content_sitesettings_change",
            SiteSettings.load().pk,
            SOCIAL_URL,
            TELEGRAM_URL,
            ADDRESS,
            SHORT_NAV,
            LANG_OFF,
            absent=stale,
        )
        self._open(
            "admin:content_footerchrome_change",
            SiteSettings.load().pk,
            "Вертикальна риска",
            CREDIT,
        )
        self._open(
            "admin:content_aboutintro_change",
            1,
            INTRO_LEFT,
            SEO_TITLE,
        )
        self._open("admin:content_aboutgestia_change", 1, GESTIA_QUOTE)
        self._open("admin:content_aboutapproach_change", 1, APPROACH_TEXT)
        self._open("admin:content_aboutclosing_change", 1, ABOUT_CTA)
        self._open(
            "admin:content_faqheader_change",
            FaqPage.load().pk,
            FAQ_IMAGE,
            FAQ_CRUMB,
            "Shift і Enter",
            absent=("Лише wide", "для переносу рядка"),
        )
        self._open("admin:content_faqitem_change", self.question.pk, FAQ_ACTIVE)
        self._open("admin:content_faqseo_change", FaqPage.load().pk, SEO_TITLE)
        from src.content.models_contacts import ContactsPage

        self._open("admin:content_contactspage_change", ContactsPage.load().pk, FORM_TITLE, SEO_TITLE)
        self._open(
            "admin:content_thankyouorder_change",
            ThankYouPage.load().pk,
            ORDER_TEXT,
            ORDER_TEXT_NONUM,
            THANKS_LINK,
            absent=("підставляється безпечно", "substituted safely"),
        )
        self._open(
            "admin:content_offerpage_change",
            self.offer.pk,
            LEGAL_BODY,
            LEGAL_DATE,
            SEO_TITLE,
            EMPTY_LOCALE_HINT,
            absent=("Якщо порожньо — на сайті лишається український текст.",),
        )
        self._open("admin:content_menugroup_change", self.menu.pk, MENU_COLLECTION)
        self._open(
            "admin:catalog_category_change",
            self.category.pk,
            CATEGORY_MEDIA,
            MENU_FEATURED,
            SLUG_AUTO,
            absent=("створиться з назви",),
        )
        self._open(
            "admin:catalog_product_change",
            self.product.pk,
            PRICE,
            STOCK_QTY,
            IS_SALE,
            IS_POPULAR,
            CARD_IMAGE,
            SLUG_AUTO,
            "1272×1540",
            absent=("створиться з назви",),
        )
        self._open("admin:catalog_productattributegroup_change", self.group.pk, GROUP_SLUG)
        self._open(
            "admin:catalog_productattribute_change",
            self.attr.pk,
            IS_FILTERABLE,
            SHOW_ON_PDP,
            SLUG_AUTO,
        )
        style = PageStyle.objects.get(page=PageStyle.Key.GLOBAL)
        self._open(
            "admin:content_globalpagestyle_change",
            style.pk,
            TEXT_COLOR,
            FONT_FAMILY,
            "Тло сторінок сайту.",
        )
