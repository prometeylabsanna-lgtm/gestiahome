from django.db import migrations

from src.content.french_copy import tighten_stored_fr_guillemets


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0054_french_copy_addons"),
        ("catalog", "0024_french_locale"),
    ]

    operations = [
        migrations.RunPython(tighten_stored_fr_guillemets, migrations.RunPython.noop),
    ]
