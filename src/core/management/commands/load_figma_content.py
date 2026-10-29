import shutil
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from src.catalog.models import (
    CatalogCell,
    Category,
    Product,
    ProductAttribute,
    ProductAttributeGroup,
    ProductImage,
    ProductSet,
)
from src.content.models import (
    AboutPage,
    Advantage,
    FooterLink,
    HomeBlock,
    Review,
    SiteSettings,
)
from src.core.figma_pdp import save_pdp_blocks, seed_pdp

DESKTOP = Path(settings.BASE_DIR) / "docs" / "figma" / "desktop"
MOBILE = Path(settings.BASE_DIR) / "docs" / "figma" / "mobile"
CATALOG = Path(settings.BASE_DIR) / "docs" / "figma" / "catalog"
ZERO = Decimal("0.00")
CTA = "Перейти до каталогу"


def nb(text):
    return text.replace(" ", "\u00a0")


REVIEW = (
    "Дуже красивий декор, який повністю відповідає фотографіям. "
    "Усе виглядає витончено й гармонійно. Саме такі деталі створюють особливу атмосферу вдома"
)


def _save(instance, field, path, name=None):
    current = getattr(instance, field)
    if getattr(current, "name", ""):
        current.delete(save=False)
    with path.open("rb") as handle:
        current.save(name or path.name, File(handle), save=True)


