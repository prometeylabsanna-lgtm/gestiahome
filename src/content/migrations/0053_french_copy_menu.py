from django.db import migrations

from src.content.french_copy import fill_french_copy, unfill_french_copy


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0052_french_copy"),
    ]

    operations = [
        migrations.RunPython(fill_french_copy, unfill_french_copy),
    ]
