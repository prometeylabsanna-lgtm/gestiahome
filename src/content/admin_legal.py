from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.models_legal import LegalPage
from src.content.proxies import CookiePolicyPage, OfferPage, PrivacyPolicyPage, ShippingPage
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_lang import language_tabs
from src.core.admin_tinymce import force_tinymce, tinymce_widget

_BODY_HINT = "Розділи оформлюйте заголовком 2."
_EN_HINT = "Якщо порожньо — на сайті лишається український текст."


class LegalPageAdmin(GestiaModelAdmin):
    page_key = ""
    fieldsets = language_tabs(
        uk_fields=("updated_on", "title_uk", "body_uk", "seo_title_uk", "seo_description_uk"),
        en_fields=("title_en", "body_en", "seo_title_en", "seo_description_en"),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(key=self.page_key)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = LegalPage.objects.filter(key=self.page_key).first()
        if obj is None:
            obj = LegalPage.objects.create(key=self.page_key, title_uk=str(self.model._meta.verbose_name))
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)

    def save_model(self, request, obj, form, change):
        obj.key = self.page_key
        super().save_model(request, obj, form, change)

    tiny_fields = ("body_uk", "body_en")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=False)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is None:
            return formfield
        if db_field.name == "body_uk":
            formfield.help_text = _BODY_HINT
        elif db_field.name in {"body_en", "title_en"}:
            formfield.help_text = _EN_HINT
        return formfield

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=False)
        return form


@admin.register(OfferPage)
class OfferPageAdmin(LegalPageAdmin):
    page_key = LegalPage.Key.OFFER


@admin.register(PrivacyPolicyPage)
class PrivacyPolicyPageAdmin(LegalPageAdmin):
    page_key = LegalPage.Key.PRIVACY


@admin.register(CookiePolicyPage)
class CookiePolicyPageAdmin(LegalPageAdmin):
    page_key = LegalPage.Key.COOKIES


@admin.register(ShippingPage)
class ShippingPageAdmin(LegalPageAdmin):
    page_key = LegalPage.Key.SHIPPING
