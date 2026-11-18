from decimal import Decimal

from django.db import migrations

BOXES = (
    ("kvitka-dusha", "Бокс «Квітка-душа»", "Box “Soul Flower”", "COL-KVITKA", "4980.00", "kvitka-large.jpg"),
    ("korinnia", "Бокс «Коріння»", "Box “Roots”", "COL-KORINNIA", "4450.00", "korinnia-large.jpg"),
    ("rodynnyi-kryshtal", "Бокс «Родинний кришталь»", "Box “Family Crystal”", "COL-KRYSHTAL", "5130.00", "kryshtal-large.jpg"),
    ("tartan", "Бокс «Тартан»", "Box “Tartan”", "COL-TARTAN", "4980.00", "tartan-large.jpg"),
    ("dytynstvo", "Бокс «Дитинство»", "Box “Childhood”", "COL-DYTYNSTVO", "3990.00", "dytynstvo-large.jpg"),
    ("spadshchyna", "Бокс «Спадщина»", "Box “Heritage”", "COL-SPADSHCHYNA", "5490.00", "spadshchyna-large.jpg"),
)

ADDONS = (
    ("addon-llyani-servetky", "Лляні серветки", "Linen napkins", "ADD-NAPKIN", "890.00", "collections/korinnia-large.jpg"),
    ("addon-kiltsia", "Кільця для серветок", "Napkin rings", "ADD-RINGS", "650.00", "collections/korinnia-small.jpg"),
    ("addon-pidsvichnyky-extra", "Додаткові підсвічники + 2 свічки", "Extra holders + 2 candles", "ADD-HOLDERS-EXTRA", "1200.00", "collections/tartan-small.jpg"),
    ("addon-servetky-klitynka", "Серветки в клітинку", "Tartan napkins", "ADD-NAPKIN-PLAID", "890.00", "about/about-table-wide.jpg"),
    ("addon-pidsvichnyky", "Підсвічники зі свічками", "Candle holders", "ADD-HOLDERS", "1200.00", "collections/tartan-small.jpg"),
    ("addon-pidsvichnyky-2", "2 підсвічники + 2 свічки", "2 holders + 2 candles", "ADD-HOLDERS-2", "1200.00", "collections/tartan-small.jpg"),
)

LINKS = {
    "kvitka-dusha": ("addon-llyani-servetky", "addon-kiltsia", "addon-pidsvichnyky-extra"),
    "korinnia": ("addon-llyani-servetky", "addon-kiltsia"),
    "rodynnyi-kryshtal": ("addon-pidsvichnyky-extra", "addon-kiltsia"),
    "tartan": ("addon-servetky-klitynka", "addon-kiltsia"),
    "dytynstvo": ("addon-pidsvichnyky", "addon-servetky-klitynka", "addon-kiltsia"),
    "spadshchyna": ("addon-pidsvichnyky-2", "addon-llyani-servetky"),
}


def _image(static_rel, stored_name):
    from src.content.static_seed import place_static

    return place_static(f"nd/{static_rel}", stored_name)


def forwards(apps, schema_editor):
    del schema_editor
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")
    HomeCollection = apps.get_model("content", "HomeCollection")

    category, _created = Category.objects.get_or_create(
        slug="kolektsiini-dodatky",
        defaults={
            "name_uk": "Доповнення колекцій",
            "name_en": "Collection extras",
            "is_active": False,
            "sort": 99,
        },
    )

    boxes = {}
    for slug, name_uk, name_en, sku, price, image_name in BOXES:
        image = _image(f"collections/{image_name}", f"products/cards/{sku.lower()}.jpg")
        product, _created = Product.objects.get_or_create(
            sku=sku,
            defaults={
                "category": category,
                "slug": slug if not Product.objects.filter(slug=slug).exists() else f"boks-{slug}",
                "name_uk": name_uk,
                "name_en": name_en,
                "price_uah": Decimal(price),
                "price_eur": Decimal("0.00"),
                "stock_qty": 99,
                "stock_status": "in_stock",
                "is_active": True,
                "is_popular": False,
                "sort": 200,
                "card_image": image or "",
            },
        )
        boxes[slug] = product

    addons = {}
    for slug, name_uk, name_en, sku, price, static_rel in ADDONS:
        image = _image(static_rel, f"products/cards/{sku.lower()}.jpg")
        product, _created = Product.objects.get_or_create(
            sku=sku,
            defaults={
                "category": category,
                "slug": slug,
                "name_uk": name_uk,
                "name_en": name_en,
                "price_uah": Decimal(price),
                "price_eur": Decimal("0.00"),
                "stock_qty": 99,
                "stock_status": "in_stock",
                "is_active": True,
                "is_popular": False,
                "sort": 210,
                "card_image": image or "",
            },
        )
        addons[slug] = product

    for collection_slug, addon_slugs in LINKS.items():
        collection = HomeCollection.objects.filter(slug=collection_slug).first()
        if collection is None:
            continue
        box = boxes[collection_slug]
        if collection.product_id != box.pk:
            collection.product_id = box.pk
            collection.save(update_fields=["product"])
        collection.addons.set([addons[slug] for slug in addon_slugs])


def backwards(apps, schema_editor):
    del apps, schema_editor


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0044_about_title_en"),
        ("catalog", "0020_media_kind_blank"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
