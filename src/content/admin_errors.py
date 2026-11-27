from django.contrib import admin

from src.content.admin_thankyou import _OpenSingleton
from src.content.models_errors import ErrorPage
from src.core.admin_lang import language_tabs


@admin.register(ErrorPage)
class ErrorPageAdmin(_OpenSingleton):
    fieldsets = language_tabs(
        uk_fields=("title_uk", "text_uk", "button_uk"),
        en_fields=("title_en", "text_en", "note_en", "button_en"),
    )
