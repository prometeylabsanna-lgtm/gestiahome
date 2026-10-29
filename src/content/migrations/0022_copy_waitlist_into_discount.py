from django.db import migrations

_WAITLIST_FIELDS = (
    "waitlist_title_uk",
    "waitlist_title_en",
    "waitlist_p1_uk",
    "waitlist_p1_en",
    "waitlist_p2_uk",
    "waitlist_p2_en",
    "waitlist_p3_uk",
    "waitlist_p3_en",
    "waitlist_email_uk",
    "waitlist_email_en",
    "waitlist_consent_uk",
    "waitlist_consent_en",
    "waitlist_privacy_uk",
    "waitlist_privacy_en",
    "waitlist_button_uk",
    "waitlist_button_en",
    "waitlist_thanks_title_uk",
    "waitlist_thanks_title_en",
    "waitlist_thanks_text_uk",
    "waitlist_thanks_text_en",
)


def forwards(apps, schema_editor):
    ContactForms = apps.get_model("content", "ContactForms")
    DiscountModal = apps.get_model("content", "DiscountModal")
    forms = ContactForms.objects.order_by("pk").first()
    modal = DiscountModal.objects.order_by("pk").first()
    if modal is None:
        modal = DiscountModal.objects.create(pk=1, enabled=True, delay_seconds=15, shows_per_session=1)
    if forms is not None:
        for name in _WAITLIST_FIELDS:
            value = getattr(forms, name, "") or ""
            if value and not (getattr(modal, name, "") or ""):
                setattr(modal, name, value)
    if not (modal.waitlist_title_uk or "").strip() and (modal.title_uk or "").strip():
        modal.waitlist_title_uk = modal.title_uk[:56]
    if not (modal.waitlist_title_en or "").strip() and (modal.title_en or "").strip():
        modal.waitlist_title_en = modal.title_en[:56]
    if not (modal.waitlist_button_uk or "").strip() and (modal.button_uk or "").strip():
        modal.waitlist_button_uk = modal.button_uk[:24]
    if not (modal.waitlist_button_en or "").strip() and (modal.button_en or "").strip():
        modal.waitlist_button_en = modal.button_en[:24]
    # Раніше waitlist завжди показувався — лишаємо увімкненим після переносу.
    modal.enabled = True
    modal.save()


def backwards(apps, schema_editor):
    DiscountModal = apps.get_model("content", "DiscountModal")
    DiscountModal.objects.filter(pk=1).update(enabled=False)


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0021_discount_waitlist_fields"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
