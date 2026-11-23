from django.db import migrations

from src.content.french_copy import STUDIO_ADDRESS
from src.content.french_copy_pages import ABOUT_FR

_WRONG_ABOUT_FR = "À propos"


def forward(apps, schema_editor):
    del schema_editor
    AboutPage = apps.get_model("content", "AboutPage")
    page = AboutPage.objects.filter(pk=1).first()
    if page is not None and (page.title_fr or "").strip() == _WRONG_ABOUT_FR:
        page.title_fr = ABOUT_FR["title_fr"]
        page.save(update_fields=["title_fr"])

    SiteSettings = apps.get_model("content", "SiteSettings")
    site = SiteSettings.objects.filter(pk=1).first()
    if site is None or (site.address_uk or "").strip() != STUDIO_ADDRESS["uk"]:
        return
    changed = []
    if not (site.address_en or "").strip():
        site.address_en = STUDIO_ADDRESS["en"]
        changed.append("address_en")
    if not (site.address_fr or "").strip():
        site.address_fr = STUDIO_ADDRESS["fr"]
        changed.append("address_fr")
    if changed:
        site.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0056_english_guillemets"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
