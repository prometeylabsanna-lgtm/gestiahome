from django.db import migrations

from src.content.french_copy_pages import ABOUT_FR

_OLD_ABOUT_FR = ("Salut, je suis Gestia", "À propos")


def forward(apps, schema_editor):
    del schema_editor
    AboutPage = apps.get_model("content", "AboutPage")
    page = AboutPage.objects.filter(pk=1).first()
    if page is None:
        return
    if (page.title_fr or "").strip() in _OLD_ABOUT_FR:
        page.title_fr = ABOUT_FR["title_fr"]
        page.save(update_fields=["title_fr"])


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0057_about_title_and_address"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