class Command(BaseCommand):
    help = "Завантажує тексти, ціни й зображення головної з docs/figma."

    def handle(self, *args, **options):
        self._wipe()
        categories = self._categories()
        self._attributes()
        products = self._products(categories)
        self._cells(products)
        self._filter_cells(products)
        self._mobile_cells(products)
        seed_pdp(products)
        self._blocks()
        save_pdp_blocks()
        self._advantages()
        self._reviews()
        self._footer()
        self._settings()
        self._clear_demo_pages()
        self._fill_english()
        seed = Path(settings.MEDIA_ROOT) / "seed"
        if seed.exists():
            shutil.rmtree(seed)
        self.stdout.write(self.style.SUCCESS("load_figma_content завершено"))

    def _fill_english(self):
        from django.apps import apps as django_apps

        from src.catalog.migrations.0013_fill_catalogcell_label_en import fill_catalogcell_label_en
        from src.content.migrations.0007_english_content_copy import fill_english_content

        fill_catalogcell_label_en(django_apps, None)
        fill_english_content(django_apps, None)

    def _wipe(self):
        for cell in CatalogCell.objects.all():
            if cell.image:
                cell.image.delete(save=False)
        CatalogCell.objects.all().delete()
        for image in ProductImage.objects.all():
            image.image.delete(save=False)
        for product in Product.objects.all():
            if product.card_image:
                product.card_image.delete(save=False)
        Product.objects.all().delete()
        for category in Category.objects.all():
            if category.image:
                category.image.delete(save=False)
        Category.objects.all().delete()
        ProductSet.objects.all().delete()
        ProductAttribute.objects.all().delete()
        ProductAttributeGroup.objects.all().delete()
        Advantage.objects.all().delete()
        Review.objects.all().delete()
        FooterLink.objects.all().delete()
        for block in HomeBlock.objects.all():
            if block.image:
                block.image.delete(save=False)
            if block.image_mobile:
                block.image_mobile.delete(save=False)
        HomeBlock.objects.all().delete()

    def _categories(self):
        specs = (
            ("rizdvyani-boksy", "Різдвяні бокси", "db3d5.png", 1, 1, True),
            ("interierni-kompozytsii", "Інтер'єрні композиції", "dd136.png", 2, 2, False),
            ("serviruvannia", "Сервірування", "fed6d.png", 3, 3, False),
            ("novorichnyi-dekor", "Новорічний декор", "", 4, None, False),
            ("vazy-ta-kashpo", "Вази та кашпо", "6fbc8.png", 5, 4, False),
            ("tekstyl", "Текстиль ", "", 6, None, False),
            ("svichky", "Свічки", "328df.png", 7, 6, False),
            ("podarunkovi-sety", "Подарункові сети", "14fec.png", 8, 5, False),
        )
        made = {}
        for slug, name, image, sort, home_sort, featured in specs:
            category = Category.objects.create(
                slug=slug,
                name_uk=name,
                sort=sort,
                home_sort=home_sort,
                menu_featured=featured,
                is_active=True,
            )
            if image:
                _save(category, "image", DESKTOP / image)
            made[slug] = category
        # Labels match the Figma filter panel; products live in these category slugs.
        filters = {
            "rizdvyani-boksy": (1, "Новорічний декор"),
            "interierni-kompozytsii": (2, "Інтер'єрні композиції"),
            "vazy-ta-kashpo": (3, ""),
            "tekstyl": (4, "Текстиль"),
            "svichky": (5, ""),
            "podarunkovi-sety": (6, ""),
        }
        for slug, (filter_sort, filter_name) in filters.items():
            category = made[slug]
            category.filter_sort = filter_sort
            category.filter_name_uk = filter_name
            category.save(update_fields=["filter_sort", "filter_name_uk"])
        return made

    def _attributes(self):
        style = ProductAttributeGroup.objects.create(slug="style", name_uk="Стиль")
        color = ProductAttributeGroup.objects.create(slug="color", name_uk="Колір")
        styles = (
            (1, "scandi", "Скандинавський"),
            (2, "classic", "Класичний"),
            (3, "modern", "Модерн"),
            (4, "boho", "Бохо"),
            (5, "rustic", "Рустик"),
        )
        colors = (
            (1, "white", "Білий"),
            (2, "beige", "Бежевий"),
            (3, "green", "Зелений"),
            (4, "red", "Червоний"),
            (5, "gold", "Золотий"),
            (6, "black", "Чорний"),
        )
        for sort, slug, name in styles:
            ProductAttribute.objects.create(group=style, slug=slug, name_uk=name, sort=sort)
        for sort, slug, name in colors:
            ProductAttribute.objects.create(group=color, slug=slug, name_uk=name, sort=sort)

    def _products(self, categories):
        # (key, sku, slug, name, image, price, weight, sort, category, popular, crop, name_width, styles, colors)
        specs = (
            ("GH-01", "GH-01", "velykodnii-ukrainskyi", "Бокс Великодній «Український»", DESKTOP / "479da.png", "8990.00", 400, 1, "podarunkovi-sety", True, "ukr", 127, ("classic",), ("red", "beige")),
            ("GH-02", "GH-02", "boks-rizdvyanyi-shyshky", "Бокс «Різдвяний Шишки»", DESKTOP / "db3d5.png", "4980.00", 400, 2, "rizdvyani-boksy", True, "shysh", 127, ("rustic",), ("green", "gold")),
            ("GH-03", "TL-0012", "velykodnii-hnizdo", "Бокс Великодній «Гніздо»", DESKTOP / "14fec.png", "2450.00", 400, 3, "podarunkovi-sety", True, "hnizdo", 126, ("scandi",), ("white",)),
            ("GH-04", "GH-04", "vesilnyi", "Бокс «Весільний»", DESKTOP / "72b4d.png", "14980.00", 500, 4, "podarunkovi-sety", True, "cover", 119, ("classic",), ("white", "gold")),
            ("GH-05", "GH-05", "vesnianyi", "Бокс «Весняний»", CATALOG / "2dcde.png", "2450.00", 400, 5, "interierni-kompozytsii", False, "cover", 143, ("boho",), ("beige", "green")),
            ("GH-06", "GH-06", "gazetnyi", "Бокс «Газетний»", CATALOG / "729be.png", "5130.00", 400, 6, "tekstyl", False, "cover", 127, ("modern",), ("black", "beige")),
        )
        attr_map = {
            (attr.group.slug, attr.slug): attr
            for attr in ProductAttribute.objects.select_related("group")
        }
        made = {}
        for key, sku, slug, name, image, price, weight, sort, category_slug, popular, crop, name_width, styles, colors in specs:
            product = Product.objects.create(
                category=categories[category_slug],
                sku=sku,
                slug=slug,
                name_uk=name,
                menu_name_uk="Бокс Різдвяний Шишки" if slug == "boks-rizdvyanyi-shyshky" else "",
                menu_name_en="Christmas box “Pine Cones”" if slug == "boks-rizdvyanyi-shyshky" else "",
                price_uah=Decimal(price),
                price_eur=ZERO,
                price_weight=weight,
                card_crop=crop,
                name_width=name_width,
                is_popular=popular,
                is_active=True,
                sort=sort,
                stock_qty=settings.STOCK_PLACEHOLDER_QTY,
            )
            _save(product, "card_image", image, f"card-{slug}.png")
            if key != "GH-03":
                shot = ProductImage(product=product, sort=1)
                _save(shot, "image", image, f"{slug}.png")
            attrs = []
            for style in styles:
                attrs.append(attr_map[("style", style)])
            for color in colors:
                attrs.append(attr_map[("color", color)])
            if attrs:
                product.filter_attrs.set(attrs)
            made[key] = product
        return made

    def _cells(self, products):
        specs = (
            (1, "split_start", "grid", 1, "GH-01", "8990.00", "ukr", 127, "479da.png"),
            (1, "split_start", "grid", 2, "GH-04", "4980.00", "cover", 119, "72b4d.png"),
            (1, "split_start", "grid", 3, "GH-02", "4980.00", "shysh", 127, "db3d5.png"),
            (1, "split_start", "grid", 4, "GH-03", "2450.00", "hnizdo", 126, "14fec.png"),
            (1, "split_start", "feature", 1, "GH-05", "2450.00", "cover", 143, "2dcde.png"),
            (2, "row", "grid", 1, "GH-04", "4980.00", "cover", 119, "72b4d.png"),
            (2, "row", "grid", 2, "GH-01", "8990.00", "ukr", 127, "479da.png"),
            (2, "row", "grid", 3, "GH-05", "2450.00", "cover", 143, "2dcde.png"),
            (2, "row", "grid", 4, "GH-06", "5130.00", "cover", 127, "729be.png"),
            (3, "split_end", "feature", 1, "GH-05", "2450.00", "wide", 143, "72b4d.png"),
            (3, "split_end", "grid", 1, "GH-01", "8990.00", "ukr", 127, "479da.png"),
            (3, "split_end", "grid", 2, "GH-06", "5130.00", "cover", 127, "729be.png"),
            (3, "split_end", "grid", 3, "GH-02", "4980.00", "shysh", 127, "db3d5.png"),
            (3, "split_end", "grid", 4, "GH-03", "2450.00", "hnizdo", 126, "14fec.png"),
        )
        for band, layout, role, sort, sku, price, crop, name_width, image in specs:
            cell = CatalogCell.objects.create(
                product=products[sku],
                band=band,
                layout=layout,
                role=role,
                sort=sort,
                price_uah=Decimal(price),
                crop=crop,
                name_width=name_width,
            )
            _save(cell, "image", CATALOG / image, f"cell-{band}-{role}-{sort}-{image}")

    def _filter_cells(self, products):
        rows = (
            (1, "GH-01", "8990.00", "ukr", 127, "479da.png"),
            (2, "GH-06", "5130.00", "cover", 127, "729be.png"),
            (3, "GH-04", "4980.00", "cover", 119, "72b4d.png"),
            (4, "GH-02", "4980.00", "shysh", 127, "db3d5.png"),
            (5, "GH-04", "4980.00", "cover", 119, "72b4d.png"),
            (6, "GH-03", "2450.00", "hnizdo", 126, "14fec.png"),
            (7, "GH-05", "2450.00", "cover", 143, "2dcde.png"),
            (8, "GH-01", "8990.00", "ukr", 127, "479da.png"),
            (9, "GH-01", "8990.00", "ukr", 127, "479da.png"),
            (10, "GH-04", "4980.00", "cover", 119, "72b4d.png"),
            (11, "GH-01", "8990.00", "ukr", 127, "479da.png"),
            (12, "GH-03", "2450.00", "hnizdo", 126, "14fec.png"),
        )
        for sort, sku, price, crop, name_width, image in rows:
            cell = CatalogCell.objects.create(
                product=products[sku],
                band=0,
                layout=CatalogCell.Layout.ROW,
                role=CatalogCell.Role.GRID,
                surface=CatalogCell.Surface.FILTERS,
                sort=sort,
                price_uah=Decimal(price),
                crop=crop,
                name_width=name_width,
            )
            _save(cell, "image", CATALOG / image, f"filter-{sort}-{image}")

    def _mobile_cells(self, products):
        stamped = "Бокс Великодній «Український»"
        rows = (
            (1, "GH-01", "feature", "", "8990.00", "ukr", "479da.png"),
            (2, "GH-02", "tile", "", "8990.00", "shysh", "db3d5.png"),
            (3, "GH-06", "tile", stamped, "8990.00", "cover", "729be.png"),
            (4, "GH-06", "tile", stamped, "8990.00", "cover", "729be.png"),
            (5, "GH-05", "tile_tall", stamped, "8990.00", "cover", "2dcde.png"),
            (6, "GH-03", "feature_tall", stamped, "8990.00", "hnizdo", "14fec.png"),
            (7, "GH-06", "tile", stamped, "8990.00", "cover", "729be.png"),
            (8, "GH-05", "tile_tall", stamped, "8990.00", "cover", "2dcde.png"),
        )
        for sort, sku, slot, label, price, crop, image in rows:
            cell = CatalogCell.objects.create(
                product=products[sku],
                band=0,
                layout=CatalogCell.Layout.ROW,
                role=CatalogCell.Role.GRID,
                surface=CatalogCell.Surface.MOBILE,
                slot=slot,
                label_uk=label,
                label_en="Easter box “Ukrainian”" if label == stamped else "",
                sort=sort,
                price_uah=Decimal(price),
                crop=crop,
                name_width=95,
            )
            _save(cell, "image", CATALOG / image, f"mobile-{sort}-{image}")

    def _blocks(self):
        hero_title = "Декор для дому, текстиль \nі флористика"
        hero_text = (
            "Декор для дому, домашній текстиль, флористика та одяг для дому від Gestia Home. "
            "Створюйте затишний простір із речами, у яких поєднуються естетика та функціональність"
        )
        advantage_text = (
            "Декор для дому, флористика, текстиль та одяг для дому українського виробництва"
        )
        advantage_mobile = (
            "Декор для дому, флористика, текстиль \nта одяг для дому українського виробництва"
        )
        callback_text = "Залиште свій номер телефону, і ми зв’яжемося з вами найближчим часом"
        callback_mobile = (
            "Залиште свій номер телефону, \nі ми зв’яжемося з вами найближчим часом"
        )
        rows = (
            ("hero", 1, hero_title, hero_text, "", CTA, "", "", "1b95b.png", "0c378.png"),
            ("video", 2, "", "", "", "", "", "", "1b95b.png", "0c378.png"),
            ("popular", 3, "Популярні товари", "", "", CTA, "", "", "", ""),
            (
                "advantages",
                4,
                "Чому обирають GESTIA HOME",
                advantage_text,
                advantage_mobile,
                CTA,
                "",
                "",
                "656fe.png",
                "",
            ),
            ("video_2", 5, "", "", "", "", "", "", "1b95b.png", "0c378.png"),
            ("reviews", 6, "Відгуки", "", "", "", "", "", "", ""),
            (
                "callback",
                7,
                "Замовити зворотний дзвінок",
                callback_text,
                callback_mobile,
                CTA,
                "Політикою конфіденційності",
                "Погоджуюсь на обробку персональних даних згідно з ",
                "",
                "",
            ),
            ("locale", 8, "Країна та мова", "Україна/Гривня ", "", "Підтвердити", "Змінити", "", "", ""),
            ("mega", 9, "", "", "", "Дивитись все", "", "", "", ""),
            ("catalog", 10, "", "", "", "Завантажити все", "", "", "", ""),
        )
        for key, sort, title, text, mobile_text, cta, link, note, image, mobile in rows:
            block = HomeBlock.objects.create(
                key=key,
                sort=sort,
                title_uk=title,
                text_uk=text,
                text_mobile_uk=mobile_text,
                cta_uk=cta,
                link_uk=link,
                note_uk=note,
                lines_uk="Ім’я\nНомер телефону\nПовідомлення" if key == "callback" else "",
            )
            if image:
                _save(block, "image", DESKTOP / image, f"{key}-{image}")
            if mobile:
                _save(block, "image_mobile", MOBILE / mobile, f"{key}-{mobile}")

    def _advantages(self):
        rows = (
            ("Унікальний дизайн", "Декор, що поєднує сучасну естетику та природну красу"),
            (
                "Українське виробництво",
                "Вироби, створені в Україні \nз увагою до деталей та естетики",
            ),
            ("Натуральні матеріали", "Натуральні матеріали для природної естетики та затишку вдома"),
            (
                "Багатофункціональність",
                "Речі, які легко адаптувати до різних потреб і домашніх сценаріїв",
            ),
        )
        for sort, (title, text) in enumerate(rows, start=1):
            Advantage.objects.create(sort=sort, title_uk=title, text_uk=text)

    def _reviews(self):
        for sort in range(1, 5):
            Review.objects.create(
                placement=Review.Placement.HOME,
                sort=sort,
                author_uk=nb("Марія К."),
                text_uk=REVIEW,
                rating_kind=Review.Rating.BLACK_FIVE if sort == 4 else Review.Rating.GOLD_FOUR,
            )
        for sort in range(1, 3):
            Review.objects.create(
                placement=Review.Placement.ABOUT,
                sort=sort,
                author_uk=nb("Олена П."),
                text_uk=REVIEW,
                rating_kind=Review.Rating.GOLD_FOUR,
            )

    def _footer(self):
        rows = (
            ("category", "Усі товари", "catalog", "", False, 1),
            ("category", "Різдвяні бокси", "category", "rizdvyani-boksy", True, 2),
            ("category", "Інтер'єрні композиції", "category", "interierni-kompozytsii", False, 3),
            ("category", "Сервірування", "category", "serviruvannia", False, 4),
            ("info", "Про нас", "about", "", False, 1),
            ("info", "Контакти", "anchor", "callback", False, 2),
            ("info", "Доставка та оплата", "shipping", "", False, 3),
            ("legal", "Публічний договір (оферта)", "offer", "", False, 1),
            ("legal", "Політика конфіденційності", "privacy", "", False, 2),
            ("legal", "Політика cookies", "cookies", "", False, 3),
        )
        for column, label, url_name, url_arg, underlined, sort in rows:
            FooterLink.objects.create(
                column=column,
                label_uk=label,
                url_name=url_name,
                url_arg=url_arg,
                underlined=underlined,
                sort=sort,
            )

    def _settings(self):
        site = SiteSettings.load()
        site.phone = "+380 000 00 00"
        site.instagram_url = "https://www.instagram.com/"
        site.pinterest_url = "https://www.pinterest.com/"
        site.footer_note_uk = "© Gestia Home 2026. У|сі права захищені."
        site.developer_note_uk = ""
        site.save()

    def _clear_demo_pages(self):
        about = AboutPage.objects.filter(pk=1, title_uk="Про майстерню").first()
        if about is None:
            return
        if about.image:
            about.image.delete(save=False)
        about.title_uk = "Про нас"
        about.title_en = ""
        about.body_uk = ""
        about.body_en = ""
        about.save()
