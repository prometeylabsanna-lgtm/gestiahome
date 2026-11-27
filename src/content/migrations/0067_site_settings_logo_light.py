from django.core.validators import FileExtensionValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0066_hardcode_copy"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="logo_light",
            field=models.ImageField(
                blank=True,
                help_text="Hero на головній. Якщо порожнє — світлий SVG nd/logo-gestia-light.svg.",
                upload_to="site/",
                validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
                verbose_name="Логотип на темному тлі",
            ),
        ),
    ]
