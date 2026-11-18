from django.db import migrations


def drop_easter_set(apps, schema_editor):
    ProductSet = apps.get_model("catalog", "ProductSet")
    ProductSet.objects.filter(slug="velykodni").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0022_hide_collection_bucket_parent"),
    ]

    operations = [
        migrations.RunPython(drop_easter_set, migrations.RunPython.noop),
    ]
