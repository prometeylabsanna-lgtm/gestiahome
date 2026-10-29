from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from unfold.widgets import UnfoldAdminTextInputWidget

from src.content.admin_keyed import KeyedBlockAdmin
from src.content.admin_limits import tighten
from src.content.home_slots import sync_category_home_sort, sync_popular_flags
from src.content.models import ContactForms, HomeBlock
from src.content.models_home_slots import HomeCategorySlot, HomePopularSlot
from src.content.proxies import (
    HomeAdvantagesBlock,
    HomeCallbackBlock,
    HomeCategoriesBlock,
    HomePopularBlock,
    HomeReviewsBlock,
)
from src.core.admin_base import (
    AdminImagePreviewWidget,
    GestiaModelAdmin,
    GestiaStackedInline,
    GestiaTabularInline,
)
from src.core.admin_lang import language_tabs
from src.core.admin_tinymce import force_tinymce, tinymce_widget

CARD_PHOTO = "303×197 px. Спільне фото для всіх карток (десктоп і мобільний). JPG або PNG."
CAT_PHOTO = "Плитка категорії. JPG або PNG, довга сторона до 2560 px."


class HomeCategorySlotForm(forms.ModelForm):
    image = forms.ImageField(
        label="Фото",
        required=False,
        help_text=CAT_PHOTO,
        widget=AdminImagePreviewWidget,
    )

    class Meta:
        model = HomeCategorySlot
        fields = ("category", "sort")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.category_id:
            self.fields["image"].initial = self.instance.category.image

    def save(self, commit=True):
        obj = super().save(commit=False)
        if commit:
            obj.save()
        if obj.category_id and "image" in self.cleaned_data:
            cat = obj.category
            image = self.cleaned_data["image"]
            if image is False:
                cat.image = None
                cat.save(update_fields=["image"])
            elif image:
                cat.image = image
                cat.save(update_fields=["image"])
        return obj


class HomeCategorySlotInline(GestiaTabularInline):
    model = HomeCategorySlot
    form = HomeCategorySlotForm
    extra = 0
    tab = True
    verbose_name = "Категорія"
    verbose_name_plural = "Категорії"
    ordering_field = "sort"
    hide_ordering_field = True
    autocomplete_fields = ("category",)
    fields = ("category", "image", "sort")


class HomePopularSlotInline(GestiaTabularInline):
    model = HomePopularSlot
    extra = 0
    tab = True
    verbose_name = "Товар"
    verbose_name_plural = "Товари"
    ordering_field = "sort"
    hide_ordering_field = True
    autocomplete_fields = ("product",)
    fields = ("product", "sort")


class HomeCallbackForm(forms.ModelForm):
    ph_name_uk = forms.CharField(
        label="Підказка імені", max_length=24, required=False, widget=UnfoldAdminTextInputWidget
    )
    ph_name_en = forms.CharField(
        label="Підказка імені (EN)", max_length=24, required=False, widget=UnfoldAdminTextInputWidget
    )
    ph_phone_uk = forms.CharField(
        label="Підказка телефону", max_length=24, required=False, widget=UnfoldAdminTextInputWidget
    )
    ph_phone_en = forms.CharField(
        label="Підказка телефону (EN)", max_length=24, required=False, widget=UnfoldAdminTextInputWidget
    )
    ph_message_uk = forms.CharField(
        label="Підказка повідомлення", max_length=24, required=False, widget=UnfoldAdminTextInputWidget
    )
    ph_message_en = forms.CharField(
        label="Підказка повідомлення (EN)",
        max_length=24,
        required=False,
        widget=UnfoldAdminTextInputWidget,
    )

    class Meta:
        model = HomeCallbackBlock
        fields = (
            "title_uk",
            "title_en",
            "text_uk",
            "text_en",
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        force_tinymce(
            self,
            ("text_uk", "text_en"),
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


@admin.register(HomeCategoriesBlock)
class HomeCategoriesAdmin(KeyedBlockAdmin):
    block_key = HomeBlock.Key.CATEGORIES
    default_sort = 2
    inlines = (HomeCategorySlotInline,)
    text_limits = {"title_uk": 20, "title_en": 20}
    tiny_fields = ()
    fieldsets = language_tabs(
        uk_fields=("title_uk",),
        en_fields=("title_en",),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        sync_category_home_sort(form.instance)


@admin.register(HomePopularBlock)
class HomePopularAdmin(KeyedBlockAdmin):
    block_key = HomeBlock.Key.POPULAR
    default_sort = 4
    inlines = (HomePopularSlotInline,)
    text_limits = {"title_uk": 24, "title_en": 24, "cta_uk": 28, "cta_en": 28}
    tiny_fields = ()
    fieldsets = language_tabs(
        uk_fields=("title_uk", "cta_uk"),
        en_fields=("title_en", "cta_en"),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        sync_popular_flags(form.instance)


@admin.register(HomeAdvantagesBlock)
class HomeAdvantagesAdmin(KeyedBlockAdmin):
    block_key = HomeBlock.Key.ADVANTAGES
    default_sort = 5
    inlines = ()
    text_limits = {
        "title_uk": 36,
        "title_en": 36,
        "text_uk": 110,
        "text_en": 110,
        "cta_uk": 28,
        "cta_en": 28,
    }
    image_hints = {"image": CARD_PHOTO}
    fieldsets = language_tabs(
        uk_fields=("title_uk", "text_uk", "cta_uk", "image"),
        en_fields=("title_en", "text_en", "cta_en"),
    )


@admin.register(HomeReviewsBlock)
class HomeReviewsAdmin(KeyedBlockAdmin):
    block_key = HomeBlock.Key.REVIEWS
    default_sort = 7
    text_limits = {"title_uk": 16, "title_en": 16}
    tiny_fields = ()
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


class ContactFormsAdmin(_SingletonAdmin):
    """Сховано з меню; literals покривають підписи форм."""

    fieldsets = language_tabs(
        uk_fields=(
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
