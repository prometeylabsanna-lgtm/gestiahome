from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.admin_limits import tighten
from src.content.admin_home_video import PageVideoMixin
from src.content.models import ContactForms, HomeBlock
from src.content.proxies import (
    HomeAdvantagesBlock,
    HomeCallbackBlock,
    HomeCategoriesBlock,
    HomeHeroBlock,
    HomePopularBlock,
    HomeReviewsBlock,
)
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_lang import language_tabs
from src.core.admin_tinymce import force_tinymce, tinymce_widget

PHOTO_DESK = "1442×871 px. JPG або PNG."
PHOTO_MOBILE = "390×735 px. JPG або PNG."
VIDEO_HINT = "MP4 або WEBM."
CARD_PHOTO = "303×197 px. Спільне фото для всіх карток. JPG або PNG."
_TINY = frozenset(
    {
        "text_uk",
        "text_en",
        "text_mobile_uk",
        "text_mobile_en",
    }
)


class KeyedBlockAdmin(GestiaModelAdmin):
    block_key = ""
    default_sort = 0
    text_limits = {}
    image_hints = {}
    tiny_fields = _TINY

    def get_queryset(self, request):
        return super().get_queryset(request).filter(key=self.block_key)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = HomeBlock.objects.filter(key=self.block_key).first()
        if obj is None:
            obj = HomeBlock.objects.create(key=self.block_key, sort=self.default_sort)
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)

    def save_model(self, request, obj, form, change):
        obj.key = self.block_key
        super().save_model(request, obj, form, change)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        hint = self.image_hints.get(db_field.name, "")
        if db_field.name == "video":
            hint = VIDEO_HINT
        return tighten(formfield, self.text_limits.get(db_field.name), hint)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        return form


