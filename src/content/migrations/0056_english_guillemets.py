from django.db import migrations, models

from src.core.utils import curly_to_guillemets


def swap_stored_en_quotes(apps, schema_editor):
    del schema_editor
    for model in apps.get_models():
        names = [
            field.name
            for field in model._meta.local_concrete_fields
            if field.name.endswith("_en") and isinstance(field, (models.CharField, models.TextField))
        ]
        if not names:
            continue
        for obj in model.objects.all().iterator():
            changed = []
            for name in names:
                value = getattr(obj, name)
                new = curly_to_guillemets(value)
                if new != value:
                    setattr(obj, name, new)
                    changed.append(name)
            if changed:
                obj.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0055_french_guillemets"),
        ("catalog", "0024_french_locale"),
    ]

    operations = [
        migrations.RunPython(swap_stored_en_quotes, migrations.RunPython.noop),
    ]
