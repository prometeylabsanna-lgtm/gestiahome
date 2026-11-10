from django.db import migrations

ABOUT_EN = {
    "intro_text_en": (
        "<p>Among the countless paths the modern world offers a woman, there is "
        "one very special role — being <em>the woman who creates a home</em>.</p>"
        "<p>A <em>home</em> that is not a place of endless chores, but a space "
        "for creativity, inspiration, love and self-expression.</p>"
        "<p>It isn’t about status, a big house or a refined interior. It’s about "
        "an <em>inner state</em> that becomes part of your personal life, just "
        "like fashion, style, travel or art.<br>It’s the wish to come home a "
        "little earlier, put on some music, light the candles, set a beautiful "
        "table and greet your friends with a smile.</p>"
    ),
    "intro_photo_left_alt_en": (
        "A woman arranging a vegetable composition on a white table"
    ),
    "intro_photo_main_alt_en": (
        "A woman setting the table with linen napkins and napkin rings"
    ),
    "gestia_quote_en": (
        "HESTIA IS THE ANCIENT GREEK GODDESS OF THE HEARTH, OF HARMONY AND THE "
        "SACRED FIRE THAT BRINGS PEOPLE, FRIENDS AND GENERATIONS TOGETHER."
    ),
    "gestia_plate_alt_en": "Hands holding a green plate above a festive table",
    "gestia_photo_alt_en": "A round table with green florals, candles and crystal",
    "gestia_text_en": (
        "<p>And how wonderful that the modern <em>Gestia</em> doesn’t have to "
        "do it all on her own. Her true role isn’t to tick off an endless "
        "to-do list, but to <em>inspire, bring people together and create a "
        "warm atmosphere</em>.</p>"
    ),
    "approach_text_en": (
        "GESTIA HOME takes care of all the extra preparation. All that’s left "
        "for you is to slip into your favourite dress, arrange the décor and "
        "open the door."
    ),
    "together_photo_alt_en": "A floral arrangement by the window",
    "together_text_en": (
        "<p>We dream of bringing back home dinners, spontaneous get-togethers, "
        "big family celebrations and the small everyday reasons to be together.</p>"
        "<p>Because a beautifully set table is not a display of wealth. It’s a "
        "gesture of care.<br>It’s at the table that friendships, trust, shared "
        "memories and family traditions are born.<br>It’s a way of saying "
        "without words: “I’m so glad you’re here tonight.”</p>"
    ),
    "closing_text_en": (
        "<p>We believe a modern woman can succeed in whatever she chooses. And, "
        "you must agree, being the inspired hostess of her own home is one of "
        "the most beautiful choices of all.</p>"
    ),
    "cta_en": "Browse the catalogue",
    "seo_title_en": "About us — Gestia Home",
    "seo_description_en": (
        "Gestia Home is about the woman who creates a home. Festive boxes and "
        "décor to inspire, bring people together and create a warm atmosphere."
    ),
}

FAQ_PAGE_EN = {
    "title_en": "Good<br>to know",
    "crumb_en": "FAQ",
    "image_alt_en": "A festive table with arrangements, candles and napkins",
    "contact_title_en": "Still have questions?",
    "contact_text_en": (
        "<p>Write to us — we’ll help you choose the right box.</p>"
    ),
    "seo_title_en": "FAQ — Gestia Home",
    "seo_description_en": (
        "Answers to common questions about Gestia Home festive boxes: what’s "
        "inside a box, which tableware works with it, when to start decorating "
        "and how long the fir lasts."
    ),
}

FAQ_ITEMS_EN = [
    {
        "question_uk": "Що входить у святковий бокс?",
        "question_en": "What’s inside a festive box?",
        "answer_en": (
            "<p>We keep refining what goes into each box so that every festive "
            "detail is covered. Our first Christmas collections include:</p>"
            "<ul>"
            "<li>a beautiful vase you can keep using long after the holidays</li>"
            "<li>fresh fir branches, fully prepared and ready to arrange</li>"
            "<li>all the technical materials you’ll need</li>"
            "<li>ornaments or décor</li>"
            "<li>designer table candles, 35 or 45 cm</li>"
            "</ul>"
        ),
        "sort": 0,
    },
    {
        "question_uk": "Який посуд та столові прибори підійдуть під бокс?",
        "question_en": "Which tableware and cutlery go with a box?",
        "answer_en": (
            "<p>Our festive boxes are versatile and will add a festive mood to "
            "any tableware and table linen. If you’d like your dishes and décor "
            "to match perfectly, try the extra pieces from our “Table "
            "accessories” section — they’re selected for each set individually.</p>"
        ),
        "sort": 1,
    },
    {
        "question_uk": "Коли розпочинати декорувати стіл до Різдвяних свят?",
        "question_en": "When should I start decorating the table for Christmas?",
        "answer_en": (
            "<p>Start whenever inspiration strikes. You can do it on your own, "
            "invite friends over, or decorate the table with your children "
            "while trimming the Christmas tree.</p>"
            "<p>To keep it stress-free, we recommend decorating 7–10 days "
            "before the holiday. That way you can enjoy the process and savour "
            "the result for longer.</p>"
        ),
        "sort": 2,
    },
    {
        "question_uk": "Скільки може простояти гілля хвої?",
        "question_en": "How long do the fir branches last?",
        "answer_en": (
            "<p>Our festive décor sets are made to last. We chose a special "
            "variety of fir that keeps its look for up to 3 months indoors at "
            "temperatures up to 25 °C.</p>"
        ),
        "sort": 3,
    },
]


def _fill(obj, updates):
    changed = []
    for key, value in updates.items():
        current = getattr(obj, key, None)
        if current in (None, ""):
            setattr(obj, key, value)
            changed.append(key)
    return changed


def seed_forward(apps, schema_editor):
    AboutPage = apps.get_model("content", "AboutPage")
    FaqPage = apps.get_model("content", "FaqPage")
    FaqItem = apps.get_model("content", "FaqItem")
    FooterLink = apps.get_model("content", "FooterLink")

    about, _ = AboutPage.objects.get_or_create(pk=1)
    about_changed = _fill(about, ABOUT_EN)
    if about_changed:
        about.save(update_fields=about_changed)

    faq, _ = FaqPage.objects.get_or_create(pk=1)
    faq_changed = _fill(faq, FAQ_PAGE_EN)
    if faq_changed:
        faq.save(update_fields=faq_changed)

    for row in FAQ_ITEMS_EN:
        item = (
            FaqItem.objects.filter(page=faq, question_uk=row["question_uk"], sort=row["sort"])
            .order_by("id")
            .first()
        )
        if item is None:
            item = (
                FaqItem.objects.filter(page=faq, question_uk=row["question_uk"])
                .order_by("sort", "id")
                .first()
            )
        if item is None:
            continue
        item_changed = _fill(
            item,
            {
                "question_en": row["question_en"],
                "answer_en": row["answer_en"],
            },
        )
        if item_changed:
            item.save(update_fields=item_changed)

    for link in FooterLink.objects.filter(url_name="faq"):
        if link.label_en in (None, ""):
            link.label_en = "FAQ"
            link.save(update_fields=["label_en"])


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0042_seed_thankyou_page"),
    ]

    operations = [
        migrations.RunPython(seed_forward, noop_reverse),
    ]
