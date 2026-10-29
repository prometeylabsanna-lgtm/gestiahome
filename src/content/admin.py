from django.conf import settings
from django.contrib import admin
from tinymce.widgets import TinyMCE

from src.content.admin_limits import tighten
from src.content.models import Advantage, FooterLink, HomeBlock, Review, SiteSettings
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_lang import language_tabs

# Реєстрація окремих блоків головної, форм, «Про нас» і підвалу.
import src.content.admin_about  # noqa: F401, E402
import src.content.admin_blocks  # noqa: F401, E402
import src.content.admin_discount  # noqa: F401, E402
import src.content.admin_legal  # noqa: F401, E402
import src.content.admin_styles  # noqa: F401, E402


class SingletonAdmin(GestiaModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdmin):
    fieldsets = language_tabs(
        uk_fields=(
            "phone",
            "email",
            "instagram_url",
            "pinterest_url",
            "logo",
            "nav_about_uk",
            "nav_all_uk",
            "menu_title_uk",
            "address_uk",
            "en_enabled",
            "telegram_notify_orders",
            "telegram_notify_leads",
        ),
        en_fields=("nav_about_en", "nav_all_en", "menu_title_en", "address_en"),
    )


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
            "text_mobile_uk",
            "cta_uk",
            "link_uk",
            "note_uk",
            "lines_uk",
            "media_kind",
            "image",
            "image_mobile",
            "video",
            "poster",
        ),
        en_fields=(
            "title_en",
            "text_en",
            "text_mobile_en",
            "cta_en",
            "link_en",
            "note_en",
            "lines_en",
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in {"text_uk", "text_en", "text_mobile_uk", "text_mobile_en"}:
            kwargs["widget"] = TinyMCE(mce_attrs=settings.TINYMCE_SHORT_CONFIG)
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(Advantage)
class AdvantageAdmin(GestiaModelAdmin):
    list_display = ("title_uk", "sort")
    search_fields = ("title_uk", "title_en")
    ordering = ("sort",)
    text_limits = {"title_uk": 24, "title_en": 24, "text_uk": 80, "text_en": 80}
    fieldsets = language_tabs(
        uk_fields=("sort", "title_uk", "text_uk", "image"),
        en_fields=("title_en", "text_en"),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in {"text_uk", "text_en"}:
            kwargs["widget"] = TinyMCE(mce_attrs=settings.TINYMCE_SHORT_CONFIG)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        hint = ""
        if db_field.name == "image":
            hint = "303×197 px. Якщо порожньо — лишається фото блоку «Переваги». JPG або PNG."
        return tighten(formfield, self.text_limits.get(db_field.name), hint)


@admin.register(Review)
class ReviewAdmin(GestiaModelAdmin):
    list_display = ("author_uk", "rating_kind", "sort")
    search_fields = ("author_uk", "text_uk")
    ordering = ("sort",)
    text_limits = {"author_uk": 24, "author_en": 24, "text_uk": 180, "text_en": 180}
    fieldsets = language_tabs(
        uk_fields=("sort", "rating_kind", "author_uk", "text_uk"),
        en_fields=("author_en", "text_en"),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in {"text_uk", "text_en"}:
            kwargs["widget"] = TinyMCE(mce_attrs=settings.TINYMCE_SHORT_CONFIG)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return tighten(formfield, self.text_limits.get(db_field.name))


@admin.register(FooterLink)
class FooterLinkAdmin(GestiaModelAdmin):
    list_display = ("label_uk", "column", "url_name", "underlined", "sort")
    list_filter = ("column", "underlined")
    search_fields = ("label_uk", "label_en")
    ordering = ("column", "sort")
    fieldsets = language_tabs(
        uk_fields=("column", "url_name", "url_arg", "underlined", "sort", "label_uk"),
        en_fields=("label_en",),
    )
