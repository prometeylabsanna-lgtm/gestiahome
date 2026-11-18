from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.models_ui import UI_PROXY
from src.content.ui_defaults import UI_GROUPS, keys_for
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_lang import language_tabs


class _OpenSingleton(GestiaModelAdmin):
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


def _fieldsets(group):
    keys = keys_for(group)
    return language_tabs(
        uk_fields=tuple(f"{key}_uk" for key in keys),
        en_fields=tuple(f"{key}_en" for key in keys),
    )


def _register(group):
    model = UI_PROXY[group]
    attrs = {"fieldsets": _fieldsets(group)}
    admin_cls = type(f"{model.__name__}Admin", (_OpenSingleton,), attrs)
    admin.site.register(model, admin_cls)
    return admin_cls


UI_ADMINS = {group: _register(group) for group, _title in UI_GROUPS}
