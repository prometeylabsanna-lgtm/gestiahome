"""Заповнює порожні слоти поточними текстами. Викликає лише міграція."""

BLOCK_FIELDS = {
    "hero": {"title": "hero_title", "text": "hero_text", "cta": "hero_cta"},
    "collections": {"title": "collections_title", "link": "collections_link", "cta": "collections_cta"},
    "categories": {"title": "categories_label"},
    "popular": {"title": "popular_title", "cta": "popular_cta"},
    "advantages": {"title": "advantages_title", "text": "advantages_text", "cta": "advantages_cta"},
    "reviews": {"title": "reviews_title"},
    "callback": {
        "title": "callback_title",
        "text": "callback_text",
        "cta": "callback_cta",
        "note": "callback_note",
        "link": "callback_privacy",
    },
}

CONTACTS = {
    "title_uk": "Контакти",
    "title_en": "Contacts",
    "seo_title_uk": "Контакти Gestia Home — телефон, пошта та майстерня",
    "seo_title_en": "Contact Gestia Home — phone, studio address, email",
    "seo_description_uk": (
        "Контакти Gestia Home: телефон, електронна пошта й адреса майстерні. "
        "Напишіть у формі про святкові бокси, сервірування столу або доставку — ми відповімо."
    ),
    "seo_description_en": (
        "Contact Gestia Home by phone, email or the form on this page. "
        "Ask about festive table boxes, table setting and delivery — the studio will reply to you."
    ),
    "form_title_uk": "Зв'язатись з нами",
    "form_title_en": "Contact us",
}

SITE_EXTRA = {
    "nav_faq": ("Актуальні питання", "FAQ"),
    "nav_contacts": ("Контакти", "Contacts"),
    "logo_alt": ("Gestia Home", "Gestia Home"),
}


def _empty(value):
    return not str(value or "").strip()


def _fits(obj, name, value):
    field = obj._meta.get_field(name)
    limit = getattr(field, "max_length", None)
    return not limit or len(value) <= limit


def _pair(obj, stem, uk, en):
    changed = False
    for suffix, value in (("_uk", uk), ("_en", en)):
        name = f"{stem}{suffix}"
        if not hasattr(obj, name) or not _empty(getattr(obj, name)):
            continue
        if not _fits(obj, name, value):
            continue
        setattr(obj, name, value)
        changed = True
    return changed


def seed_ui_slots(apps, schema_editor):
    del schema_editor
    from src.content.literals import LITERALS
    from src.content.static_seed import place_static
    from src.content.ui_defaults import UI_FIELDS

    InterfaceCopy = apps.get_model("content", "InterfaceCopy")
    copy, _created = InterfaceCopy.objects.get_or_create(pk=1)
    for key, _label, uk, en, _limit, _aria, _group in UI_FIELDS:
        _pair(copy, key, uk, en)
    copy.save()

    ContactsPage = apps.get_model("content", "ContactsPage")
    page, _created = ContactsPage.objects.get_or_create(pk=1)
    for name, value in CONTACTS.items():
        if _empty(getattr(page, name)) and _fits(page, name, value):
            setattr(page, name, value)
    page.save()

    SiteSettings = apps.get_model("content", "SiteSettings")
    site, _created = SiteSettings.objects.get_or_create(pk=1)
    for stem in ("nav_about", "nav_all", "menu_title", "credit"):
        uk, en = LITERALS[stem]
        _pair(site, stem, uk, en)
    for stem, pair in SITE_EXTRA.items():
        _pair(site, stem, pair[0], pair[1])
    light = place_static("nd/g-mark-light.png", "site/g-mark-light.png")
    dark = place_static("nd/g-mark-dark.png", "site/g-mark-dark.png")
    if light and not site.mark_light:
        site.mark_light = light
    if dark and not site.mark_dark:
        site.mark_dark = dark
    site.save()

    ContactForms = apps.get_model("content", "ContactForms")
    forms, _created = ContactForms.objects.get_or_create(pk=1)
    for field in ContactForms._meta.fields:
        if not field.name.endswith("_uk"):
            continue
        stem = field.name[:-3]
        if stem not in LITERALS:
            continue
        uk, en = LITERALS[stem]
        _pair(forms, stem, uk, en)
    forms.save()

    HomeBlock = apps.get_model("content", "HomeBlock")
    for key, mapping in BLOCK_FIELDS.items():
        block = HomeBlock.objects.filter(key=key).first()
        if block is None:
            continue
        for field_name, literal_key in mapping.items():
            uk, en = LITERALS[literal_key]
            _pair(block, field_name, uk, en)
        block.save()


def unseed_ui_slots(apps, schema_editor):
    del apps, schema_editor
