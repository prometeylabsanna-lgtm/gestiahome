from django.db import migrations

ABOUT_TITLE_EN = "Hi, I\u2019m Gestia"


def forward(apps, schema_editor):
    AboutPage = apps.get_model("content", "AboutPage")
    page = AboutPage.objects.filter(pk=1).first()
    if page is None:
        return
    if (page.title_en or "").strip() != "About":
        return
    page.title_en = ABOUT_TITLE_EN
    page.save(update_fields=["title_en"])


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0043_seed_about_faq_en"),
    ]

    operations = [
        migrations.RunPython(forward, noop_reverse),
    ]
