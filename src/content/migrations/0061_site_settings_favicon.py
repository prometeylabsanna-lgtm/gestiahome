from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0060_merge_20261127_1617"),
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
