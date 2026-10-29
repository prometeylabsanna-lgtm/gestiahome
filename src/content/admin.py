from django.contrib import admin

from src.content.admin_limits import tighten
from src.content.models import Advantage, FooterLink, HomeBlock, Review, SiteSettings
from src.content.proxies import AboutReview, HomeReview
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_lang import language_tabs
from src.core.admin_tinymce import force_tinymce, tinymce_widget

# Реєстрація окремих блоків головної, форм, «Про нас» і підвалу.
import src.content.admin_about  # noqa: F401, E402
import src.content.admin_blocks  # noqa: F401, E402
import src.content.admin_discount  # noqa: F401, E402
import src.content.admin_home_banners  # noqa: F401, E402
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
            "telegram_url",
            "logo",
        ),
        en_fields=(),
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

    tiny_fields = ("text_uk", "text_en")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        return form


@admin.register(Advantage)
class AdvantageAdmin(GestiaModelAdmin):
    list_display = ("title_uk", "sort")
    search_fields = ("title_uk", "title_en")
    ordering = ("sort",)
    text_limits = {"title_uk": 24, "title_en": 24, "text_uk": 80, "text_en": 80}
    tiny_fields = ("text_uk", "text_en")
    fieldsets = language_tabs(
        uk_fields=("sort", "title_uk", "text_uk", "image"),
        en_fields=("title_en", "text_en"),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        hint = ""
        if db_field.name == "image":
            hint = "303×197 px. Якщо порожньо — лишається фото блоку «Переваги». JPG або PNG."
        return tighten(formfield, self.text_limits.get(db_field.name), hint)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        for name, limit in self.text_limits.items():
            if name in form.base_fields:
                tighten(form.base_fields[name], limit)
        return form

    def save_model(self, request, obj, form, change):
        if obj.block_id is None:
            block, _ = HomeBlock.objects.get_or_create(
                key=HomeBlock.Key.ADVANTAGES,
                defaults={"sort": 5, "title_uk": "Чому обирають GESTIA HOME"},
            )
            obj.block = block
        super().save_model(request, obj, form, change)


class ReviewAdmin(GestiaModelAdmin):
    placement = Review.Placement.HOME
    list_display = ("author_uk", "rating_kind", "sort")
    search_fields = ("author_uk", "text_uk")
    ordering = ("sort",)
    text_limits = {"author_uk": 24, "author_en": 24, "text_uk": 180, "text_en": 180}
    tiny_fields = ("text_uk", "text_en")
    fieldsets = language_tabs(
        uk_fields=("sort", "rating_kind", "author_uk", "text_uk"),
        en_fields=("author_en", "text_en"),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(placement=self.placement)

    def save_model(self, request, obj, form, change):
        obj.placement = self.placement
        super().save_model(request, obj, form, change)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return tighten(formfield, self.text_limits.get(db_field.name))

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        for name, limit in self.text_limits.items():
            if name in form.base_fields:
                tighten(form.base_fields[name], limit)
        return form


@admin.register(HomeReview)
class HomeReviewAdmin(ReviewAdmin):
    placement = Review.Placement.HOME


@admin.register(AboutReview)
class AboutReviewAdmin(ReviewAdmin):
    placement = Review.Placement.ABOUT



# FooterLink сховано: футер збирається автоматично з категорій і юридичних сторінок.
class FooterLinkAdmin(GestiaModelAdmin):
    list_display = ("label_uk", "column", "url_name", "underlined", "sort")
    fieldsets = language_tabs(
        uk_fields=("column", "url_name", "url_arg", "underlined", "sort", "label_uk"),
        en_fields=("label_en",),
    )
