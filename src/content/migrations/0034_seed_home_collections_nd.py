from django.db import migrations

OLD_HERO_TITLE_UK = "Декор для дому, текстиль \nі флористика"
OLD_HERO_TITLE_EN = "Home decor, textiles \nand floristry"
OLD_HERO_TEXT_UK = (
    "Декор для дому, домашній текстиль, флористика та одяг для дому від Gestia Home. "
    "Створюйте затишний простір із речами, у яких поєднуються естетика та функціональність"
)
OLD_HERO_TEXT_EN = (
    "Home decor, home textiles, floristry, and clothing for the home from Gestia Home. "
    "Create a cosy space with pieces that bring aesthetics and function together."
)
NEW_HERO_TITLE = "Art of modern hospitality"
NEW_HERO_TEXT_UK = "Святкові бокси для самостійного декорування столу"
NEW_HERO_TEXT_EN = "Festive boxes for decorating your own table"

BLOCK_DEFAULTS = {
    "sort": 2,
    "title_uk": "Різдвяна колекція святкових боксів",
    "title_en": "Christmas collection of festive boxes",
    "link_uk": "Традиції починаються зі столу",
    "link_en": "Traditions begin at the table",
    "cta_uk": "Дізнатись детальніше",
    "cta_en": "Learn more",
}

COLLECTIONS = (
    {
        "sort": 1,
        "label_uk": "Колекція",
        "label_en": "Collection",
        "title_uk": "Квітка-душа",
        "title_en": "Soul Flower",
        "text_uk": (
            "<p>«Квітка-душа» — живі квіти амарилісу, які родина власноруч вирощує до Різдва. "
            "Поєднує красу живих квітів гіпеаструму із мистецтвом святкового сервірування. "
            "Насичені червоні пелюстки, срібні чаші, натуральна хвоя та мерехтіння свічок "
            "створюють разом вишукану композицію, яку ви вирощуєте та оформлюєте власноруч.</p>"
            "<p>Цінність цього сету — спільне очікування на розквіт квітів. Кожна квітка стає "
            "частиною маленької родинної історії, яку захочеться повторювати щороку.</p>"
        ),
        "large": "kvitka-large.jpg",
        "small": "kvitka-small.jpg",
        "alt_large_uk": "Зимова композиція з хвої та гілок на бетонному постаменті",
        "alt_small_uk": "Композиція з червоних амарилісів, хвої та стрічок",
    },
    {
        "sort": 2,
        "label_uk": "Колекція",
        "label_en": "Collection",
        "title_uk": "Коріння",
        "title_en": "Roots",
        "text_uk": (
            "<p>Різні види живої хвої, природні фактури та стримані відтінки, щоб створити "
            "сервірування, у якому немає нічого зайвого. Лише природна гармонія, аромат "
            "зимового лісу та деталі, які хочеться розглядати.</p>"
        ),
        "large": "korinnia-large.jpg",
        "small": "korinnia-small.jpg",
        "alt_large_uk": "Сервірування з лляною серветкою, свічками та квітами",
        "alt_small_uk": "Руки зав’язують серветку з кільцем на тарілці",
    },
    {
        "sort": 3,
        "label_uk": "Колекція",
        "label_en": "Collection",
        "title_uk": "Родинний\nкришталь",
        "title_en": "Family\nCrystal",
        "text_uk": (
            "<p>Пам’ятаєте, як у дитинстві у бабусиній шафі стояв кришталевий сервіз? Він здавався "
            "настільки вишуканим, що його ставили на стіл виключно на свята. А то й взагалі він "
            "десятиріччями збирав пил у серванті, наче безцінний ювелірний експонат. Настав час "
            "його дістати… Або інтерпретувати…</p>"
        ),
        "large": "kryshtal-large.jpg",
        "small": "kryshtal-small.jpg",
        "alt_large_uk": "Святковий стіл у саду з солом’яними композиціями",
        "alt_small_uk": "Солом’яні вінки, квіти та келихи на святковому столі",
    },
    {
        "sort": 4,
        "label_uk": "Колекція",
        "label_en": "Collection",
        "title_uk": "Тартан",
        "title_en": "Tartan",
        "text_uk": (
            "<p>Колекція натхненна естетикою європейського Різдва, де вишуканість передається "
            "не лише через речі, а й через смак, знання та виховання.</p>"
            "<p>Благородні відтінки бордо та класична клітинка створюють святкове сервірування, "
            "сповнене стриманої розкоші та домашнього тепла.</p>"
        ),
        "large": "tartan-large.jpg",
        "small": "tartan-small.jpg",
        "alt_large_uk": "Банкетний зал зі свічниками та калами",
        "alt_small_uk": "Сервірування з калами, свічками та кришталевими келихами",
    },
    {
        "sort": 5,
        "label_uk": "Колекція",
        "label_en": "Collection",
        "title_uk": "Дитинство",
        "title_en": "Childhood",
        "text_uk": (
            "<p>Пригадайте аромат першої очищеної мандаринки та дістаньте з пам’яті спогади про "
            "коробку з-під взуття з ялинковими іграшками та срібним дощиком. Металеві коники, "
            "саморобні сніжинки, цукерки та мандаринки…</p>"
            "<p>Ми перенесли цю ностальгію у сучасне сервірування, щоб різдвяний стіл став не "
            "просто красивим, а й сповненим знайомих символів, теплих історій та рідних спогадів. "
            "Знайди у старій коробці новорічних іграшок з дитинства свою найулюбленішу, додай її "
            "до композиції та розкажи про неї своїм дітям!</p>"
        ),
        "large": "dytynstvo-large.jpg",
        "small": "dytynstvo-small.jpg",
        "alt_large_uk": "Воскові свічки серед ягід і шишок",
        "alt_small_uk": "Свічки, шишки та червоні ягоди на святковому столі",
    },
    {
        "sort": 6,
        "label_uk": "Різдвяна колекція",
        "label_en": "Christmas collection",
        "title_uk": "Спадщина",
        "title_en": "Heritage",
        "text_uk": (
            "<p>Здавна в українських родинах Різдво починалося з особливих приготувань. Дім "
            "наповнювався не тільки ароматом хвої та святкових страв, а й ароматом зрілого "
            "колосся. Почесне місце на столі займав Дідух — символ пам’яті про предків, "
            "добробуту та єдності роду.</p>"
            "<p>Колекція «Спадщина» переосмислює ці традиції в сучасному мистецтві сервірування.</p>"
        ),
        "large": "spadshchyna-large.jpg",
        "small": "spadshchyna-small.jpg",
        "alt_large_uk": "Довгий святковий стіл на тлі червоних штор",
        "alt_small_uk": "Сервірування з червоними антуріумами",
    },
)


