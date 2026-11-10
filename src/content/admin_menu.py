from django.contrib import admin

from src.content.models_menu import MenuGroup, MenuGroupItem
from src.core.admin_base import GestiaModelAdmin, GestiaTabularInline
from src.core.admin_lang import language_tabs


class MenuGroupItemInline(GestiaTabularInline):
    model = MenuGroupItem
    extra = 0
    tab = True
    verbose_name = "Пункт"
    verbose_name_plural = "Пункти"
    ordering_field = "sort"
    hide_ordering_field = True
    autocomplete_fields = ("collection", "category")
    fields = (
        "is_active",
        "sort",
        "label_uk",
        "label_en",
        "collection",
        "category",
    )


@admin.register(MenuGroup)
class MenuGroupAdmin(GestiaModelAdmin):
    list_display = ("title_uk", "is_active", "open_by_default", "sort")
    list_filter = ("is_active", "open_by_default")
    search_fields = ("title_uk", "title_en")
    ordering = ("sort", "id")
    inlines = (MenuGroupItemInline,)
    fieldsets = language_tabs(
        uk_fields=("is_active", "open_by_default", "sort", "title_uk"),
        en_fields=("title_en",),
    )
