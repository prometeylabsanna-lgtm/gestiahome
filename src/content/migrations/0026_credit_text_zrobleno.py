from django.db import migrations

OLD_UK = "Вітрину зібрано в"
OLD_EN = "Storefront assembled by"
NEW_UK = "Зроблено"
NEW_EN = "Made by"


def forwards(apps, schema_editor):
    del schema_editor
    SiteSettings = apps.get_model("content", "SiteSettings")
    SiteSettings.objects.filter(credit_uk=OLD_UK).update(credit_uk=NEW_UK)
    SiteSettings.objects.filter(credit_en=OLD_EN).update(credit_en=NEW_EN)


def backwards(apps, schema_editor):
    del schema_editor
    SiteSettings = apps.get_model("content", "SiteSettings")
    SiteSettings.objects.filter(credit_uk=NEW_UK).update(credit_uk=OLD_UK)
    SiteSettings.objects.filter(credit_en=NEW_EN).update(credit_en=OLD_EN)


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0025_site_settings_telegram_url"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
