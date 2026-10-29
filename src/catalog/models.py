from decimal import Decimal

from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import get_language, gettext_lazy as _

from src.core.models import TimeStampedModel
from src.core.seo import category_meta_description, product_meta_description
from src.core.slug import ensure_new_slug
from src.core.utils import localized

IMAGE_VALIDATOR = FileExtensionValidator(["jpg", "jpeg", "png", "webp"])


class Category(TimeStampedModel):
    parent = models.ForeignKey(
        "self",
        verbose_name="Батьківська категорія",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    slug = models.SlugField("Слаг", max_length=80, unique=True)
    name_uk = models.CharField("Назва", max_length=160)
    name_en = models.CharField("Назва (EN)", max_length=160, blank=True)
    image = models.ImageField(
        "Зображення",
        upload_to="categories/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
    )
    is_active = models.BooleanField("Активна", default=True)
    sort = models.PositiveIntegerField("Порядок", default=0)
    home_sort = models.PositiveIntegerField("Порядок на головній", null=True, blank=True)
    menu_featured = models.BooleanField("Акцент у меню", default=False)
    filter_sort = models.PositiveSmallIntegerField("Порядок у фільтрі", null=True, blank=True)
    filter_name_uk = models.CharField("Назва у фільтрі", max_length=160, blank=True)
    seo_title_uk = models.CharField(
        "SEO title",
        max_length=200,
        blank=True,
        help_text="Цільова довжина: 50–60 символів.",
    )
    seo_title_en = models.CharField(
        "SEO title (EN)",
        max_length=200,
        blank=True,
        help_text="Цільова довжина: 50–60 символів.",
    )
    seo_description_uk = models.CharField(
        "SEO description",
        max_length=300,
        blank=True,
        help_text="Цільова довжина: 140–160 символів.",
    )
    seo_description_en = models.CharField(
        "SEO description (EN)",
        max_length=300,
        blank=True,
        help_text="Цільова довжина: 140–160 символів.",
    )

    class Meta:
        ordering = ["sort", "name_uk"]
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        indexes = [models.Index(fields=["is_active", "sort"])]

    def __str__(self):
        return self.name_uk

    def save(self, *args, **kwargs):
        slug_set = ensure_new_slug(self)
        if slug_set and kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"slug"}
        super().save(*args, **kwargs)

    @property
    def name(self):
        return localized(self, "name")

    def get_absolute_url(self):
        return reverse("category", kwargs={"slug": self.slug})

    @property
    def seo_title(self):
        return localized(self, "seo_title").strip() or f"{self.name} — Gestia"

    @property
    def seo_description(self):
        return category_meta_description(self)

    @property
    def has_public_products(self):
        if self.products.filter(is_active=True).exists():
            return True
        return self.children.filter(is_active=True, products__is_active=True).exists()

    @property
    def filter_label(self):
        custom = (self.filter_name_uk or "").strip()
        if not custom:
            return self.name
        if custom == (self.name_uk or "").strip():
            lang = (get_language() or "uk").split("-")[0]
            if lang != "uk":
                return self.name
            return self.filter_name_uk
        return self.filter_name_uk

    def chain(self):
        nodes = []
        node = self
        seen = set()
        while node and node.pk not in seen:
            seen.add(node.pk)
            nodes.append(node)
            node = node.parent
        return list(reversed(nodes))


class ProductAttributeGroup(models.Model):
    class Slug(models.TextChoices):
        STYLE = "style", "Стиль"
        COLOR = "color", "Колір"

    slug = models.CharField("Слаг", max_length=32, choices=Slug.choices, unique=True)
    name_uk = models.CharField("Назва", max_length=80)
    name_en = models.CharField("Назва (EN)", max_length=80, blank=True)

    class Meta:
        verbose_name = "Група фільтра"
        verbose_name_plural = "Групи фільтрів"

    def __str__(self):
        return self.name_uk

    @property
    def name(self):
        return localized(self, "name")


class ProductAttribute(models.Model):
    group = models.ForeignKey(
        ProductAttributeGroup,
        verbose_name="Група",
        related_name="values",
        on_delete=models.CASCADE,
    )
    slug = models.SlugField("Слаг", max_length=80)
    name_uk = models.CharField("Назва", max_length=80)
    name_en = models.CharField("Назва (EN)", max_length=80, blank=True)
    is_filterable = models.BooleanField("У фільтрі", default=True)
    show_on_pdp = models.BooleanField("На картці", default=True)
    sort = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort", "name_uk"]
        verbose_name = "Значення фільтра"
        verbose_name_plural = "Значення фільтрів"
        constraints = [
            models.UniqueConstraint(fields=["group", "slug"], name="uniq_attr_group_slug")
        ]

    def __str__(self):
        return f"{self.group.name_uk}: {self.name_uk}"

    def save(self, *args, **kwargs):
        extra = {"group_id": self.group_id} if self.group_id else None
        slug_set = ensure_new_slug(self, extra_filter=extra)
        if slug_set and kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"slug"}
        super().save(*args, **kwargs)

    @property
    def name(self):
        return localized(self, "name")


