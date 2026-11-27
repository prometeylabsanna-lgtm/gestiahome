from django.core.cache import cache
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.utils import OperationalError, ProgrammingError

from src.content.media import MediaChoice
from src.core.fields import WebPImageField
from src.core.utils import localized

IMAGE_VALIDATOR = FileExtensionValidator(["jpg", "jpeg", "png", "webp"])
VIDEO_VALIDATOR = FileExtensionValidator(["mp4", "webm"])


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(self.cache_key)

    @classmethod
    def load(cls):
        cached = cache.get(cls.cache_key)
        if cached is not None:
            return cached
        obj, _created = cls.objects.get_or_create(pk=1)
        cache.set(cls.cache_key, obj, 60)
        return obj


class SiteSettings(SingletonModel):
    cache_key = "site_settings_v2"
    phone = models.CharField("Телефон", max_length=40, default="+380000000000")
    email = models.EmailField("Електронна пошта", blank=True)
    address_uk = models.CharField("Адреса", max_length=255, blank=True)
    address_en = models.CharField("Адреса (EN)", max_length=255, blank=True)
    address_fr = models.CharField("Адреса (FR)", max_length=255, blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    pinterest_url = models.URLField("Pinterest", blank=True)
    telegram_url = models.URLField("Telegram", blank=True, help_text="Посилання t.me/… у соцряді.")
    developer_note_uk = models.CharField("Підпис розробника", max_length=160, blank=True)
    developer_note_en = models.CharField("Підпис розробника (EN)", max_length=160, blank=True)
    developer_note_fr = models.CharField("Підпис розробника (FR)", max_length=160, blank=True)
    logo = models.ImageField(
        "Логотип",
        upload_to="site/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Шапка близько 113×43, підвал 191×73. JPG або PNG.",
    )
    logo_alt_uk = models.CharField("Підпис логотипа", max_length=80, blank=True)
    logo_alt_en = models.CharField("Підпис логотипа (EN)", max_length=80, blank=True)
    logo_alt_fr = models.CharField("Підпис логотипа (FR)", max_length=80, blank=True)
    mark_light = models.ImageField(
        "Знак G, світлий",
        upload_to="site/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Світлий знак на темному тлі. PNG.",
    )
    mark_dark = models.ImageField(
        "Знак G, темний",
        upload_to="site/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Темний знак на світлому тлі підвалу. PNG.",
    )
    nav_about_uk = models.CharField("Пункт «Про нас»", max_length=16, blank=True)
    nav_about_en = models.CharField("Пункт «Про нас» (EN)", max_length=16, blank=True)
    nav_about_fr = models.CharField("Пункт «Про нас» (FR)", max_length=16, blank=True)
    nav_all_uk = models.CharField("Пункт «Усі товари»", max_length=20, blank=True)
    nav_all_en = models.CharField("Пункт «Усі товари» (EN)", max_length=20, blank=True)
    nav_all_fr = models.CharField("Пункт «Усі товари» (FR)", max_length=20, blank=True)
    menu_title_uk = models.CharField(
        "Заголовок у меню",
        max_length=16,
        blank=True,
        help_text="У мобільному меню. Кнопка в шапці лишається своєю.",
    )
    menu_title_en = models.CharField("Заголовок у меню (EN)", max_length=16, blank=True)
    menu_title_fr = models.CharField("Заголовок у меню (FR)", max_length=16, blank=True)
    nav_faq_uk = models.CharField("Пункт «Актуальні питання»", max_length=40, blank=True)
    nav_faq_en = models.CharField("Пункт «Актуальні питання» (EN)", max_length=40, blank=True)
    nav_faq_fr = models.CharField("Пункт «Актуальні питання» (FR)", max_length=40, blank=True)
    nav_contacts_uk = models.CharField("Пункт «Контакти»", max_length=40, blank=True)
    nav_contacts_en = models.CharField("Пункт «Контакти» (EN)", max_length=40, blank=True)
    nav_contacts_fr = models.CharField("Пункт «Контакти» (FR)", max_length=40, blank=True)
    credit_uk = models.CharField("Текст перед PrometeyLabs", max_length=32, blank=True)
    credit_en = models.CharField("Текст перед PrometeyLabs (EN)", max_length=32, blank=True)
    credit_fr = models.CharField("Текст перед PrometeyLabs (FR)", max_length=32, blank=True)
    en_enabled = models.BooleanField("Англійська увімкнена", default=True)
    fr_enabled = models.BooleanField("Французька увімкнена", default=True)
    telegram_notify_orders = models.BooleanField("Telegram: замовлення", default=True)
    telegram_notify_leads = models.BooleanField("Telegram: заявки", default=True)
    color_ink = models.CharField("Колір тексту", max_length=7, default="#241c16")
    color_paper = models.CharField("Колір тла", max_length=7, default="#f3eee6")
    color_accent = models.CharField("Акцент", max_length=7, default="#8d3b2a")
    footer_note_uk = models.CharField("Підпис у підвалі", max_length=255, blank=True)
    footer_note_en = models.CharField("Підпис у підвалі (EN)", max_length=255, blank=True)
    footer_note_fr = models.CharField("Підпис у підвалі (FR)", max_length=255, blank=True)

    class Meta:
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "Налаштування сайту"

    def __str__(self):
        return "Налаштування сайту"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._sync_global_style()

    def _sync_global_style(self):
        from src.content.colors import TOKEN_ACCENT, TOKEN_INK, TOKEN_PAPER, normalize_hex
        from src.content.models_styles import PageStyle

        try:
            PageStyle.objects.filter(page=PageStyle.Key.GLOBAL).update(
                text_color=normalize_hex(self.color_ink) or TOKEN_INK,
                background_color=normalize_hex(self.color_paper) or TOKEN_PAPER,
                hover_color=normalize_hex(self.color_accent) or TOKEN_ACCENT,
            )
        except (OperationalError, ProgrammingError):
            return

    @property
    def address(self):
        return localized(self, "address")

    @property
    def logo_alt(self):
        return localized(self, "logo_alt")

    @property
    def nav_about(self):
        return localized(self, "nav_about")

    @property
    def nav_all(self):
        return localized(self, "nav_all")

    @property
    def nav_faq(self):
        return localized(self, "nav_faq")

    @property
    def nav_contacts(self):
        return localized(self, "nav_contacts")

    @property
    def menu_title(self):
        return localized(self, "menu_title")

    @property
    def credit(self):
        return localized(self, "credit")

    @property
    def footer_note(self):
        return localized(self, "footer_note")

    @property
    def developer_note(self):
        return localized(self, "developer_note")

    @property
    def copyright_lead(self):
        note = self.footer_note or ""
        return note.split("|", 1)[0]

    @property
    def copyright_tail(self):
        note = self.footer_note or ""
        parts = note.split("|", 1)
        return parts[1] if len(parts) == 2 else ""


class HomeBlock(MediaChoice):
    class Key(models.TextChoices):
        HERO = "hero", "Головний банер"
        COLLECTIONS = "collections", "Колекції"
        CATEGORIES = "categories", "Категорії"
        VIDEO = "video", "Відео 1"
        POPULAR = "popular", "Популярні товари"
        ADVANTAGES = "advantages", "Переваги"
        VIDEO_2 = "video_2", "Відео 2"
        REVIEWS = "reviews", "Відгуки"
        CALLBACK = "callback", "Зворотний дзвінок"
        LOCALE = "locale", "Країна та мова"
        MEGA = "mega", "Мегаменю"
        CATALOG = "catalog", "Каталог"
        PDP_SHIP = "pdp_ship", "Доставка товару"
        PDP_PAY = "pdp_pay", "Оплата товару"
        PDP_SET = "pdp_set", "Товари сету"
        PDP_RELATED = "pdp_related", "Схожі товари"

    rich_text_fields = ("text_uk", "text_en", "text_fr")
    key = models.CharField("Ключ", max_length=32, choices=Key.choices, unique=True)
    title_uk = models.CharField("Заголовок", max_length=200, blank=True)
    title_en = models.CharField("Заголовок (EN)", max_length=200, blank=True)
    title_fr = models.CharField("Заголовок (FR)", max_length=200, blank=True)
    text_uk = models.TextField("Текст", blank=True)
    text_en = models.TextField("Текст (EN)", blank=True)
    text_fr = models.TextField("Текст (FR)", blank=True)
    image = models.ImageField(
        "Зображення",
        upload_to="home/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Одна картинка для десктопу і мобільного.",
    )
    image_mobile = models.ImageField(
        "Зображення (застаріле)",
        upload_to="home/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Не використовується. Залишено для сумісності.",
    )
    video = models.FileField(
        "Відео",
        upload_to="home/video/",
        blank=True,
        validators=[VIDEO_VALIDATOR],
    )
    text_mobile_uk = models.TextField("Текст (застаріле)", blank=True)
    text_mobile_en = models.TextField("Текст (застаріле, EN)", blank=True)
    text_mobile_fr = models.TextField("Текст (застаріле, FR)", blank=True)
    seo_title_uk = models.CharField("SEO-заголовок", max_length=200, blank=True)
    seo_title_en = models.CharField("SEO-заголовок (EN)", max_length=200, blank=True)
    seo_title_fr = models.CharField("SEO-заголовок (FR)", max_length=200, blank=True)
    seo_description_uk = models.CharField("SEO-опис", max_length=300, blank=True)
    seo_description_en = models.CharField("SEO-опис (EN)", max_length=300, blank=True)
    seo_description_fr = models.CharField("SEO-опис (FR)", max_length=300, blank=True)
    cta_uk = models.CharField("Текст кнопки", max_length=200, blank=True)
    cta_en = models.CharField("Текст кнопки (EN)", max_length=200, blank=True)
    cta_fr = models.CharField("Текст кнопки (FR)", max_length=200, blank=True)
    link_uk = models.CharField("Другий підпис", max_length=160, blank=True)
    link_en = models.CharField("Другий підпис (EN)", max_length=160, blank=True)
    link_fr = models.CharField("Другий підпис (FR)", max_length=160, blank=True)
    note_uk = models.TextField("Примітка", blank=True)
    note_en = models.TextField("Примітка (EN)", blank=True)
    note_fr = models.TextField("Примітка (FR)", blank=True)
    lines_uk = models.TextField("Рядки підписів", blank=True)
    lines_en = models.TextField("Рядки підписів (EN)", blank=True)
    lines_fr = models.TextField("Рядки підписів (FR)", blank=True)
    sort = models.PositiveIntegerField("Порядок", default=0)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "Блок головної"
        verbose_name_plural = "Блоки головної"

    def __str__(self):
        return self.get_key_display()

    @property
    def title(self):
        return localized(self, "title")

    @property
    def text(self):
        return localized(self, "text")

    @property
    def cta(self):
        return localized(self, "cta")

    @property
    def text_mobile(self):
        return self.text

    @property
    def link_label(self):
        return localized(self, "link")

    @property
    def note(self):
        return localized(self, "note")

    @property
    def seo_title(self):
        return localized(self, "seo_title")

    @property
    def seo_description(self):
        return localized(self, "seo_description")

    @property
    def field_labels(self):
        parts = localized(self, "lines").splitlines()
        while len(parts) < 8:
            parts.append("")
        return parts


class HomeCollection(models.Model):
    rich_text_fields = ("text_uk", "text_en", "story_uk", "story_en", "text_fr", "story_fr")
    block = models.ForeignKey(
        "content.HomeBlock",
        related_name="collection_cards",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Блок",
    )
    slug = models.SlugField(
        "Слаг",
        max_length=120,
        unique=True,
        null=True,
        blank=True,
        help_text="URL: /kolektsiia/<slug>/",
    )
    label_uk = models.CharField("Підпис", max_length=120, blank=True)
    label_en = models.CharField("Підпис (EN)", max_length=120, blank=True)
    label_fr = models.CharField("Підпис (FR)", max_length=120, blank=True)
    title_uk = models.CharField("Назва", max_length=160)
    title_en = models.CharField("Назва (EN)", max_length=160, blank=True)
    title_fr = models.CharField("Назва (FR)", max_length=160, blank=True)
    text_uk = models.TextField("Текст", blank=True)
    text_en = models.TextField("Текст (EN)", blank=True)
    text_fr = models.TextField("Текст (FR)", blank=True)
    story_uk = models.TextField("Історія", blank=True)
    story_en = models.TextField("Історія (EN)", blank=True)
    story_fr = models.TextField("Історія (FR)", blank=True)
    box_items_uk = models.TextField(
        "У боксі",
        blank=True,
        help_text="Один пункт у рядку.",
    )
    box_items_en = models.TextField(
        "У боксі (EN)",
        blank=True,
        help_text="Один пункт у рядку.",
    )
    box_items_fr = models.TextField(
        "У боксі (FR)",
        blank=True,
        help_text="Один пункт у рядку.",
    )
    image_large = models.ImageField(
        "Велике фото",
        upload_to="home/collections/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
    )
    image_small = models.ImageField(
        "Мале фото",
        upload_to="home/collections/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
    )
    alt_large_uk = models.CharField("Alt великого фото", max_length=200, blank=True)
    alt_large_en = models.CharField("Alt великого фото (EN)", max_length=200, blank=True)
    alt_large_fr = models.CharField("Alt великого фото (FR)", max_length=200, blank=True)
    alt_small_uk = models.CharField("Alt малого фото", max_length=200, blank=True)
    alt_small_en = models.CharField("Alt малого фото (EN)", max_length=200, blank=True)
    alt_small_fr = models.CharField("Alt малого фото (FR)", max_length=200, blank=True)
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="home_collections",
        verbose_name="Категорія",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="home_collections_as_main",
        verbose_name="Товар боксу",
    )
    addons = models.ManyToManyField(
        "catalog.Product",
        blank=True,
        related_name="home_collections_as_addon",
        verbose_name="Доповнити сет",
    )
    seo_title_uk = models.CharField("SEO-заголовок", max_length=200, blank=True)
    seo_title_en = models.CharField("SEO-заголовок (EN)", max_length=200, blank=True)
    seo_title_fr = models.CharField("SEO-заголовок (FR)", max_length=200, blank=True)
    seo_description_uk = models.CharField("SEO-опис", max_length=300, blank=True)
    seo_description_en = models.CharField("SEO-опис (EN)", max_length=300, blank=True)
    seo_description_fr = models.CharField("SEO-опис (FR)", max_length=300, blank=True)
    is_active = models.BooleanField("Показувати на сайті", default=True)
    sort = models.PositiveIntegerField("Порядок", default=0)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "Колекція"
        verbose_name_plural = "Колекції"

    def __str__(self):
        return self.title_uk

    @property
    def label(self):
        return localized(self, "label")

    @property
    def title(self):
        return localized(self, "title")

    @property
    def text(self):
        return localized(self, "text")

    @property
    def story(self):
        return localized(self, "story")

    @property
    def box_items(self):
        raw = localized(self, "box_items")
        return [line.strip() for line in (raw or "").splitlines() if line.strip()]

    @property
    def alt_large(self):
        return localized(self, "alt_large")

    @property
    def alt_small(self):
        return localized(self, "alt_small")

    @property
    def seo_title(self):
        from src.core.seo import collection_meta_title

        return collection_meta_title(self)

    @property
    def seo_description(self):
        from src.core.seo import collection_meta_description

        return collection_meta_description(self)

    def gallery_photos(self):
        photos = []
        if self.image_large:
            photos.append({"url": self.image_large.url, "alt": self.alt_large})
        if self.image_small:
            photos.append({"url": self.image_small.url, "alt": self.alt_small})
        rows = self.gallery_images.all()
        cached = getattr(self, "_prefetched_objects_cache", {})
        if "gallery_images" in cached:
            rows = cached["gallery_images"]
        for row in rows:
            if row.image:
                photos.append({"url": row.image.url, "alt": row.alt})
        return photos

    def get_absolute_url(self):
        from django.urls import reverse

        if self.slug:
            return reverse("collection", kwargs={"slug": self.slug})
        return reverse("catalog")