class HomeCallbackForm(forms.ModelForm):
    ph_name_uk = forms.CharField(label="Підказка імені", max_length=24, required=False)
    ph_name_en = forms.CharField(label="Підказка імені (EN)", max_length=24, required=False)
    ph_phone_uk = forms.CharField(label="Підказка телефону", max_length=24, required=False)
    ph_phone_en = forms.CharField(label="Підказка телефону (EN)", max_length=24, required=False)
    ph_message_uk = forms.CharField(label="Підказка повідомлення", max_length=24, required=False)
    ph_message_en = forms.CharField(label="Підказка повідомлення (EN)", max_length=24, required=False)

    class Meta:
        model = HomeCallbackBlock
        fields = (
            "title_uk",
            "title_en",
            "text_uk",
            "text_en",
            "text_mobile_uk",
            "text_mobile_en",
            "note_uk",
            "note_en",
            "link_uk",
            "link_en",
            "cta_uk",
            "cta_en",
        )
        widgets = {
            "text_uk": tinymce_widget(short=True),
            "text_en": tinymce_widget(short=True),
            "text_mobile_uk": tinymce_widget(short=True),
            "text_mobile_en": tinymce_widget(short=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        force_tinymce(
            self,
            ("text_uk", "text_en", "text_mobile_uk", "text_mobile_en"),
            short=True,
        )
        uk = _lines(self.instance.lines_uk)
        en = _lines(self.instance.lines_en)
        self.fields["ph_name_uk"].initial = uk[0]
        self.fields["ph_phone_uk"].initial = uk[1]
        self.fields["ph_message_uk"].initial = uk[2]
        self.fields["ph_name_en"].initial = en[0]
        self.fields["ph_phone_en"].initial = en[1]
        self.fields["ph_message_en"].initial = en[2]

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.lines_uk = _join(self.cleaned_data, "uk")
        obj.lines_en = _join(self.cleaned_data, "en")
        obj.key = HomeBlock.Key.CALLBACK
        if commit:
            obj.save()
        return obj


def _lines(value):
    parts = (value or "").splitlines()
    while len(parts) < 3:
        parts.append("")
    return parts[:3]


def _join(cleaned, lang):
    return "\n".join(
        [
            cleaned.get(f"ph_name_{lang}", ""),
            cleaned.get(f"ph_phone_{lang}", ""),
            cleaned.get(f"ph_message_{lang}", ""),
        ]
    )


@admin.register(HomeHeroBlock)
class HomeHeroAdmin(KeyedBlockAdmin):
    block_key = HomeBlock.Key.HERO
    default_sort = 1
    text_limits = {
        "title_uk": 64,
        "title_en": 64,
        "text_uk": 200,
        "text_en": 200,
        "cta_uk": 28,
        "cta_en": 28,
    }
    image_hints = {
        "image": PHOTO_DESK,
        "image_mobile": PHOTO_MOBILE,
        "poster": "Кадр до старту відео, 1442×871 px. Якщо порожньо — основне фото. JPG або PNG.",
    }
    fieldsets = language_tabs(
        uk_fields=("title_uk", "text_uk", "cta_uk", "media_kind", "image", "image_mobile", "video", "poster"),
        en_fields=("title_en", "text_en", "cta_en"),
    )


@admin.register(HomeCategoriesBlock)
class HomeCategoriesAdmin(PageVideoMixin, KeyedBlockAdmin):
    block_key = HomeBlock.Key.CATEGORIES
    default_sort = 2
    page_video_key = HomeBlock.Key.VIDEO
    page_video_sort = 3
    page_video_title = "Відео-блок після категорій"
    page_video_description = (
        "На головній цей блок стоїть одразу після категорій і перед популярними товарами."
    )
    text_limits = {"title_uk": 20, "title_en": 20}
    fieldsets = language_tabs(
        uk_fields=("title_uk",),
        en_fields=("title_en",),
    )


@admin.register(HomePopularBlock)
class HomePopularAdmin(KeyedBlockAdmin):
    block_key = HomeBlock.Key.POPULAR
    default_sort = 4
    text_limits = {"title_uk": 24, "title_en": 24, "cta_uk": 28, "cta_en": 28}
    fieldsets = language_tabs(
        uk_fields=("title_uk", "cta_uk"),
        en_fields=("title_en", "cta_en"),
    )


@admin.register(HomeAdvantagesBlock)
class HomeAdvantagesAdmin(PageVideoMixin, KeyedBlockAdmin):
    block_key = HomeBlock.Key.ADVANTAGES
    default_sort = 5
    page_video_key = HomeBlock.Key.VIDEO_2
    page_video_sort = 6
    page_video_title = "Відео-блок після переваг"
    page_video_description = (
        "На головній цей блок стоїть одразу після переваг і перед відгуками."
    )
    text_limits = {
        "title_uk": 36,
        "title_en": 36,
        "text_uk": 110,
        "text_en": 110,
        "text_mobile_uk": 110,
        "text_mobile_en": 110,
        "cta_uk": 28,
        "cta_en": 28,
    }
    image_hints = {"image": CARD_PHOTO}
    fieldsets = language_tabs(
        uk_fields=("title_uk", "text_uk", "text_mobile_uk", "cta_uk", "image"),
        en_fields=("title_en", "text_en", "text_mobile_en", "cta_en"),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "text_mobile_uk" and formfield is not None:
            formfield.help_text = "Для телефона. Якщо порожньо — текст із комп’ютера."
        return formfield


@admin.register(HomeReviewsBlock)
class HomeReviewsAdmin(KeyedBlockAdmin):
    block_key = HomeBlock.Key.REVIEWS
    default_sort = 7
    text_limits = {"title_uk": 16, "title_en": 16}
    fieldsets = language_tabs(
        uk_fields=("title_uk",),
        en_fields=("title_en",),
    )


@admin.register(HomeCallbackBlock)
class HomeCallbackAdmin(KeyedBlockAdmin):
    form = HomeCallbackForm
    block_key = HomeBlock.Key.CALLBACK
    default_sort = 8
    text_limits = {
        "title_uk": 32,
        "title_en": 32,
        "text_uk": 100,
        "text_en": 100,
        "text_mobile_uk": 100,
        "text_mobile_en": 100,
        "note_uk": 72,
        "note_en": 72,
        "link_uk": 40,
        "link_en": 40,
        "cta_uk": 28,
        "cta_en": 28,
        "ph_name_uk": 24,
        "ph_name_en": 24,
        "ph_phone_uk": 24,
        "ph_phone_en": 24,
        "ph_message_uk": 24,
        "ph_message_en": 24,
    }
    fieldsets = language_tabs(
        uk_fields=(
            "title_uk",
            "text_uk",
            "text_mobile_uk",
            "ph_name_uk",
            "ph_phone_uk",
            "ph_message_uk",
            "note_uk",
            "link_uk",
            "cta_uk",
        ),
        en_fields=(
            "title_en",
            "text_en",
            "text_mobile_en",
            "ph_name_en",
            "ph_phone_en",
            "ph_message_en",
            "note_en",
            "link_en",
            "cta_en",
        ),
    )

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        for name, limit in self.text_limits.items():
            if name in form.base_fields:
                tighten(form.base_fields[name], limit)
        return form


class _SingletonAdmin(GestiaModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.load()
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)


@admin.register(ContactForms)
class ContactFormsAdmin(_SingletonAdmin):
    fieldsets = language_tabs(
        uk_fields=(
            "waitlist_title_uk",
            "waitlist_p1_uk",
            "waitlist_p2_uk",
            "waitlist_p3_uk",
            "waitlist_email_uk",
            "waitlist_consent_uk",
            "waitlist_privacy_uk",
            "waitlist_button_uk",
            "waitlist_thanks_title_uk",
            "waitlist_thanks_text_uk",
            "contact_button_uk",
            "callback_button_uk",
            "buy_button_uk",
            "sheet_close_uk",
            "sheet_consent_uk",
            "label_name_uk",
            "label_phone_uk",
            "label_message_uk",
            "label_address_uk",
            "label_email_uk",
        ),
        en_fields=(
            "waitlist_title_en",
            "waitlist_p1_en",
            "waitlist_p2_en",
            "waitlist_p3_en",
            "waitlist_email_en",
            "waitlist_consent_en",
            "waitlist_privacy_en",
            "waitlist_button_en",
            "waitlist_thanks_title_en",
            "waitlist_thanks_text_en",
            "contact_button_en",
            "callback_button_en",
            "buy_button_en",
            "sheet_close_en",
            "sheet_consent_en",
            "label_name_en",
            "label_phone_en",
            "label_message_en",
            "label_address_en",
            "label_email_en",
        ),
    )