def _place(name):
    from src.content.static_seed import place_static

    return place_static(f"nd/collections/{name}", f"home/collections/{name}")


def forwards(apps, schema_editor):
    del schema_editor
    HomeBlock = apps.get_model("content", "HomeBlock")
    HomeCollection = apps.get_model("content", "HomeCollection")
    Category = apps.get_model("catalog", "Category")

    hero = HomeBlock.objects.filter(key="hero").first()
    if hero is not None:
        updates = []
        if hero.title_uk == OLD_HERO_TITLE_UK:
            hero.title_uk = NEW_HERO_TITLE
            updates.append("title_uk")
        if hero.title_en == OLD_HERO_TITLE_EN:
            hero.title_en = NEW_HERO_TITLE
            updates.append("title_en")
        if hero.text_uk == OLD_HERO_TEXT_UK:
            hero.text_uk = NEW_HERO_TEXT_UK
            updates.append("text_uk")
        if hero.text_en == OLD_HERO_TEXT_EN:
            hero.text_en = NEW_HERO_TEXT_EN
            updates.append("text_en")
        if updates:
            hero.save(update_fields=updates)

    block, _created = HomeBlock.objects.get_or_create(
        key="collections",
        defaults=BLOCK_DEFAULTS,
    )
    if not _created:
        patch = []
        for field, value in BLOCK_DEFAULTS.items():
            if field == "sort":
                continue
            current = getattr(block, field, "")
            if not (current or "").strip():
                setattr(block, field, value)
                patch.append(field)
        if patch:
            block.save(update_fields=patch)

    category = Category.objects.filter(slug="rizdvyani-boksy").first()
    category_id = category.pk if category else None

    for row in COLLECTIONS:
        collection, created = HomeCollection.objects.get_or_create(
            block=block,
            title_uk=row["title_uk"],
            defaults={
                "sort": row["sort"],
                "label_uk": row["label_uk"],
                "label_en": row["label_en"],
                "title_en": row["title_en"],
                "text_uk": row["text_uk"],
                "text_en": "",
                "alt_large_uk": row["alt_large_uk"],
                "alt_small_uk": row["alt_small_uk"],
                "category_id": category_id,
                "is_active": True,
            },
        )
        if created or not collection.image_large:
            large = _place(row["large"])
            if large:
                collection.image_large = large
        if created or not collection.image_small:
            small = _place(row["small"])
            if small:
                collection.image_small = small
        collection.save()


def backwards(apps, schema_editor):
    del schema_editor
    HomeBlock = apps.get_model("content", "HomeBlock")
    hero = HomeBlock.objects.filter(key="hero").first()
    if hero is None:
        return
    updates = []
    if hero.title_uk == NEW_HERO_TITLE:
        hero.title_uk = OLD_HERO_TITLE_UK
        updates.append("title_uk")
    if hero.title_en == NEW_HERO_TITLE:
        hero.title_en = OLD_HERO_TITLE_EN
        updates.append("title_en")
    if hero.text_uk == NEW_HERO_TEXT_UK:
        hero.text_uk = OLD_HERO_TEXT_UK
        updates.append("text_uk")
    if hero.text_en == NEW_HERO_TEXT_EN:
        hero.text_en = OLD_HERO_TEXT_EN
        updates.append("text_en")
    if updates:
        hero.save(update_fields=updates)


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0033_home_collections_nd"),
        ("catalog", "0020_media_kind_blank"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
