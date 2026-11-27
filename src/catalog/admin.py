from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from src.core.admin_tinymce import force_tinymce, tinymce_widget

from src.catalog.admin_filters import (
    CatalogBooleanFilter,
    CatalogChoicesFilter,
    CatalogRelatedFilter,
)
from src.catalog.admin_product_form import ProductAdminForm, filter_field_names
from src.catalog.models import (
    Category,
    Product,
    ProductAttribute,
    ProductAttributeGroup,
    ProductImage,
)
from src.core.admin_actions import CATEGORY_ACTIONS, PRODUCT_ACTIONS
from src.core.admin_base import GestiaModelAdmin, GestiaStackedInline
from src.core.admin_hints import ATTRIBUTE_HINTS, CATEGORY_HINTS, GROUP_HINTS, PRODUCT_HINTS, apply_hints
from src.core.admin_lang import language_tabs
from src.core.admin_slug import SlugAdminMixin, set_form_help

HIDDEN_CATEGORY_SLUGS = ("kolektsiini-dodatky",)
GALLERY_HINT = "1272×1540 px. JPG або PNG."
GALLERY_VIDEO_HINT = "MP4 або WEBM."
GALLERY_POSTER_HINT = "Кадр до старту відео. Якщо порожньо — основне фото."


class ProductImageInline(GestiaStackedInline):
    model = ProductImage
    fields = ("media_kind", "image", "video", "poster", "sort")
    extra = 2
    ordering_field = "sort"
    hide_ordering_field = True
    classes = ("gestia-product-gallery",)
    verbose_name = "Фото або відео"
    verbose_name_plural = "Галерея картки"

    class Media:
        css = {"all": ("css/admin/product_gallery.css",)}

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is None:
            return formfield
        if db_field.name == "image":
            formfield.help_text = GALLERY_HINT
        elif db_field.name == "video":
            formfield.help_text = GALLERY_VIDEO_HINT
        elif db_field.name == "poster":
            formfield.help_text = GALLERY_POSTER_HINT
        return formfield


