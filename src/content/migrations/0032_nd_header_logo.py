from django.db import migrations

OLD_LOGOS = ("site/5493c.webp", "site/5493c.png")
NEW_LOGO = "site/gestia-logo-nd.png"
NEW_STATIC = "nd/logo.png"
REVERSE_LOGO = "site/5493c.webp"


def forwards(apps, schema_editor):
    del schema_editor
    from src.content.static_seed import place_static

    SiteSettings = apps.get_model("content", "SiteSettings")
    settings_row = SiteSettings.objects.filter(pk=1).first()
    if not settings_row or not settings_row.logo:
        return
    current = settings_row.logo.name
    if current not in OLD_LOGOS:
        return
    stored = place_static(NEW_STATIC, NEW_LOGO)
    if not stored:
        return
    settings_row.logo = stored
    settings_row.save(update_fields=["logo"])


def backwards(apps, schema_editor):
    del schema_editor
    SiteSettings = apps.get_model("content", "SiteSettings")
    settings_row = SiteSettings.objects.filter(pk=1).first()
    if not settings_row:
        return
    if settings_row.logo and settings_row.logo.name == NEW_LOGO:
        settings_row.logo = REVERSE_LOGO
        settings_row.save(update_fields=["logo"])


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0031_homelocaleblock"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
