from django.contrib import admin

from src.core.admin_tinymce import force_tinymce, tinymce_widget

from src.catalog.admin_filters import (
    CatalogBooleanFilter,
    CatalogChoicesFilter,
    CatalogRelatedFilter,
)
from src.catalog.models import (
    CatalogCell,
    Category,
    Product,
    ProductAttribute,
    ProductAttributeGroup,
    ProductImage,
    ProductSet,
)
from src.core.admin_base import GestiaModelAdmin, GestiaStackedInline
from src.core.admin_lang import language_tabs
from src.core.admin_slug import SlugAdminMixin

GALLERY_HINT = "1272×1540 px. JPG або PNG."


class ProductImageInline(GestiaStackedInline):
    model = ProductImage
    fields = ("image", "frame_height", "frame_top", "sort")
    extra = 1
    ordering_field = "sort"
    hide_ordering_field = True
    classes = ("gestia-product-gallery",)
    verbose_name = "Фото"
    verbose_name_plural = "Галерея"

    class Media:
        css = {"all": ("css/admin/product_gallery.css",)}

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "image" and formfield is not None:
            formfield.help_text = GALLERY_HINT
        return formfield


@admin.register(Category)
class CategoryAdmin(SlugAdminMixin, GestiaModelAdmin):
    list_display = (
        "name_uk",
        "parent",
        "slug",
        "is_active",
        "sort",
        "home_sort",
        "menu_featured",
        "filter_sort",
    )
    list_filter = ("is_active", "parent")
    search_fields = ("name_uk", "name_en", "slug")
    ordering = ("sort", "name_uk")
    fieldsets = language_tabs(
        uk_fields=(
            "parent",
            "slug",
            "image",
            "is_active",
            "sort",
            "home_sort",
            "menu_featured",
            "filter_sort",
            "name_uk",
            "filter_name_uk",
            "seo_title_uk",
            "seo_description_uk",
        ),
        en_fields=("name_en", "seo_title_en", "seo_description_en"),
    )


@admin.register(ProductAttributeGroup)
class ProductAttributeGroupAdmin(SlugAdminMixin, GestiaModelAdmin):
    auto_slug = False
    list_display = ("slug", "name_uk")
    search_fields = ("name_uk", "slug")
    fieldsets = language_tabs(
        uk_fields=("slug", "name_uk"),
        en_fields=("name_en",),
    )


@admin.register(ProductAttribute)
class ProductAttributeAdmin(SlugAdminMixin, GestiaModelAdmin):
    list_display = ("name_uk", "group", "slug", "sort", "is_filterable")
    list_filter = ("group", "is_filterable")
    search_fields = ("name_uk", "name_en", "slug")
    fieldsets = language_tabs(
        uk_fields=("group", "slug", "is_filterable", "show_on_pdp", "sort", "name_uk"),
        en_fields=("name_en",),
    )


@admin.register(ProductSet)
class ProductSetAdmin(SlugAdminMixin, GestiaModelAdmin):
    list_display = ("name_uk", "slug")
    search_fields = ("name_uk", "name_en", "slug")
    fieldsets = language_tabs(
        uk_fields=("slug", "name_uk"),
        en_fields=("name_en",),
    )


@admin.register(CatalogCell)
class CatalogCellAdmin(GestiaModelAdmin):
    list_display = ("product", "surface", "band", "layout", "role", "slot", "sort", "price_uah", "crop")
    list_filter = ("surface", "band", "layout", "role", "slot")
    autocomplete_fields = ("product",)
    ordering = ("band", "sort")


@admin.register(Product)
class ProductAdmin(SlugAdminMixin, GestiaModelAdmin):
    list_display = (
        "name_uk",
        "sku",
        "category",
        "price_uah",
        "price_eur",
        "price_weight",
        "is_popular",
        "stock_status",
        "stock_qty",
        "is_active",
        "is_sale",
    )
    list_display_links = ("name_uk",)
    list_editable = ("stock_qty",)
    list_filter_submit = True
    list_filter_sheet = False
    list_filter = (
        ("category", CatalogRelatedFilter),
        ("product_set", CatalogRelatedFilter),
        ("stock_status", CatalogChoicesFilter),
        ("is_active", CatalogBooleanFilter),
        ("is_sale", CatalogBooleanFilter),
    )
    list_filter_options = {
        "category": {"horizontal": True, "label": "Категорія"},
        "product_set": {"horizontal": True, "label": "Сет"},
        "stock_status": {"horizontal": True, "label": "Наявність"},
        "is_active": {"horizontal": True, "label": "Активний"},
        "is_sale": {"horizontal": True, "label": "Акція"},
    }
    actions = (
        "activate_products",
        "deactivate_products",
        "set_sale",
        "unset_sale",
    )
    search_fields = ("name_uk", "name_en", "sku", "slug")
    autocomplete_fields = ("category", "product_set")
    filter_horizontal = ("filter_attrs", "related_manual")
    inlines = [ProductImageInline]
    ordering = ("sort", "name_uk")
    fieldsets = language_tabs(
        uk_fields=(
            "category",
            "product_set",
            "sku",
            "slug",
            "price_uah",
            "price_eur",
            "stock_status",
            "stock_qty",
            "is_active",
            "is_sale",
            "is_popular",
            "price_weight",
            "card_crop",
            "name_width",
            "card_image",
            "sort",
            "filter_attrs",
            "related_manual",
            "name_uk",
            "menu_name_uk",
            "description_uk",
            "seo_title_uk",
            "seo_description_uk",
        ),
        en_fields=(
            "name_en",
            "menu_name_en",
            "description_en",
            "seo_title_en",
            "seo_description_en",
        ),
    )

    tiny_fields = ("description_uk", "description_en")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=False)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=False)
        return form

    @admin.action(description="Активувати")
    def activate_products(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Деактивувати")
    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Позначити акцією")
    def set_sale(self, request, queryset):
        queryset.update(is_sale=True)

    @admin.action(description="Зняти акцію")
    def unset_sale(self, request, queryset):
        queryset.update(is_sale=False)
