from django.db import migrations

LOCALE_DEFAULTS = {
    "title_uk": "Країна та мова",
    "title_en": "Country and language",
    "text_uk": "Україна/Гривня",
    "text_en": "Ukraine/Hryvnia",
    "cta_uk": "Підтвердити",
    "cta_en": "Confirm",
    "link_uk": "Змінити",
    "link_en": "Change",
    "note_uk": (
        "Будь ласка, оберіть місце доставки, щоб побачити правильні ціни та способи доставки"
    ),
    "note_en": (
        "Please choose a delivery location to see the correct prices and delivery options"
    ),
    "lines_uk": (
        "Місце доставки\n"
        "Україна\n"
        "Міжнародна доставка\n"
        "Мова сайту\n"
        "Оберіть мову / Choose language\n"
        "Українська\n"
        "English"
    ),
    "lines_en": (
        "Delivery place\n"
        "Ukraine\n"
        "International delivery\n"
        "Site language\n"
        "Choose language\n"
        "Українська\n"
        "English"
    ),
}

def _blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def forwards(apps, schema_editor):
    del schema_editor
    HomeBlock = apps.get_model("content", "HomeBlock")

    block, _created = HomeBlock.objects.get_or_create(
        key="locale",
        defaults={"sort": 8},
    )
    updates = {}
    for field, value in LOCALE_DEFAULTS.items():
        if _blank(getattr(block, field, "")):
            updates[field] = value
    if updates:
        for field, value in updates.items():
            setattr(block, field, value)
        block.save(update_fields=list(updates.keys()))


def backwards(apps, schema_editor):
    del apps, schema_editor


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0029_media_kind_blank"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