class HomeCollectionImage(models.Model):
    collection = models.ForeignKey(
        HomeCollection,
        related_name="gallery_images",
        on_delete=models.CASCADE,
        verbose_name="Колекція",
    )
    image = models.ImageField(
        "Фото",
        upload_to="home/collections/gallery/",
        validators=[IMAGE_VALIDATOR],
    )
    alt_uk = models.CharField("Alt-текст", max_length=200, blank=True)
    alt_en = models.CharField("Alt-текст (EN)", max_length=200, blank=True)
    alt_fr = models.CharField("Alt-текст (FR)", max_length=200, blank=True)
    sort = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "Фото колекції"
        verbose_name_plural = "Фото колекції"

    def __str__(self):
        return f"{self.collection_id}:{self.pk}"

    @property
    def alt(self):
        return localized(self, "alt")


class Advantage(MediaChoice):
    rich_text_fields = ("text_uk", "text_en", "text_fr")
    block = models.ForeignKey(
        "content.HomeBlock",
        related_name="advantage_cards",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Блок",
    )
    title_uk = models.CharField("Заголовок", max_length=160)
    title_en = models.CharField("Заголовок (EN)", max_length=160, blank=True)
    title_fr = models.CharField("Заголовок (FR)", max_length=160, blank=True)
    text_uk = models.TextField("Текст", blank=True)
    text_en = models.TextField("Текст (EN)", blank=True)
    text_fr = models.TextField("Текст (FR)", blank=True)
    image = models.ImageField(
        "Зображення",
        upload_to="home/advantages/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
    )
    video = models.FileField(
        "Відео",
        upload_to="home/advantages/video/",
        blank=True,
        validators=[VIDEO_VALIDATOR],
        help_text="MP4 або WEBM.",
    )
    sort = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "Перевага"
        verbose_name_plural = "Переваги"

    def __str__(self):
        return self.title_uk

    @property
    def title(self):
        return localized(self, "title")

    @property
    def text(self):
        return localized(self, "text")


