from django.contrib import admin

from src.content.models import (
    FooterLink,
    HomeBlock,
    HomeCollection,
    HomeCollectionImage,
    SiteSettings,
)
from src.core.admin_base import GestiaModelAdmin, GestiaTabularInline
from src.core.admin_hints import COLLECTION_HINTS, SITE_HINTS, apply_hints
from src.core.admin_lang import language_tabs
from src.core.admin_tinymce import force_tinymce, tinymce_widget

# Реєстрація окремих блоків головної, форм, «Про нас» і підвалу.
import src.content.admin_about  # noqa: F401, E402
import src.content.admin_blocks  # noqa: F401, E402
import src.content.admin_faq  # noqa: F401, E402
import src.content.admin_home_banners  # noqa: F401, E402
import src.content.admin_legal  # noqa: F401, E402
import src.content.admin_menu  # noqa: F401, E402
import src.content.admin_styles  # noqa: F401, E402
import src.content.admin_contacts  # noqa: F401, E402
import src.content.admin_thankyou  # noqa: F401, E402
import src.content.admin_ui  # noqa: F401, E402


class SingletonAdmin(GestiaModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdmin):
    fieldsets = language_tabs(
        uk_fields=(
            "site_name_uk",
            "phone",
            "email",
            "address_uk",
            "instagram_url",
            "pinterest_url",
            "telegram_url",
            "logo",
            "logo_alt_uk",
            "mark_light",
            "mark_dark",
            "nav_about_uk",
            "nav_faq_uk",
            "nav_contacts_uk",
            "nav_all_uk",
            "menu_title_uk",
            "credit_uk",
            "en_enabled",
            "fr_enabled",
        ),
        en_fields=(
            "site_name_en",
            "address_en",
            "logo_alt_en",
            "nav_about_en",
            "nav_faq_en",
            "nav_contacts_en",
            "nav_all_en",
            "menu_title_en",
            "credit_en",
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return apply_hints(formfield, db_field.name, SITE_HINTS)


@admin.register(HomeBlock)
class HomeBlockAdmin(GestiaModelAdmin):
    list_display = ("key", "title_uk", "sort")
    list_filter = ("key",)
    search_fields = ("title_uk", "title_en", "text_uk")
    ordering = ("sort",)
    fieldsets = language_tabs(
        uk_fields=(
            "key",
            "sort",
            "title_uk",
            "text_uk",
            "cta_uk",
            "link_uk",
            "note_uk",
            "lines_uk",
            "media_kind",
            "image",
            "video",
            "poster",
            "seo_title_uk",
            "seo_description_uk",
        ),
        en_fields=(
            "title_en",
            "text_en",
            "cta_en",
            "link_en",
            "note_en",
            "lines_en",
            "seo_title_en",
            "seo_description_en",
        ),
    )

    tiny_fields = ("text_uk", "text_en", "text_fr")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        return form


class HomeCollectionImageInline(GestiaTabularInline):
    model = HomeCollectionImage
    extra = 0
    tab = True
    verbose_name = "Фото"
    verbose_name_plural = "Галерея"
    ordering_field = "sort"
    hide_ordering_field = True
    fields = ("image", "alt_uk", "alt_en", "alt_fr", "sort")


@admin.register(HomeCollection)
class HomeCollectionAdmin(GestiaModelAdmin):
    list_display = ("title_uk", "slug", "is_active", "sort")
    list_filter = ("is_active",)
    search_fields = ("title_uk", "title_en", "label_uk", "slug")
    ordering = ("sort", "id")
    autocomplete_fields = ("category", "product", "addons")
    inlines = (HomeCollectionImageInline,)
    tiny_fields = ("text_uk", "text_en", "story_uk", "story_en", "text_fr", "story_fr")
    fieldsets = language_tabs(
        uk_fields=(
            "is_active",
            "sort",
            "slug",
            "label_uk",
            "title_uk",
            "text_uk",
            "story_uk",
            "box_items_uk",
            "image_large",
            "image_small",
            "alt_large_uk",
            "alt_small_uk",
            "category",
            "product",
            "addons",
            "seo_title_uk",
            "seo_description_uk",
        ),
        en_fields=(
            "label_en",
            "title_en",
            "text_en",
            "story_en",
            "box_items_en",
            "alt_large_en",
            "alt_small_en",
            "seo_title_en",
            "seo_description_en",
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return apply_hints(formfield, db_field.name, COLLECTION_HINTS, seo=True)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        return form

    def save_model(self, request, obj, form, change):
        if obj.block_id is None:
            block, _ = HomeBlock.objects.get_or_create(
                key=HomeBlock.Key.COLLECTIONS,
                defaults={
                    "sort": 2,
                    "title_uk": "Різдвяна колекція святкових боксів",
                    "link_uk": "Традиції починаються зі столу",
                    "cta_uk": "Дізнатись детальніше",
                },
            )
            obj.block = block
        super().save_model(request, obj, form, change)


# FooterLink сховано: футер збирається автоматично з категорій і юридичних сторінок.
class FooterLinkAdmin(GestiaModelAdmin):
    list_display = ("label_uk", "column", "url_name", "underlined", "sort")
    fieldsets = language_tabs(
        uk_fields=("column", "url_name", "url_arg", "underlined", "sort", "label_uk"),
        en_fields=("label_en",),
    )
