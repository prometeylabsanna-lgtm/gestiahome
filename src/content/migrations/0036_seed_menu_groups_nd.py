from django.db import migrations


BOX_ITEMS = (
    ("«Квітка-душа»", "«Soul Flower»", "Квітка-душа", 1),
    ("«Коріння»", "«Roots»", "Коріння", 2),
    ("«Родинний кришталь»", "«Family Crystal»", "Родинний\nкришталь", 3),
    ("«Тартан»", "«Tartan»", "Тартан", 4),
    ("«Дитинство»", "«Childhood»", "Дитинство", 5),
    ("«Спадщина»", "«Heritage»", "Спадщина", 6),
)

ACCESSORY_ITEMS = (
    ("Підсвічники", "Candle holders", 1),
    ("Серветки", "Napkins", 2),
    ("Кільця для серветок", "Napkin rings", 3),
)


def forwards(apps, schema_editor):
    del schema_editor
    MenuGroup = apps.get_model("content", "MenuGroup")
    MenuGroupItem = apps.get_model("content", "MenuGroupItem")
    HomeCollection = apps.get_model("content", "HomeCollection")

    boxes, _created = MenuGroup.objects.get_or_create(
        title_uk="Святкові бокси",
        defaults={
            "title_en": "Festive boxes",
            "sort": 1,
            "is_active": True,
            "open_by_default": True,
        },
    )
    if not boxes.title_en:
        boxes.title_en = "Festive boxes"
        boxes.save(update_fields=["title_en"])

    accessories, _created = MenuGroup.objects.get_or_create(
        title_uk="Столові аксесуари",
        defaults={
            "title_en": "Table accessories",
            "sort": 2,
            "is_active": True,
            "open_by_default": False,
        },
    )
    if not accessories.title_en:
        accessories.title_en = "Table accessories"
        accessories.save(update_fields=["title_en"])

    for label_uk, label_en, title_uk, sort in BOX_ITEMS:
        collection = HomeCollection.objects.filter(title_uk=title_uk).order_by("id").first()
        MenuGroupItem.objects.get_or_create(
            group=boxes,
            label_uk=label_uk,
            defaults={
                "label_en": label_en,
                "collection": collection,
                "category": None,
                "sort": sort,
                "is_active": True,
            },
        )

    for label_uk, label_en, sort in ACCESSORY_ITEMS:
        MenuGroupItem.objects.get_or_create(
            group=accessories,
            label_uk=label_uk,
            defaults={
                "label_en": label_en,
                "collection": None,
                "category": None,
                "sort": sort,
                "is_active": True,
            },
        )


def backwards(apps, schema_editor):
    del apps, schema_editor


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0035_menu_groups_nd"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