class AboutPage(MediaChoice, SingletonModel):
    cache_key = "about_page_v3"
    rich_text_fields = (
        "body_uk",
        "body_en",
        "intro_text_uk",
        "intro_text_en",
        "gestia_text_uk",
        "gestia_text_en",
        "together_text_uk",
        "together_text_en",
        "closing_text_uk",
        "closing_text_en",
        "body_fr",
        "intro_text_fr",
        "gestia_text_fr",
        "together_text_fr",
        "closing_text_fr",
    )
    title_uk = models.CharField("Заголовок", max_length=200, default="Про нас")
    title_en = models.CharField("Заголовок (EN)", max_length=200, blank=True)
    title_fr = models.CharField("Заголовок (FR)", max_length=200, blank=True)
    lead_uk = models.CharField("Підзаголовок", max_length=40, blank=True)
    lead_en = models.CharField("Підзаголовок (EN)", max_length=40, blank=True)
    lead_fr = models.CharField("Підзаголовок (FR)", max_length=40, blank=True)
    crumb_uk = models.CharField("Посилання «Головна»", max_length=16, blank=True)
    crumb_en = models.CharField("Посилання «Головна» (EN)", max_length=16, blank=True)
    crumb_fr = models.CharField("Посилання «Головна» (FR)", max_length=16, blank=True)
    story_label_uk = models.CharField("Назва історії", max_length=32, blank=True)
    story_label_en = models.CharField("Назва історії (EN)", max_length=32, blank=True)
    story_label_fr = models.CharField("Назва історії (FR)", max_length=32, blank=True)
    body_uk = models.TextField("Текст", blank=True)
    body_en = models.TextField("Текст (EN)", blank=True)
    body_fr = models.TextField("Текст (FR)", blank=True)
    intro_text_uk = models.TextField("Текст інтро", blank=True)
    intro_text_en = models.TextField("Текст інтро (EN)", blank=True)
    intro_text_fr = models.TextField("Текст інтро (FR)", blank=True)
    intro_photo_left = WebPImageField(
        "Фото інтро (ліве)",
        upload_to="about/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Десктоп. Близько 3:4. JPG або PNG.",
    )
    intro_photo_left_alt_uk = models.CharField("Alt лівого фото", max_length=200, blank=True)
    intro_photo_left_alt_en = models.CharField("Alt лівого фото (EN)", max_length=200, blank=True)
    intro_photo_left_alt_fr = models.CharField("Alt лівого фото (FR)", max_length=200, blank=True)
    intro_photo_main = WebPImageField(
        "Фото інтро (головне)",
        upload_to="about/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Близько 4:5. JPG або PNG.",
    )
    intro_photo_main_alt_uk = models.CharField("Alt головного фото", max_length=200, blank=True)
    intro_photo_main_alt_en = models.CharField("Alt головного фото (EN)", max_length=200, blank=True)
    intro_photo_main_alt_fr = models.CharField("Alt головного фото (FR)", max_length=200, blank=True)
    gestia_quote_uk = models.TextField("Цитата Гестії", blank=True)
    gestia_quote_en = models.TextField("Цитата Гестії (EN)", blank=True)
    gestia_quote_fr = models.TextField("Цитата Гестії (FR)", blank=True)
    gestia_plate = WebPImageField(
        "Фото тарілки",
        upload_to="about/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Близько 4:3. JPG або PNG.",
    )
    gestia_plate_alt_uk = models.CharField("Alt тарілки", max_length=200, blank=True)
    gestia_plate_alt_en = models.CharField("Alt тарілки (EN)", max_length=200, blank=True)
    gestia_plate_alt_fr = models.CharField("Alt тарілки (FR)", max_length=200, blank=True)
    gestia_photo = WebPImageField(
        "Фото столу Гестії",
        upload_to="about/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Фон правої колонки. JPG або PNG.",
    )
    gestia_photo_alt_uk = models.CharField("Alt столу Гестії", max_length=200, blank=True)
    gestia_photo_alt_en = models.CharField("Alt столу Гестії (EN)", max_length=200, blank=True)
    gestia_photo_alt_fr = models.CharField("Alt столу Гестії (FR)", max_length=200, blank=True)
    gestia_text_uk = models.TextField("Текст Гестії", blank=True)
    gestia_text_en = models.TextField("Текст Гестії (EN)", blank=True)
    gestia_text_fr = models.TextField("Текст Гестії (FR)", blank=True)
    approach_text_uk = models.TextField("Текст підходу", blank=True)
    approach_text_en = models.TextField("Текст підходу (EN)", blank=True)
    approach_text_fr = models.TextField("Текст підходу (FR)", blank=True)
    together_photo = WebPImageField(
        "Фото «Разом»",
        upload_to="about/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Близько 4:5. JPG або PNG.",
    )
    together_photo_alt_uk = models.CharField("Alt «Разом»", max_length=200, blank=True)
    together_photo_alt_en = models.CharField("Alt «Разом» (EN)", max_length=200, blank=True)
    together_photo_alt_fr = models.CharField("Alt «Разом» (FR)", max_length=200, blank=True)
    together_text_uk = models.TextField("Текст «Разом»", blank=True)
    together_text_en = models.TextField("Текст «Разом» (EN)", blank=True)
    together_text_fr = models.TextField("Текст «Разом» (FR)", blank=True)
    closing_text_uk = models.TextField("Фінальний текст", blank=True)
    closing_text_en = models.TextField("Фінальний текст (EN)", blank=True)
    closing_text_fr = models.TextField("Фінальний текст (FR)", blank=True)
    cta_uk = models.CharField("Кнопка каталогу", max_length=40, blank=True)
    cta_en = models.CharField("Кнопка каталогу (EN)", max_length=40, blank=True)
    cta_fr = models.CharField("Кнопка каталогу (FR)", max_length=40, blank=True)
    image = models.ImageField(
        "Фото",
        upload_to="about/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Одна картинка для десктопу і мобільного, у макеті 1442×871. JPG або PNG.",
    )
    image_mobile = WebPImageField(
        "Фото (застаріле)",
        upload_to="about/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Не використовується. Залишено для сумісності.",
    )
    video = models.FileField(
        "Відео",
        upload_to="about/video/",
        blank=True,
        validators=[VIDEO_VALIDATOR],
    )
    seo_title_uk = models.CharField("SEO-заголовок", max_length=200, blank=True)
    seo_title_en = models.CharField("SEO-заголовок (EN)", max_length=200, blank=True)
    seo_title_fr = models.CharField("SEO-заголовок (FR)", max_length=200, blank=True)
    seo_description_uk = models.CharField("SEO-опис", max_length=300, blank=True)
    seo_description_en = models.CharField("SEO-опис (EN)", max_length=300, blank=True)
    seo_description_fr = models.CharField("SEO-опис (FR)", max_length=300, blank=True)
    reviews_title_uk = models.CharField("Заголовок відгуків", max_length=64, blank=True)
    reviews_title_en = models.CharField("Заголовок відгуків (EN)", max_length=64, blank=True)
    reviews_title_fr = models.CharField("Заголовок відгуків (FR)", max_length=64, blank=True)
    popular_title_uk = models.CharField("Заголовок популярних", max_length=64, blank=True)
    popular_title_en = models.CharField("Заголовок популярних (EN)", max_length=64, blank=True)
    popular_title_fr = models.CharField("Заголовок популярних (FR)", max_length=64, blank=True)
    popular_cta_uk = models.CharField("Кнопка популярних", max_length=40, blank=True)
    popular_cta_en = models.CharField("Кнопка популярних (EN)", max_length=40, blank=True)
    popular_cta_fr = models.CharField("Кнопка популярних (FR)", max_length=40, blank=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "Сторінка «Про нас»"
        verbose_name_plural = "Сторінка «Про нас»"

    def __str__(self):
        return "Про нас"

    @property
    def title(self):
        return localized(self, "title")

    @property
    def body(self):
        return localized(self, "body")

    @property
    def intro_text(self):
        return localized(self, "intro_text")

    @property
    def intro_photo_left_alt(self):
        return localized(self, "intro_photo_left_alt")

    @property
    def intro_photo_main_alt(self):
        return localized(self, "intro_photo_main_alt")

    @property
    def gestia_quote(self):
        return localized(self, "gestia_quote")

    @property
    def gestia_plate_alt(self):
        return localized(self, "gestia_plate_alt")

    @property
    def gestia_photo_alt(self):
        return localized(self, "gestia_photo_alt")

    @property
    def gestia_text(self):
        return localized(self, "gestia_text")

    @property
    def approach_text(self):
        return localized(self, "approach_text")

    @property
    def together_photo_alt(self):
        return localized(self, "together_photo_alt")

    @property
    def together_text(self):
        return localized(self, "together_text")

    @property
    def closing_text(self):
        return localized(self, "closing_text")

    @property
    def cta(self):
        return localized(self, "cta")

    @property
    def seo_title(self):
        return localized(self, "seo_title") or self.title

    @property
    def seo_description(self):
        return localized(self, "seo_description")

    @property
    def reviews_title(self):
        return localized(self, "reviews_title")

    @property
    def popular_title(self):
        return localized(self, "popular_title")

    @property
    def popular_cta(self):
        return localized(self, "popular_cta")


class Review(models.Model):
    class Placement(models.TextChoices):
        HOME = "home", "Головна"
        ABOUT = "about", "Про нас"

    class Rating(models.TextChoices):
        GOLD_FOUR = "gold4", "4 золоті"
        BLACK_FIVE = "black5", "5 чорних"

    rich_text_fields = ("text_uk", "text_en", "text_fr")
    placement = models.CharField(
        "Сторінка",
        max_length=16,
        choices=Placement.choices,
        default=Placement.HOME,
        db_index=True,
    )
    author_uk = models.CharField("Ім'я", max_length=80)
    author_en = models.CharField("Ім'я (EN)", max_length=80, blank=True)
    author_fr = models.CharField("Ім'я (FR)", max_length=80, blank=True)
    text_uk = models.TextField("Текст")
    text_en = models.TextField("Текст (EN)", blank=True)
    text_fr = models.TextField("Текст (FR)", blank=True)
    rating_kind = models.CharField(
        "Рейтинг",
        max_length=16,
        choices=Rating.choices,
        default=Rating.GOLD_FOUR,
    )
    sort = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"

    def __str__(self):
        return self.author_uk

    @property
    def author(self):
        return localized(self, "author")

    @property
    def text(self):
        return localized(self, "text")


class FooterLink(models.Model):
    class Column(models.TextChoices):
        CATEGORY = "category", "Категорії"
        INFO = "info", "Інформація"
        LEGAL = "legal", "Документи"

    column = models.CharField("Колонка", max_length=16, choices=Column.choices)
    label_uk = models.CharField("Підпис", max_length=200)
    label_en = models.CharField("Підпис (EN)", max_length=200, blank=True)
    label_fr = models.CharField("Підпис (FR)", max_length=200, blank=True)
    url_name = models.CharField("Ім'я URL", max_length=40, blank=True)
    url_arg = models.CharField("Аргумент URL", max_length=80, blank=True)
    underlined = models.BooleanField("З лінією", default=False)
    sort = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["column", "sort", "id"]
        verbose_name = "Посилання підвалу"
        verbose_name_plural = "Посилання підвалу"

    def __str__(self):
        return self.label_uk

    @property
    def label(self):
        return localized(self, "label")

    def href(self):
        from django.urls import NoReverseMatch, reverse

        if self.url_name == "category" and self.url_arg:
            return reverse("category", kwargs={"slug": self.url_arg})
        if self.url_name == "anchor":
            return reverse("home") + "#" + (self.url_arg or "callback")
        if self.url_name:
            try:
                return reverse(self.url_name)
            except NoReverseMatch:
                return ""
        return self.url_arg or ""


class ContactForms(SingletonModel):
    """Тексти форм, які не є окремим візуальним блоком головної."""

    cache_key = "contact_forms_v1"

    waitlist_title_uk = models.CharField("Заголовок вікна", max_length=56, blank=True)
    waitlist_title_en = models.CharField("Заголовок вікна (EN)", max_length=56, blank=True)
    waitlist_title_fr = models.CharField("Заголовок вікна (FR)", max_length=56, blank=True)
    waitlist_p1_uk = models.CharField("Перший абзац", max_length=160, blank=True)
    waitlist_p1_en = models.CharField("Перший абзац (EN)", max_length=160, blank=True)
    waitlist_p1_fr = models.CharField("Перший абзац (FR)", max_length=160, blank=True)
    waitlist_p2_uk = models.CharField("Другий абзац", max_length=120, blank=True)
    waitlist_p2_en = models.CharField("Другий абзац (EN)", max_length=120, blank=True)
    waitlist_p2_fr = models.CharField("Другий абзац (FR)", max_length=120, blank=True)
    waitlist_p3_uk = models.CharField("Третій абзац", max_length=140, blank=True)
    waitlist_p3_en = models.CharField("Третій абзац (EN)", max_length=140, blank=True)
    waitlist_p3_fr = models.CharField("Третій абзац (FR)", max_length=140, blank=True)
    waitlist_email_uk = models.CharField("Підказка email", max_length=20, blank=True)
    waitlist_email_en = models.CharField("Підказка email (EN)", max_length=20, blank=True)
    waitlist_email_fr = models.CharField("Підказка email (FR)", max_length=20, blank=True)
    waitlist_consent_uk = models.CharField("Текст згоди", max_length=72, blank=True)
    waitlist_consent_en = models.CharField("Текст згоди (EN)", max_length=72, blank=True)
    waitlist_consent_fr = models.CharField("Текст згоди (FR)", max_length=72, blank=True)
    waitlist_privacy_uk = models.CharField("Посилання на політику", max_length=36, blank=True)
    waitlist_privacy_en = models.CharField("Посилання на політику (EN)", max_length=36, blank=True)
    waitlist_privacy_fr = models.CharField("Посилання на політику (FR)", max_length=36, blank=True)
    waitlist_button_uk = models.CharField("Кнопка", max_length=24, blank=True)
    waitlist_button_en = models.CharField("Кнопка (EN)", max_length=24, blank=True)
    waitlist_button_fr = models.CharField("Кнопка (FR)", max_length=24, blank=True)
    waitlist_thanks_title_uk = models.CharField("Заголовок після надсилання", max_length=16, blank=True)
    waitlist_thanks_title_en = models.CharField("Заголовок після надсилання (EN)", max_length=16, blank=True)
    waitlist_thanks_title_fr = models.CharField("Заголовок після надсилання (FR)", max_length=16, blank=True)
    waitlist_thanks_text_uk = models.CharField("Текст після надсилання", max_length=90, blank=True)
    waitlist_thanks_text_en = models.CharField("Текст після надсилання (EN)", max_length=90, blank=True)
    waitlist_thanks_text_fr = models.CharField("Текст після надсилання (FR)", max_length=90, blank=True)

    sheet_consent_uk = models.CharField("Текст згоди у вікні", max_length=56, blank=True)
    sheet_consent_en = models.CharField("Текст згоди у вікні (EN)", max_length=56, blank=True)
    sheet_consent_fr = models.CharField("Текст згоди у вікні (FR)", max_length=56, blank=True)
    sheet_close_uk = models.CharField("Кнопка «Закрити»", max_length=16, blank=True)
    sheet_close_en = models.CharField("Кнопка «Закрити» (EN)", max_length=16, blank=True)
    sheet_close_fr = models.CharField("Кнопка «Закрити» (FR)", max_length=16, blank=True)
    contact_button_uk = models.CharField("Кнопка контакту", max_length=16, blank=True)
    contact_button_en = models.CharField("Кнопка контакту (EN)", max_length=16, blank=True)
    contact_button_fr = models.CharField("Кнопка контакту (FR)", max_length=16, blank=True)
    callback_button_uk = models.CharField("Кнопка заявки", max_length=24, blank=True)
    callback_button_en = models.CharField("Кнопка заявки (EN)", max_length=24, blank=True)
    callback_button_fr = models.CharField("Кнопка заявки (FR)", max_length=24, blank=True)
    buy_button_uk = models.CharField("Кнопка швидкого замовлення", max_length=24, blank=True)
    buy_button_en = models.CharField("Кнопка швидкого замовлення (EN)", max_length=24, blank=True)
    buy_button_fr = models.CharField("Кнопка швидкого замовлення (FR)", max_length=24, blank=True)

    label_name_uk = models.CharField("Підпис імені", max_length=16, blank=True)
    label_name_en = models.CharField("Підпис імені (EN)", max_length=16, blank=True)
    label_name_fr = models.CharField("Підпис імені (FR)", max_length=16, blank=True)
    label_phone_uk = models.CharField("Підпис телефону", max_length=16, blank=True)
    label_phone_en = models.CharField("Підпис телефону (EN)", max_length=16, blank=True)
    label_phone_fr = models.CharField("Підпис телефону (FR)", max_length=16, blank=True)
    label_message_uk = models.CharField("Підпис повідомлення", max_length=24, blank=True)
    label_message_en = models.CharField("Підпис повідомлення (EN)", max_length=24, blank=True)
    label_message_fr = models.CharField("Підпис повідомлення (FR)", max_length=24, blank=True)
    label_address_uk = models.CharField("Підпис адреси", max_length=24, blank=True)
    label_address_en = models.CharField("Підпис адреси (EN)", max_length=24, blank=True)
    label_address_fr = models.CharField("Підпис адреси (FR)", max_length=24, blank=True)
    label_email_uk = models.CharField("Підпис email", max_length=16, blank=True)
    label_email_en = models.CharField("Підпис email (EN)", max_length=16, blank=True)
    label_email_fr = models.CharField("Підпис email (FR)", max_length=16, blank=True)

    class Meta:
        verbose_name = "CTA та контактні форми"
        verbose_name_plural = "CTA та контактні форми"

    def __str__(self):
        return "CTA та контактні форми"


from src.content import models_about as _about_models  # noqa: E402,F401
from src.content import models_discount as _discount_models  # noqa: E402,F401
from src.content import models_faq as _faq_models  # noqa: E402,F401
from src.content import models_home_slots as _home_slots  # noqa: E402,F401
from src.content import models_legal as _legal_models  # noqa: E402,F401
from src.content import models_menu as _menu_models  # noqa: E402,F401
from src.content import models_styles as _style_models  # noqa: E402,F401
from src.content import models_contacts as _contacts_models  # noqa: E402,F401
from src.content import models_thankyou as _thankyou_models  # noqa: E402,F401
from src.content import models_ui as _ui_models  # noqa: E402,F401
from src.content import proxies as _home_proxies  # noqa: E402,F401
