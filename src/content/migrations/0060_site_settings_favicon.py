from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0059_site_settings_site_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="favicon",
            field=models.FileField(
                blank=True,
                help_text="Іконка вкладки браузера. PNG або ICO.",
                upload_to="site/",
                verbose_name="Favicon",
            ),
        ),
    ]
