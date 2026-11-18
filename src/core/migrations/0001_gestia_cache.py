from django.core.management import call_command
from django.db import migrations


def create_gestia_cache(apps, schema_editor):
    call_command(
        "createcachetable",
        "gestia_cache",
        database=schema_editor.connection.alias,
        verbosity=0,
    )


def drop_gestia_cache(apps, schema_editor):
    schema_editor.execute("DROP TABLE IF EXISTS gestia_cache")


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunPython(create_gestia_cache, drop_gestia_cache),
    ]
