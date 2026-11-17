from django.db import migrations

DEFAULTS = {
    "order_title_uk": "Раді стати частиною ваших традицій!",
    "order_title_en": "We’re happy to be part of your traditions!",
    "order_text_uk": (
        "<p>Замовлення № {number} оформлено. Після відправлення ви отримаєте "
        "номер накладної для відстеження.</p>"
    ),
    "order_text_en": (
        "<p>Your order No. {number} has been placed. Once it ships, we’ll send "
        "you a tracking number.</p>"
    ),
    "order_text_nonum_uk": (
        "<p>Замовлення оформлено. Після відправлення ви отримаєте номер "
        "накладної для відстеження.</p>"
    ),
    "order_text_nonum_en": (
        "<p>Your order has been placed. Once it ships, we’ll send you a "
        "tracking number.</p>"
    ),
    "link_uk": "На головну",
    "link_en": "Back to home",
    "contact_title_uk": "Дякуємо",
    "contact_title_en": "Thank you",
    "contact_text_uk": (
        "<p>Ми отримали ваше повідомлення і незабаром відповімо.</p>"
    ),
    "contact_text_en": (
        "<p>We’ve received your message and will get back to you soon.</p>"
    ),
}


def _fill(obj, updates):
    changed = []
    for key, value in updates.items():
        current = getattr(obj, key, None)
        if current in (None, ""):
            setattr(obj, key, value)
            changed.append(key)
    return changed


def seed_forward(apps, schema_editor):
    ThankYouPage = apps.get_model("content", "ThankYouPage")
    page, _ = ThankYouPage.objects.get_or_create(pk=1)
    changed = _fill(page, DEFAULTS)
    if changed:
        page.save(update_fields=changed)


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0041_thankyou_page"),
    ]

    operations = [
        migrations.RunPython(seed_forward, noop_reverse),
    ]
