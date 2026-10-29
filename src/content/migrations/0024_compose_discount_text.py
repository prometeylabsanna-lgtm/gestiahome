from django.db import migrations
from django.utils.html import escape


def _join(*parts):
    chunks = [escape(part.strip()) for part in parts if (part or "").strip()]
    if not chunks:
        return ""
    return "".join(f"<p>{chunk}</p>" for chunk in chunks)


def forwards(apps, schema_editor):
    DiscountModal = apps.get_model("content", "DiscountModal")
    for modal in DiscountModal.objects.all():
        if not (modal.text_uk or "").strip():
            modal.text_uk = _join(
                modal.waitlist_title_uk,
                modal.waitlist_p1_uk,
                modal.waitlist_p2_uk,
                modal.waitlist_p3_uk,
            )
        if not (modal.text_en or "").strip():
            modal.text_en = _join(
                modal.waitlist_title_en,
                modal.waitlist_p1_en,
                modal.waitlist_p2_en,
                modal.waitlist_p3_en,
            )
        modal.save(update_fields=["text_uk", "text_en"])


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0023_styles_chrome_font_discount_text"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
