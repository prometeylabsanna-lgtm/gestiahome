from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0045_seed_collection_products_nd"),
    ]

    operations = [
        migrations.AddField(
            model_name="homeblock",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Оновлено"),
        ),
        migrations.AddField(
            model_name="homecollection",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Оновлено"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Оновлено"),
        ),
        migrations.AddField(
            model_name="faqpage",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Оновлено"),
        ),
        migrations.AddField(
            model_name="legalpage",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Оновлено"),
        ),
    ]