@admin.register(Category)
class CategoryAdmin(SlugAdminMixin, GestiaModelAdmin):
    list_display = (
        "name_uk",
        "parent",
        "slug",
        "is_active",
        "sort",
        "menu_featured",
    )
    list_filter = ("is_active", "parent")
    actions = CATEGORY_ACTIONS
    search_fields = ("name_uk", "name_en", "name_fr", "slug")
    ordering = ("sort", "name_uk")
    fieldsets = language_tabs(
        uk_fields=(
            "parent",
            "slug",
            "media_kind",
            "image",
            "video",
            "poster",
            "is_active",
            "sort",
            "menu_featured",
            "name_uk",
            "seo_title_uk",
            "seo_description_uk",
        ),
        en_fields=("name_en", "seo_title_en", "seo_description_en"),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return apply_hints(formfield, db_field.name, CATEGORY_HINTS)

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(slug__in=HIDDEN_CATEGORY_SLUGS)


@admin.register(ProductAttributeGroup)
class ProductAttributeGroupAdmin(SlugAdminMixin, GestiaModelAdmin):
    list_display = ("slug", "name_uk")
    search_fields = ("name_uk", "slug")
    fieldsets = language_tabs(
        uk_fields=("slug", "name_uk", "value_links"),
        en_fields=("name_en",),
        uk_description="Нова група (наприклад «Розмір») з’явиться окремим полем у вкладці «Фільтри» товару.",
    )
    readonly_fields = ("value_links",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return apply_hints(formfield, db_field.name, GROUP_HINTS)

    @admin.display(description="Значення")
    def value_links(self, obj):
        if obj is None or not obj.pk:
            return "Спочатку збережіть групу, потім додайте значення."
        rows = obj.values.order_by("sort", "id")
        links = format_html_join(
            "",
            '<a class="gestia-value-link" href="{}">{}</a>',
            (
                (reverse("admin:catalog_productattribute_change", args=[row.pk]), row.name_uk)
                for row in rows
            ),
        )
        add_url = f"{reverse('admin:catalog_productattribute_add')}?group={obj.pk}"
        return format_html(
            '<div class="gestia-value-list">{}<a class="gestia-value-add" href="{}">Додати</a></div>',
            links,
            add_url,
        )


@admin.register(ProductAttribute)
class ProductAttributeAdmin(SlugAdminMixin, GestiaModelAdmin):
    list_display = ("name_uk", "group", "slug", "sort", "is_filterable")
    list_filter = ("group", "is_filterable")
    search_fields = ("name_uk", "name_en", "name_fr", "slug")
    fieldsets = language_tabs(
        uk_fields=("group", "slug", "is_filterable", "show_on_pdp", "sort", "name_uk"),
        en_fields=("name_en",),
        uk_description="Значення фільтра (наприклад «Білий» у групі «Колір»).",
    )

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        group = request.GET.get("group")
        if group:
            initial["group"] = group
        return initial

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is not None and db_field.name == "sort":
            formfield.widget.attrs["maxlength"] = "3"
            formfield.widget.attrs["inputmode"] = "numeric"
            formfield.widget.attrs["min"] = "0"
            formfield.widget.attrs["max"] = "999"
            classes = formfield.widget.attrs.get("class", "")
            formfield.widget.attrs["class"] = f"{classes} gestia-sort".strip()
        return apply_hints(formfield, db_field.name, ATTRIBUTE_HINTS)

    def response_add(self, request, obj, post_url_continue=None):
        redirect = self._group_redirect(request, obj)
        if redirect is not None:
            return redirect
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        redirect = self._group_redirect(request, obj)
        if redirect is not None:
            return redirect
        return super().response_change(request, obj)

    def _group_redirect(self, request, obj):
        if "_continue" in request.POST or not obj.group_id:
            return None
        if "_addanother" in request.POST:
            url = f"{reverse('admin:catalog_productattribute_add')}?group={obj.group_id}"
            return HttpResponseRedirect(url)
        return HttpResponseRedirect(
            reverse("admin:catalog_productattributegroup_change", args=[obj.group_id])
        )


@admin.register(Product)
class ProductAdmin(SlugAdminMixin, GestiaModelAdmin):
    form = ProductAdminForm
    list_display = (
        "name_uk",
        "sku",
        "category",
        "price_uah",
        "price_eur",
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
        ("stock_status", CatalogChoicesFilter),
        ("is_active", CatalogBooleanFilter),
        ("is_sale", CatalogBooleanFilter),
    )
    list_filter_options = {
        "category": {"horizontal": True, "label": "Категорія"},
        "stock_status": {"horizontal": True, "label": "Наявність"},
        "is_active": {"horizontal": True, "label": "Активний"},
        "is_sale": {"horizontal": True, "label": "Акція"},
    }
    actions = PRODUCT_ACTIONS
    search_fields = ("name_uk", "name_en", "name_fr", "sku", "slug")
    autocomplete_fields = ("category", "related_manual")
    inlines = [ProductImageInline]
    ordering = ("sort", "name_uk")
    fieldsets = language_tabs(
        uk_fields=(
            "category",
            "sku",
            "slug",
            "price_uah",
            "price_eur",
            "stock_status",
            "stock_qty",
            "is_active",
            "is_sale",
            "is_popular",
            "card_crop",
            "name_width",
            "media_kind",
            "card_image",
            "video",
            "poster",
            "sort",
            "related_manual",
            "name_uk",
            "description_uk",
            "seo_title_uk",
            "seo_description_uk",
        ),
        en_fields=(
            "name_en",
            "description_en",
            "seo_title_en",
            "seo_description_en",
        ),
    )

    tiny_fields = ("description_uk", "description_en", "description_fr")

    def get_fieldsets(self, request, obj=None):
        filter_fields = tuple(filter_field_names())
        extra = ()
        if filter_fields:
            extra = (
                (
                    "Фільтри",
                    {
                        "classes": ("tab",),
                        "fields": filter_fields,
                        "description": "Окреме поле на кожну групу. Нові групи — у розділі «Фільтри» каталогу.",
                    },
                ),
            )
        return super().get_fieldsets(request, obj) + extra

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=False)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return apply_hints(formfield, db_field.name, PRODUCT_HINTS)

    def get_form(self, request, obj=None, change=False, **kwargs):
        fields = kwargs.get("fields")
        if fields is not None:
            kwargs["fields"] = tuple(
                name for name in fields if not str(name).startswith("attr_group_")
            )
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=False)
        return form

