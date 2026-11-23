from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.admin_keyed import KeyedBlockAdmin
from src.content.admin_limits import tighten
from src.content.home_slots import sync_popular_flags
from src.content.models import ContactForms, HomeBlock, HomeCollection
from src.content.models_home_slots import HomePopularSlot
from src.content.proxies import (
    HomeCollectionsBlock,
    HomeLocaleBlock,
    HomePopularBlock,
)
from src.core.admin_base import GestiaModelAdmin, GestiaStackedInline, GestiaTabularInline
from src.core.admin_lang import language_tabs
from src.core.admin_tinymce import force_tinymce, tinymce_widget


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


class HomeCollectionInline(GestiaStackedInline):
    model = HomeCollection
    extra = 0
    tab = True
    verbose_name = "Колекція"
    verbose_name_plural = "Колекції"
    ordering_field = "sort"
    hide_ordering_field = True
    autocomplete_fields = ("category",)
    tiny_fields = ("text_uk", "text_en", "text_fr")
    fields = (
        "is_active",
        "sort",
        "label_uk",
        "label_en",
        "title_uk",
        "title_en",
        "text_uk",
        "text_en",
        "image_large",
        "image_small",
        "alt_large_uk",
        "alt_large_en",
        "alt_small_uk",
        "alt_small_en",
        "category",
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(HomeCollectionsBlock)
class HomeCollectionsAdmin(KeyedBlockAdmin):
    block_key = HomeBlock.Key.COLLECTIONS
    default_sort = 2
    inlines = (HomeCollectionInline,)
    text_limits = {
        "title_uk": 80,
        "title_en": 80,
        "link_uk": 80,
        "link_en": 80,
        "cta_uk": 40,
        "cta_en": 40,
    }
    tiny_fields = ()
    fieldsets = language_tabs(
        uk_fields=("title_uk", "link_uk", "cta_uk"),
        en_fields=("title_en", "link_en", "cta_en"),
    )


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


LOCALE_FIELD_META = {
    "title_uk": ("Заголовок діалогу", "Крок «Підтвердити»: «Країна та мова»."),
    "title_en": ("Dialog title", "Confirm step heading."),
    "title_fr": ("Titre du dialogue", "Titre de l’étape Confirmer."),
    "text_uk": ("Поточний регіон", "Рядок під заголовком, напр. «Україна/Гривня»."),
    "text_en": ("Current region", "Line under the title, e.g. «Ukraine/Hryvnia»."),
    "text_fr": ("Région actuelle", "Ligne sous le titre, p. ex. « Ukraine/Hryvnia »."),
    "cta_uk": ("Кнопка підтвердження", "Текст кнопки «Підтвердити»."),
    "cta_en": ("Confirm button", "Confirm button label."),
    "cta_fr": ("Bouton confirmer", "Libellé du bouton Confirmer."),
    "link_uk": ("Посилання «Змінити»", "Відкриває крок вибору регіону."),
    "link_en": ("Change link", "Opens the region step."),
    "link_fr": ("Lien modifier", "Ouvre l’étape de la région."),
    "note_uk": (
        "Опис кроку регіону",
        "Текст під «Місце доставки» про ціни й доставку.",
    ),
    "note_en": ("Region step description", "Copy under the delivery place heading."),
    "note_fr": ("Description de l’étape région", "Texte sous le titre du lieu de livraison."),
    "lines_uk": (
        "Рядки діалогу (по одному в рядку)",
        "1) Місце доставки 2) Україна 3) Міжнародна доставка "
        "4) Мова сайту 5) Оберіть мову / Choose language 6) Українська 7) English 8) Français",
    ),
    "lines_en": (
        "Dialog lines (one per row)",
        "1) Delivery place 2) Ukraine 3) International delivery "
        "4) Site language 5) Choose language 6) Українська 7) English 8) Français",
    ),
    "lines_fr": (
        "Lignes du dialogue (une par ligne)",
        "1) Lieu de livraison 2) Ukraine 3) Livraison internationale "
        "4) Langue du site 5) Choisissez la langue 6) Українська 7) English 8) Français",
    ),
}


@admin.register(HomeLocaleBlock)
class HomeLocaleAdmin(KeyedBlockAdmin):
    block_key = HomeBlock.Key.LOCALE
    default_sort = 8
    tiny_fields = ()
    fieldsets = language_tabs(
        uk_fields=(
            "title_uk",
            "text_uk",
            "cta_uk",
            "link_uk",
            "note_uk",
            "lines_uk",
        ),
        en_fields=(
            "title_en",
            "text_en",
            "cta_en",
            "link_en",
            "note_en",
            "lines_en",
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        meta = LOCALE_FIELD_META.get(db_field.name)
        if formfield is not None and meta:
            formfield.label, formfield.help_text = meta
        return formfield

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        for name, (label, help_text) in LOCALE_FIELD_META.items():
            if name in form.base_fields:
                form.base_fields[name].label = label
                form.base_fields[name].help_text = help_text
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
