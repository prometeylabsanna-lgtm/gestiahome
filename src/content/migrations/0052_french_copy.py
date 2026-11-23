from django.db import migrations

from src.content.french_copy import fill_french_copy, unfill_french_copy


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0051_french_locale_ui"),
        ("catalog", "0024_french_locale"),
    ]

    operations = [
        migrations.RunPython(fill_french_copy, unfill_french_copy),
    ]
