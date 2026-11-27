from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0063_site_settings_og_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="site_name_short_uk",
            field=models.CharField(
                default="Gestia",
                help_text="У title каталогу та короткому бренді, зараз «Gestia».",
                max_length=40,
                verbose_name="Коротка назва",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="site_name_short_en",
            field=models.CharField(
                default="Gestia",
                max_length=40,
                verbose_name="Коротка назва (EN)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="site_name_short_fr",
            field=models.CharField(
                default="Gestia",
                max_length=40,
                verbose_name="Коротка назва (FR)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="theme_color",
            field=models.CharField(
                default="#ffffff",
                help_text="Мета theme-color у браузері. За замовчуванням #ffffff.",
                max_length=7,
                verbose_name="Колір вкладки (theme-color)",
            ),
        ),
    ]
