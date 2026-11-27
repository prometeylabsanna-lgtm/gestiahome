from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0061_site_settings_favicon"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="currency_uah",
            field=models.CharField(
                default="UAH",
                help_text="Після ціни в гривнях, зараз «UAH».",
                max_length=8,
                verbose_name="Суфікс гривні",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="currency_uah_sign",
            field=models.CharField(
                default="₴",
                help_text="Знак у format_money для гривні, зараз «₴».",
                max_length=8,
                verbose_name="Знак гривні",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="currency_eur",
            field=models.CharField(
                default="€",
                help_text="Знак євро, зараз «€».",
                max_length=8,
                verbose_name="Знак євро",
            ),
        ),
    ]
