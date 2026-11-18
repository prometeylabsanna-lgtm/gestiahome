from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.models_contacts import ContactsPage
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_lang import language_tabs


@admin.register(ContactsPage)
class ContactsPageAdmin(GestiaModelAdmin):
    fieldsets = language_tabs(
        uk_fields=("title_uk", "seo_title_uk", "seo_description_uk", "form_title_uk"),
        en_fields=("title_en", "seo_title_en", "seo_description_en", "form_title_en"),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied
        obj = self.model.load()
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)