class ProductSet(models.Model):
    slug = models.SlugField("Слаг", max_length=80, unique=True)
    name_uk = models.CharField("Назва", max_length=160)
    name_en = models.CharField("Назва (EN)", max_length=160, blank=True)

    class Meta:
        verbose_name = "Сет"
        verbose_name_plural = "Сети"

    def __str__(self):
        return self.name_uk

    def save(self, *args, **kwargs):
        slug_set = ensure_new_slug(self)
        if slug_set and kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"slug"}
        super().save(*args, **kwargs)

    @property
    def name(self):
        return localized(self, "name")


class Product(TimeStampedModel):
    class Stock(models.TextChoices):
        IN_STOCK = "in_stock", _("В наявності")
        ON_ORDER = "on_order", _("Під замовлення")
        OUT = "out", _("Немає в наявності")

    rich_text_fields = ("description_uk", "description_en")
    category = models.ForeignKey(
        Category,
        verbose_name="Категорія",
        related_name="products",
        on_delete=models.PROTECT,
    )
    product_set = models.ForeignKey(
        ProductSet,
        verbose_name="Сет",
        null=True,
        blank=True,
        related_name="products",
        on_delete=models.SET_NULL,
    )
    sku = models.CharField("Артикул", max_length=64, unique=True)
    slug = models.SlugField("Слаг", max_length=120, unique=True)
    name_uk = models.CharField("Назва", max_length=200)
    name_en = models.CharField("Назва (EN)", max_length=200, blank=True)
    description_uk = models.TextField("Опис", blank=True)
    description_en = models.TextField("Опис (EN)", blank=True)
    price_uah = models.DecimalField("Ціна, грн", max_digits=10, decimal_places=2)
    price_eur = models.DecimalField("Ціна, євро", max_digits=10, decimal_places=2)
    stock_status = models.CharField(
        "Наявність",
        max_length=16,
        choices=Stock.choices,
        default=Stock.IN_STOCK,
    )
    stock_qty = models.PositiveIntegerField("Залишок, шт", default=0)
    is_active = models.BooleanField("Активний", default=True)
    is_sale = models.BooleanField("Акція", default=False)
    is_popular = models.BooleanField("Популярний на головній", default=False)
    menu_name_uk = models.CharField("Назва в меню", max_length=200, blank=True)
    menu_name_en = models.CharField("Назва в меню (EN)", max_length=200, blank=True)
    price_weight = models.PositiveSmallIntegerField("Насиченість ціни на головній", default=400)
    card_crop = models.CharField(
        "Кадр картки",
        max_length=16,
        choices=[
            ("ukr", "107.6%"),
            ("cover", "cover"),
            ("shysh", "114.41%"),
            ("hnizdo", "114.99%"),
            ("wide", "115.8%"),
        ],
        default="cover",
    )
    name_width = models.PositiveSmallIntegerField("Ширина назви на картці", default=127)
    card_image = models.ImageField(
        "Фото картки",
        upload_to="products/cards/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
    )
    sort = models.PositiveIntegerField("Порядок", default=0)
    filter_attrs = models.ManyToManyField(
        ProductAttribute,
        verbose_name="Стиль і колір",
        blank=True,
        related_name="products",
    )
    related_manual = models.ManyToManyField(
        "self",
        verbose_name="Схожі вручну",
        blank=True,
        symmetrical=False,
        related_name="related_from",
    )
    seo_title_uk = models.CharField("SEO title", max_length=200, blank=True)
    seo_title_en = models.CharField("SEO title (EN)", max_length=200, blank=True)
    seo_description_uk = models.CharField("SEO description", max_length=300, blank=True)
    seo_description_en = models.CharField("SEO description (EN)", max_length=300, blank=True)

    class Meta:
        ordering = ["sort", "name_uk"]
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        indexes = [
            models.Index(fields=["is_active", "category"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self):
        return self.name_uk

    def save(self, *args, **kwargs):
        slug_set = ensure_new_slug(self)
        status_changed = False
        if self.stock_qty == 0 and self.stock_status == self.Stock.IN_STOCK:
            self.stock_status = self.Stock.OUT
            status_changed = True
        elif self.stock_qty > 0 and self.stock_status == self.Stock.OUT:
            self.stock_status = self.Stock.IN_STOCK
            status_changed = True
        update_fields = kwargs.get("update_fields")
        extra = set()
        if status_changed:
            extra.add("stock_status")
        if slug_set:
            extra.add("slug")
        if extra and update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | extra
        super().save(*args, **kwargs)

    @property
    def name(self):
        return localized(self, "name")

    @property
    def menu_name(self):
        return localized(self, "menu_name") or self.name

    @property
    def description(self):
        return localized(self, "description")

    @property
    def seo_title(self):
        return localized(self, "seo_title") or self.name

    @property
    def seo_description(self):
        return product_meta_description(self)

    def amount(self, currency: str):
        if currency == "eur":
            return self.price_eur
        return self.price_uah

    @property
    def qty_max(self):
        return min(99, self.stock_qty)

    def get_absolute_url(self):
        return reverse("product", kwargs={"slug": self.slug})

    @property
    def cover(self):
        cached = getattr(self, "_prefetched_objects_cache", {})
        if "images" in cached:
            images = list(cached["images"])
            return images[0] if images else None
        return self.images.order_by("sort", "id").first()

    @property
    def card_photo_url(self):
        if self.card_image:
            return self.card_image.url
        cover = self.cover
        if cover:
            return cover.image.url
        return ""


class CatalogCell(models.Model):
    class Layout(models.TextChoices):
        SPLIT_START = "split_start", "Сітка і велика"
        ROW = "row", "Ряд"
        SPLIT_END = "split_end", "Велика і сітка"

    class Role(models.TextChoices):
        GRID = "grid", "Картка"
        FEATURE = "feature", "Велика"

    class Crop(models.TextChoices):
        UKR = "ukr", "107.6%"
        COVER = "cover", "cover"
        SHYSH = "shysh", "114.41%"
        HNIZDO = "hnizdo", "114.99%"
        WIDE = "wide", "115.8%"

    class Surface(models.TextChoices):
        MOSAIC = "mosaic", "Мозаїка"
        FILTERS = "filters", "Фільтри"
        MOBILE = "mobile", "Мобільний"
        PDP_MOBILE = "pdp_mobile", "Картки товару"

    class Slot(models.TextChoices):
        FEATURE = "feature", "На всю ширину"
        FEATURE_TALL = "feature_tall", "Висока"
        TILE = "tile", "Плитка"
        TILE_TALL = "tile_tall", "Висока плитка"

    product = models.ForeignKey(
        Product,
        verbose_name="Товар",
        related_name="catalog_cells",
        on_delete=models.CASCADE,
    )
    band = models.PositiveSmallIntegerField("Ряд композиції")
    layout = models.CharField("Композиція", max_length=16, choices=Layout.choices)
    role = models.CharField("Роль", max_length=16, choices=Role.choices)
    sort = models.PositiveSmallIntegerField("Порядок", default=0)
    price_uah = models.DecimalField("Ціна у фреймі, грн", max_digits=10, decimal_places=2)
    crop = models.CharField("Кадр фото", max_length=16, choices=Crop.choices, default=Crop.COVER)
    name_width = models.PositiveSmallIntegerField("Ширина назви", default=127)
    surface = models.CharField(
        "Поверхня",
        max_length=16,
        choices=Surface.choices,
        default=Surface.MOSAIC,
    )
    slot = models.CharField("Слот", max_length=16, choices=Slot.choices, blank=True, default="")
    label_uk = models.CharField("Підпис у фреймі", max_length=200, blank=True)
    label_en = models.CharField("Підпис у фреймі (EN)", max_length=200, blank=True)
    image = models.ImageField(
        "Фото комірки",
        upload_to="catalog/cells/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
    )

    class Meta:
        ordering = ["band", "sort", "id"]
        verbose_name = "Комірка каталогу"
        verbose_name_plural = "Комірки каталогу"

    def __str__(self):
        return f"{self.surface}:{self.band}:{self.role}:{self.product.name_uk}"

    @property
    def label(self):
        return localized(self, "label") or self.product.name

    @property
    def price_label(self):
        whole = int(Decimal(self.price_uah).quantize(Decimal("1")))
        return f"{whole:,}".replace(",", " ") + " UAH"

    @property
    def photo_url(self):
        if self.image:
            return self.image.url
        cover = self.product.cover
        if cover:
            return cover.image.url
        return ""


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="Товар",
        related_name="images",
        on_delete=models.CASCADE,
    )
    image = models.ImageField("Фото", upload_to="products/", validators=[IMAGE_VALIDATOR])
    sort = models.PositiveIntegerField("Порядок", default=0)
    frame_height = models.DecimalField("Висота кадру, %", max_digits=6, decimal_places=2, default=Decimal("100"))
    frame_top = models.DecimalField("Зсув кадру, %", max_digits=6, decimal_places=2, default=Decimal("0"))

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "Фото товару"
        verbose_name_plural = "Фото товару"

    def __str__(self):
        return "Фото"
