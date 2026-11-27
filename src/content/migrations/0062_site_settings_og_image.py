import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0061_site_settings_currency"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="og_image",
            field=models.ImageField(
                blank=True,
                help_text="Якщо порожня — лишається поточний static og-default.",
                upload_to="site/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        ["jpg", "jpeg", "png", "webp"]
                    )
                ],
                verbose_name="OG-картинка за замовчуванням",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="og_image_alt_uk",
            field=models.CharField(
                default="Святковий стіл Gestia Home",
                max_length=160,
                verbose_name="Підпис OG-картинки",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="og_image_alt_en",
            field=models.CharField(
                default="A festive table by Gestia Home",
                max_length=160,
                verbose_name="Підпис OG-картинки (EN)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="og_image_alt_fr",
            field=models.CharField(
                default="Une table de fête Gestia Home",
                max_length=160,
                verbose_name="Підпис OG-картинки (FR)",
            ),
        ),
    ]
