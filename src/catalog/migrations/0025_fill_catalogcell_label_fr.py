from django.db import migrations

LABEL_UK = "Бокс Великодній «Український»"
LABEL_FR = "Coffret de Pâques «Ukrainien»"


def fill_catalogcell_label_fr(apps, schema_editor):
    del schema_editor
    CatalogCell = apps.get_model("catalog", "CatalogCell")
    CatalogCell.objects.filter(label_uk=LABEL_UK, label_fr="").update(label_fr=LABEL_FR)


def clear_catalogcell_label_fr(apps, schema_editor):
    del schema_editor
    CatalogCell = apps.get_model("catalog", "CatalogCell")
    CatalogCell.objects.filter(label_uk=LABEL_UK, label_fr=LABEL_FR).update(label_fr="")


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0024_french_locale"),
    ]

    operations = [
        migrations.RunPython(fill_catalogcell_label_fr, clear_catalogcell_label_fr),
    ]
