from django.db import migrations

# English for the six collection cards. Fills only empty fields.

COPY = {
    "kvitka-dusha": {
        "text_en": (
            "<p>“Soul Flower” is living amaryllis that the family grows by hand until Christmas. "
            "It brings the beauty of living hippeastrum together with the art of a festive table. "
            "Deep red petals, silver bowls, natural pine and the flicker of candles make a refined "
            "arrangement that you grow and compose yourself.</p>"
            "<p>The value of this set is the shared wait for the flowers to open. Each flower "
            "becomes part of a small family story you will want to repeat every year.</p>"
        ),
        "box_items_en": "\n".join(
            [
                "Coupe vases — 2",
                "3 living amaryllis bulbs",
                "Fresh pine",
                "All the materials you need",
                "A masterclass on decorating the table quickly and without fuss",
            ]
        ),
        "alt_large_en": "A winter arrangement of pine and branches on a concrete plinth",
        "alt_small_en": "An arrangement of red amaryllis, pine and ribbons",
    },
    "korinnia": {
        "text_en": (
            "<p>Different kinds of fresh pine, natural textures and quiet tones, for a table "
            "setting with nothing extra. Only a natural harmony, the scent of a winter forest, "
            "and details you want to look at closely.</p>"
        ),
        "box_items_en": "\n".join(
            [
                "A vase",
                "3 kinds of fresh pine",
                "All the materials you need",
                "Antique bells",
                "A masterclass on decorating the table quickly and without fuss",
            ]
        ),
        "alt_large_en": "A table setting with a linen napkin, candles and flowers",
        "alt_small_en": "Hands tying a napkin with a ring on a plate",
    },
    "rodynnyi-kryshtal": {
        "text_en": (
            "<p>Do you remember the crystal service that stood in your grandmother’s cupboard "
            "when you were a child? It seemed so fine that it came to the table only for holidays. "
            "Or it gathered dust in the sideboard for decades, like a priceless jewel. "
            "It is time to take it out… Or to reinterpret it…</p>"
        ),
        "box_items_en": "\n".join(
            [
                "A fruit-bowl vase",
                "Trimmed branches of fresh pine",
                "All the materials you need to assemble the table arrangement",
                "Candles — 2",
                "Ornaments",
                "A link to a masterclass on assembling it quickly and enjoying the process",
            ]
        ),
        "alt_large_en": "A festive table in the garden with straw arrangements",
        "alt_small_en": "Straw wreaths, flowers and glasses on a festive table",
    },
    "tartan": {
        "text_en": (
            "<p>The collection is inspired by a European Christmas, where refinement is carried "
            "not only by the objects, but by taste, knowledge and upbringing.</p>"
            "<p>Deep burgundy and a classic tartan make a festive table of quiet luxury "
            "and the warmth of home.</p>"
        ),
        "box_items_en": "\n".join(
            [
                "Trimmed branches of fresh pine",
                "A tray and all the materials",
                "4 candles",
                "Ornaments",
            ]
        ),
        "alt_large_en": "A banquet hall with candlesticks and calla lilies",
        "alt_small_en": "A table setting with calla lilies, candles and crystal glasses",
    },
    "dytynstvo": {
        "text_en": (
            "<p>Recall the scent of the first peeled mandarin, and the shoebox of Christmas "
            "ornaments and silver tinsel. Metal horses, handmade snowflakes, sweets and mandarins…</p>"
            "<p>We carried that nostalgia into a contemporary table setting, so the Christmas table "
            "is not only beautiful, but full of familiar symbols, warm stories and family memories. "
            "Find your favourite ornament in the old box from childhood, add it to the arrangement, "
            "and tell your children about it.</p>"
        ),
        "box_items_en": "\n".join(
            [
                "A saucepan vase",
                "Fresh pine branches",
                "All the materials you need",
                "2 candles",
                "Ornaments",
                "A masterclass on decorating the table quickly and without fuss",
            ]
        ),
        "alt_large_en": "Wax candles among berries and pine cones",
        "alt_small_en": "Candles, pine cones and red berries on a festive table",
    },
    "spadshchyna": {
        "text_en": (
            "<p>For a long time, Christmas in Ukrainian families began with particular preparations. "
            "The house filled not only with the scent of pine and festive food, but with the scent "
            "of ripe wheat. The place of honour on the table belonged to the didukh — a symbol of "
            "memory of the ancestors, of prosperity, and of the unity of the family.</p>"
            "<p>The Heritage collection reinterprets these traditions in the contemporary art "
            "of table setting.</p>"
        ),
        "box_items_en": "\n".join(
            [
                "A fruit-bowl vase of Pokuttia ceramics",
                "Trimmed pine branches",
                "Decorative braids and sheaves",
                "All the materials you need to assemble the table arrangement",
                "Candles in a matching colour — 2",
                "A link to a masterclass on decorating the table quickly and without fuss with these materials",
            ]
        ),
        "alt_large_en": "A long festive table against red curtains",
        "alt_small_en": "A table setting with red anthuriums",
    },
}


def _empty(value):
    return not str(value or "").strip()


def fill_english(apps, schema_editor):
    del schema_editor
    HomeCollection = apps.get_model("content", "HomeCollection")
    for slug, payload in COPY.items():
        row = HomeCollection.objects.filter(slug=slug).first()
        if row is None:
            continue
        changed = []
        story = payload["text_en"]
        if _empty(row.text_en):
            row.text_en = story
            changed.append("text_en")
        if _empty(row.story_en):
            row.story_en = story
            changed.append("story_en")
        for field in ("box_items_en", "alt_large_en", "alt_small_en"):
            if _empty(getattr(row, field)):
                setattr(row, field, payload[field])
                changed.append(field)
        if changed:
            row.save(update_fields=changed)


def clear_english(apps, schema_editor):
    del schema_editor
    HomeCollection = apps.get_model("content", "HomeCollection")
    for slug, payload in COPY.items():
        row = HomeCollection.objects.filter(slug=slug).first()
        if row is None:
            continue
        story = payload["text_en"]
        changed = []
        for field, value in (
            ("text_en", story),
            ("story_en", story),
            ("box_items_en", payload["box_items_en"]),
            ("alt_large_en", payload["alt_large_en"]),
            ("alt_small_en", payload["alt_small_en"]),
        ):
            if getattr(row, field) == value:
                setattr(row, field, "")
                changed.append(field)
        if changed:
            row.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0047_ui_slots"),
    ]

    operations = [
        migrations.RunPython(fill_english, clear_english),
    ]
