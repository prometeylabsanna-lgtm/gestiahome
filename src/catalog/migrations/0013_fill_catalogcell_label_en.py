from django.db import migrations

LABEL_UK = "Бокс Великодній «Український»"
LABEL_EN = "Easter box «Ukrainian»"


def fill_catalogcell_label_en(apps, schema_editor):
    del schema_editor
    CatalogCell = apps.get_model("catalog", "CatalogCell")
    CatalogCell.objects.filter(label_uk=LABEL_UK, label_en="").update(label_en=LABEL_EN)


def clear_catalogcell_label_en(apps, schema_editor):
    del schema_editor
    CatalogCell = apps.get_model("catalog", "CatalogCell")
    CatalogCell.objects.filter(label_uk=LABEL_UK, label_en=LABEL_EN).update(label_en="")


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0012_catalogcell_label_en"),
    ]

    operations = [
        migrations.RunPython(fill_catalogcell_label_en, clear_catalogcell_label_en),
    ]
