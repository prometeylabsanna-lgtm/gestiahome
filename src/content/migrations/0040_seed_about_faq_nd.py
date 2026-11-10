from django.db import migrations

ABOUT_TITLE = "Hi, I’m Gestia"
ABOUT_SEO_TITLE = "Про нас — Gestia Home"
ABOUT_SEO_DESC = (
    "Gestia Home — про жінку, яка створює дім. Святкові бокси та декор, "
    "щоб надихати, об’єднувати та створювати приємну атмосферу."
)

INTRO_TEXT = (
    "<p>Серед безлічі можливостей, які відкриває  сучасний світ перед  жінкою "
    "є одна особлива роль -бути <em>жінкою, яка створює дім</em>.</p>"
    "<p><em>Дім</em>, який не є місцем нескінченних обов’язків, а є простором "
    "творчості, натхнення, любові та самовираження.</p>"
    "<p>І це не про  особливий статус, великий будинок чи вишуканий інтер’єр, "
    "це про <em>внутрішній стан</em>, який стає важливою частиною особистого життя, "
    "як мода, стиль, подорожі чи мистецтво.<br>Це про бажання раніше прийти додому, "
    "увімкнути музику, запалити свічки, красиво накрити стіл та з посмішкою зустріти друзів.</p>"
)

GESTIA_QUOTE = (
    "ГЕСТІЯ - ДАВНЬОГРЕЦЬКА БОГИНЯ РОДИННОГО ТЕПЛА, ГАРМОНІЇ ТА СВЯЩЕННОГО ВОГНЮ, "
    "ЩО ОБ’ЄДНУЄ ЛЮДЕЙ, ДРУЗІВ ТА ЗВ’ЯЗОК МІЖ ПОКОЛІННЯМИ."
)

GESTIA_TEXT = (
    "<p>І як прекрасно, що сучасна <em>Гестія</em> не зобов’язана робити все самостійно. "
    "Адже її головна роль — не виконувати нескінченний перелік справ, а "
    "<em>надихати, об’єднувати та створювати приємну атмосферу</em></p>"
)

APPROACH_TEXT = (
    "GESTIA HOME бере на себе всі зайві приготування. Тобі залишається тільки "
    "вдягнути улюблену сукню, розставити декор та відкрити двері."
)

TOGETHER_TEXT = (
    "<p>Ми мріємо повернути моду на домашні вечері, спонтанні зустрічі, великі "
    "сімейні свята та маленькі щоденні приводи бути разом.</p>"
    "<p>Бо красиво накритий стіл — це не демонстрація достатку. Це жест уваги.<br>"
    "Саме за столом народжуються дружба, довіра, спільні спогади та сімейні традиції.<br>"
    "Це спосіб сказати без слів: «Я рада, що ти сьогодні тут».</p>"
)

CLOSING_TEXT = (
    "<p>Ми впевнені, що сучасна жінка може бути успішною в усьому, що вона сама обирає. "
    "І, погодьтесь, бути натхненною господинею власного дому — один із найкрасивіших її виборів.</p>"
)

CTA_UK = "Перейти до каталогу"

