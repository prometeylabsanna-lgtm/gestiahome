from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0063_site_settings_short_name_theme"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="instagram_label",
            field=models.CharField(
                default="Instagram",
                max_length=40,
                verbose_name="Підпис Instagram",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="pinterest_label",
            field=models.CharField(
                default="Pinterest",
                max_length=40,
                verbose_name="Підпис Pinterest",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="telegram_label",
            field=models.CharField(
                default="Telegram",
                max_length=40,
                verbose_name="Підпис Telegram",
            ),
        ),
    ]
