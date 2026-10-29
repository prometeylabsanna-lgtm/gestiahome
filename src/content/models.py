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
    email = models.EmailField("Email", blank=True)
    address_uk = models.CharField("Адреса", max_length=255, blank=True)
    address_en = models.CharField("Адреса (EN)", max_length=255, blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    pinterest_url = models.URLField("Pinterest", blank=True)
    telegram_url = models.URLField("Telegram", blank=True, help_text="Посилання t.me/… у соцряді.")
    developer_note_uk = models.CharField("Підпис розробника", max_length=160, blank=True)
    developer_note_en = models.CharField("Підпис розробника (EN)", max_length=160, blank=True)
    logo = models.ImageField(
        "Логотип",
        upload_to="site/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Шапка близько 113×43, підвал 191×73. JPG або PNG.",
    )
    nav_about_uk = models.CharField("Пункт «Про нас»", max_length=16, blank=True)
    nav_about_en = models.CharField("Пункт «Про нас» (EN)", max_length=16, blank=True)
    nav_all_uk = models.CharField("Пункт «Усі товари»", max_length=20, blank=True)
    nav_all_en = models.CharField("Пункт «Усі товари» (EN)", max_length=20, blank=True)
    menu_title_uk = models.CharField(
        "Заголовок у меню",
        max_length=16,
        blank=True,
        help_text="У мобільному меню. Кнопка в шапці лишається своєю.",
    )
    menu_title_en = models.CharField("Заголовок у меню (EN)", max_length=16, blank=True)
    credit_uk = models.CharField("Текст перед PrometeyLabs", max_length=32, blank=True)
    credit_en = models.CharField("Текст перед PrometeyLabs (EN)", max_length=32, blank=True)
    en_enabled = models.BooleanField("Англійська увімкнена", default=True)
    telegram_notify_orders = models.BooleanField("Telegram: замовлення", default=True)
    telegram_notify_leads = models.BooleanField("Telegram: заявки", default=True)
    color_ink = models.CharField("Колір тексту", max_length=7, default="#241c16")
    color_paper = models.CharField("Колір тла", max_length=7, default="#f3eee6")
    color_accent = models.CharField("Акцент", max_length=7, default="#8d3b2a")
    footer_note_uk = models.CharField("Підпис у підвалі", max_length=255, blank=True)
    footer_note_en = models.CharField("Підпис у підвалі (EN)", max_length=255, blank=True)

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

    rich_text_fields = ("text_uk", "text_en")
    key = models.CharField("Ключ", max_length=32, choices=Key.choices, unique=True)
    title_uk = models.CharField("Заголовок", max_length=200, blank=True)
    title_en = models.CharField("Заголовок (EN)", max_length=200, blank=True)
    text_uk = models.TextField("Текст", blank=True)
    text_en = models.TextField("Текст (EN)", blank=True)
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
    seo_title_uk = models.CharField("SEO title", max_length=200, blank=True)
    seo_title_en = models.CharField("SEO title (EN)", max_length=200, blank=True)
    seo_description_uk = models.CharField("SEO description", max_length=300, blank=True)
    seo_description_en = models.CharField("SEO description (EN)", max_length=300, blank=True)
    cta_uk = models.CharField("Текст кнопки", max_length=200, blank=True)
    cta_en = models.CharField("Текст кнопки (EN)", max_length=200, blank=True)
    link_uk = models.CharField("Другий підпис", max_length=160, blank=True)
    link_en = models.CharField("Другий підпис (EN)", max_length=160, blank=True)
    note_uk = models.TextField("Примітка", blank=True)
    note_en = models.TextField("Примітка (EN)", blank=True)
    lines_uk = models.TextField("Рядки підписів", blank=True)
    lines_en = models.TextField("Рядки підписів (EN)", blank=True)
    sort = models.PositiveIntegerField("Порядок", default=0)

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
        while len(parts) < 3:
            parts.append("")
        return parts[:3]


class Advantage(models.Model):
    rich_text_fields = ("text_uk", "text_en")
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
    text_uk = models.TextField("Текст", blank=True)
    text_en = models.TextField("Текст (EN)", blank=True)
    image = models.ImageField(
        "Зображення",
        upload_to="home/advantages/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
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
    cache_key = "about_page_v2"
    rich_text_fields = ("body_uk", "body_en")
    title_uk = models.CharField("Заголовок", max_length=200, default="Про нас")
    title_en = models.CharField("Заголовок (EN)", max_length=200, blank=True)
    lead_uk = models.CharField("Підзаголовок", max_length=40, blank=True)
    lead_en = models.CharField("Підзаголовок (EN)", max_length=40, blank=True)
    crumb_uk = models.CharField("Посилання «Головна»", max_length=16, blank=True)
    crumb_en = models.CharField("Посилання «Головна» (EN)", max_length=16, blank=True)
    story_label_uk = models.CharField("Назва історії", max_length=32, blank=True)
    story_label_en = models.CharField("Назва історії (EN)", max_length=32, blank=True)
    body_uk = models.TextField("Текст", blank=True)
    body_en = models.TextField("Текст (EN)", blank=True)
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
    seo_title_uk = models.CharField("SEO title", max_length=200, blank=True)
    seo_title_en = models.CharField("SEO title (EN)", max_length=200, blank=True)
    seo_description_uk = models.CharField("SEO description", max_length=300, blank=True)
    seo_description_en = models.CharField("SEO description (EN)", max_length=300, blank=True)
    reviews_title_uk = models.CharField("Заголовок відгуків", max_length=64, blank=True)
    reviews_title_en = models.CharField("Заголовок відгуків (EN)", max_length=64, blank=True)
    popular_title_uk = models.CharField("Заголовок популярних", max_length=64, blank=True)
    popular_title_en = models.CharField("Заголовок популярних (EN)", max_length=64, blank=True)
    popular_cta_uk = models.CharField("Кнопка популярних", max_length=40, blank=True)
    popular_cta_en = models.CharField("Кнопка популярних (EN)", max_length=40, blank=True)

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

    rich_text_fields = ("text_uk", "text_en")
    placement = models.CharField(
        "Сторінка",
        max_length=16,
        choices=Placement.choices,
        default=Placement.HOME,
        db_index=True,
    )
    author_uk = models.CharField("Ім'я", max_length=80)
    author_en = models.CharField("Ім'я (EN)", max_length=80, blank=True)
    text_uk = models.TextField("Текст")
    text_en = models.TextField("Текст (EN)", blank=True)
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
    waitlist_p1_uk = models.CharField("Перший абзац", max_length=160, blank=True)
    waitlist_p1_en = models.CharField("Перший абзац (EN)", max_length=160, blank=True)
    waitlist_p2_uk = models.CharField("Другий абзац", max_length=120, blank=True)
    waitlist_p2_en = models.CharField("Другий абзац (EN)", max_length=120, blank=True)
    waitlist_p3_uk = models.CharField("Третій абзац", max_length=140, blank=True)
    waitlist_p3_en = models.CharField("Третій абзац (EN)", max_length=140, blank=True)
    waitlist_email_uk = models.CharField("Підказка email", max_length=20, blank=True)
    waitlist_email_en = models.CharField("Підказка email (EN)", max_length=20, blank=True)
    waitlist_consent_uk = models.CharField("Текст згоди", max_length=72, blank=True)
    waitlist_consent_en = models.CharField("Текст згоди (EN)", max_length=72, blank=True)
    waitlist_privacy_uk = models.CharField("Посилання на політику", max_length=36, blank=True)
    waitlist_privacy_en = models.CharField("Посилання на політику (EN)", max_length=36, blank=True)
    waitlist_button_uk = models.CharField("Кнопка", max_length=24, blank=True)
    waitlist_button_en = models.CharField("Кнопка (EN)", max_length=24, blank=True)
    waitlist_thanks_title_uk = models.CharField("Заголовок після надсилання", max_length=16, blank=True)
    waitlist_thanks_title_en = models.CharField("Заголовок після надсилання (EN)", max_length=16, blank=True)
    waitlist_thanks_text_uk = models.CharField("Текст після надсилання", max_length=90, blank=True)
    waitlist_thanks_text_en = models.CharField("Текст після надсилання (EN)", max_length=90, blank=True)

    sheet_consent_uk = models.CharField("Текст згоди у вікні", max_length=56, blank=True)
    sheet_consent_en = models.CharField("Текст згоди у вікні (EN)", max_length=56, blank=True)
    sheet_close_uk = models.CharField("Кнопка «Закрити»", max_length=16, blank=True)
    sheet_close_en = models.CharField("Кнопка «Закрити» (EN)", max_length=16, blank=True)
    contact_button_uk = models.CharField("Кнопка контакту", max_length=16, blank=True)
    contact_button_en = models.CharField("Кнопка контакту (EN)", max_length=16, blank=True)
    callback_button_uk = models.CharField("Кнопка заявки", max_length=24, blank=True)
    callback_button_en = models.CharField("Кнопка заявки (EN)", max_length=24, blank=True)
    buy_button_uk = models.CharField("Кнопка швидкого замовлення", max_length=24, blank=True)
    buy_button_en = models.CharField("Кнопка швидкого замовлення (EN)", max_length=24, blank=True)

    label_name_uk = models.CharField("Підпис імені", max_length=16, blank=True)
    label_name_en = models.CharField("Підпис імені (EN)", max_length=16, blank=True)
    label_phone_uk = models.CharField("Підпис телефону", max_length=16, blank=True)
    label_phone_en = models.CharField("Підпис телефону (EN)", max_length=16, blank=True)
    label_message_uk = models.CharField("Підпис повідомлення", max_length=24, blank=True)
    label_message_en = models.CharField("Підпис повідомлення (EN)", max_length=24, blank=True)
    label_address_uk = models.CharField("Підпис адреси", max_length=24, blank=True)
    label_address_en = models.CharField("Підпис адреси (EN)", max_length=24, blank=True)
    label_email_uk = models.CharField("Підпис email", max_length=16, blank=True)
    label_email_en = models.CharField("Підпис email (EN)", max_length=16, blank=True)

    class Meta:
        verbose_name = "CTA та контактні форми"
        verbose_name_plural = "CTA та контактні форми"

    def __str__(self):
        return "CTA та контактні форми"


from src.content import models_about as _about_models  # noqa: E402,F401
from src.content import models_discount as _discount_models  # noqa: E402,F401
from src.content import models_home_slots as _home_slots  # noqa: E402,F401
from src.content import models_legal as _legal_models  # noqa: E402,F401
from src.content import models_styles as _style_models  # noqa: E402,F401
from src.content import proxies as _home_proxies  # noqa: E402,F401