FAQ_ITEMS = [
    {
        "question_uk": "Що входить у святковий бокс?",
        "answer_uk": (
            "<p>Ми постійно працюємо над кількістю предметів у боксі, намагаючись "
            "врахувати всі святкові компоненти. Перші різдвяні колекції боксів мають:</p>"
            "<ul>"
            "<li>красиву вазу, яку можна використовувати у подальшому</li>"
            "<li>живу хвою, яка вже повністю підготовлена для роботи</li>"
            "<li>всі необхідні технічні матеріали</li>"
            "<li>іграшки чи декор</li>"
            "<li>дизайнерські столові свічки 35 або 45 см</li>"
            "</ul>"
        ),
        "sort": 0,
    },
    {
        "question_uk": "Який посуд та столові прибори підійдуть під бокс?",
        "answer_uk": (
            "<p>Святкові бокси універсальні та доповнять настроєм будь-який посуд та "
            "столовий текстиль. Якщо ти хочеш ідеально об’єднати свій посуд з декором, "
            "радимо скористатися додатковими елементами боксу з розділу «Столові аксесуари», "
            "які підібрані під кожний сет окремо.</p>"
        ),
        "sort": 1,
    },
    {
        "question_uk": "Коли розпочинати декорувати стіл до Різдвяних свят?",
        "answer_uk": (
            "<p>Розпочинай декорування столу, коли матимеш натхнення. Це можна зробити "
            "самостійно, можна зібрати друзів чи прикрасити стіл з дітьми, коли будеш "
            "декорувати новорічну ялинку.</p>"
            "<p>Але щоб не втомитися, радимо прикрашати стіл заздалегідь, за 7–10 днів "
            "до свята. Це дозволить тобі насолодитися процесом та розтягнути задоволення "
            "від результату.</p>"
        ),
        "sort": 2,
    },
    {
        "question_uk": "Скільки може простояти гілля хвої?",
        "answer_uk": (
            "<p>Святкові декоративні сети довготривалі. Ми спеціально обрали особливий вид "
            "піхти, який може простояти в приміщенні до 25 градусів до 3-х місяців у "
            "незмінному вигляді.</p>"
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


def _place(name, stored):
    from src.content.static_seed import place_static

    return place_static(f"nd/about/{name}", stored)


def seed_forward(apps, schema_editor):
    AboutPage = apps.get_model("content", "AboutPage")
    FaqPage = apps.get_model("content", "FaqPage")
    FaqItem = apps.get_model("content", "FaqItem")
    FooterLink = apps.get_model("content", "FooterLink")

    page, _ = AboutPage.objects.get_or_create(pk=1)
    about_updates = {
        "intro_text_uk": INTRO_TEXT,
        "intro_photo_left_alt_uk": "Жінка створює композицію з овочів на білому столі",
        "intro_photo_main_alt_uk": "Жінка сервірує стіл лляними серветками та кільцями",
        "gestia_quote_uk": GESTIA_QUOTE,
        "gestia_plate_alt_uk": "Руки тримають зелену тарілку над святково накритим столом",
        "gestia_photo_alt_uk": "Круглий стіл із зеленою флористикою, свічками та кришталем",
        "gestia_text_uk": GESTIA_TEXT,
        "approach_text_uk": APPROACH_TEXT,
        "together_photo_alt_uk": "Квіткова композиція біля вікна",
        "together_text_uk": TOGETHER_TEXT,
        "closing_text_uk": CLOSING_TEXT,
        "cta_uk": CTA_UK,
        "seo_title_uk": ABOUT_SEO_TITLE,
        "seo_description_uk": ABOUT_SEO_DESC,
    }
    changed = _fill(page, about_updates)
    if page.title_uk in ("", "Про нас"):
        page.title_uk = ABOUT_TITLE
        changed.append("title_uk")

    photo_map = {
        "intro_photo_left": ("about-peppers-woman.jpg", "about/intro-left.jpg"),
        "intro_photo_main": ("about-woman-beige.jpg", "about/intro-main.jpg"),
        "gestia_plate": ("about-plate.jpg", "about/gestia-plate.jpg"),
        "gestia_photo": ("about-green-table.jpg", "about/gestia-photo.jpg"),
        "together_photo": ("about-flowers-window.jpg", "about/together.jpg"),
    }
    for field, (src, dest) in photo_map.items():
        if not getattr(page, field):
            stored = _place(src, dest)
            if stored:
                setattr(page, field, stored)
                changed.append(field)

    if changed:
        page.save(update_fields=changed)

    faq, _ = FaqPage.objects.get_or_create(pk=1)
    faq_updates = {
        "title_uk": "Актуальні<br>питання",
        "crumb_uk": "Актуальні питання",
        "image_alt_uk": "Святковий стіл з композиціями, свічками та серветками",
        "contact_title_uk": "Залишились питання?",
        "contact_text_uk": "<p>Напишіть нам — ми допоможемо підібрати бокс.</p>",
        "seo_title_uk": "Актуальні питання — Gestia Home",
        "seo_description_uk": (
            "Відповіді на актуальні питання про святкові бокси Gestia Home: що входить "
            "у бокс, який посуд підійде, коли декорувати стіл та скільки стоїть хвоя."
        ),
    }
    faq_changed = _fill(faq, faq_updates)
    if not faq.image:
        stored = _place("about-table-wide.jpg", "faq/table-wide.jpg")
        if stored:
            faq.image = stored
            faq_changed.append("image")
    if faq_changed:
        faq.save(update_fields=faq_changed)

    if not FaqItem.objects.filter(page=faq).exists():
        for row in FAQ_ITEMS:
            FaqItem.objects.create(page=faq, is_active=True, **row)

    if not FooterLink.objects.filter(column="info", url_name="faq").exists():
        FooterLink.objects.create(
            column="info",
            label_uk="Актуальні питання",
            label_en="FAQ",
            url_name="faq",
            sort=4,
        )


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0039_about_faq_nd"),
    ]

    operations = [
        migrations.RunPython(seed_forward, noop_reverse),
    ]
