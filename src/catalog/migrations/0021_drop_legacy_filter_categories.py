from django.db import migrations


def drop_legacy_filter_categories(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")
    moves = (
        ("novorichnyi-dekor", "rizdvyani-boksy"),
        ("tekstyl", "interierni-kompozytsii"),
    )
    for old_slug, new_slug in moves:
        old = Category.objects.filter(slug=old_slug).first()
        if old is None:
            continue
        new = Category.objects.filter(slug=new_slug).first()
        if new is None and Product.objects.filter(category_id=old.pk).exists():
            continue
        if new is not None:
            Product.objects.filter(category_id=old.pk).update(category_id=new.pk)
        old.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0020_media_kind_blank"),
    ]

    operations = [
        migrations.RunPython(drop_legacy_filter_categories, migrations.RunPython.noop),
    ]
