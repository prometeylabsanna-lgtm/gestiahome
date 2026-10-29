from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.colors import TOKEN_ACCENT, TOKEN_CHROME, TOKEN_INK, TOKEN_PAPER
from src.content.models_styles import FONT_INTER, GlobalPageStyle, PageStyle
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_color import GestiaColorWidget

_COLOR_DEFAULTS = {
    "background_color": TOKEN_PAPER,
    "chrome_background_color": TOKEN_CHROME,
    "text_color": TOKEN_INK,
    "hover_color": TOKEN_ACCENT,
}


@admin.register(GlobalPageStyle)
class GlobalPageStyleAdmin(GestiaModelAdmin):
    change_form_template = "admin/content/globalpagestyle/change_form.html"
    page_key = PageStyle.Key.GLOBAL
    fields = (
        "background_color",
        "chrome_background_color",
        "text_color",
        "hover_color",
        "font_family",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(page=self.page_key)

    def has_add_permission(self, request):
        if PageStyle.objects.filter(page=self.page_key).exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = PageStyle.objects.filter(page=self.page_key).first()
        if obj is None:
            obj = PageStyle.objects.create(page=self.page_key)
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)

    def save_model(self, request, obj, form, change):
        obj.page = self.page_key
        super().save_model(request, obj, form, change)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        default = _COLOR_DEFAULTS.get(db_field.name)
        if default:
            kwargs["widget"] = GestiaColorWidget(default=default)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is None:
            return formfield
        if db_field.name == "background_color":
            formfield.help_text = "Тло сторінок сайту."
        elif db_field.name == "chrome_background_color":
            formfield.help_text = "Спільний фон шапки і підвалу."
        elif db_field.name == "hover_color":
            formfield.help_text = "Підсвітка посилань і кнопок."
        elif db_field.name == "font_family":
            formfield.help_text = "Inter — як у макеті; System UI — системний; Georgia — із зарубками."
        return formfield

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_save_and_continue"] = True
        if request.method == "POST" and "_reset_defaults" in request.POST and object_id:
            obj = self.get_object(request, object_id)
            if obj is not None:
                obj.background_color = TOKEN_PAPER
                obj.chrome_background_color = TOKEN_CHROME
                obj.text_color = TOKEN_INK
                obj.hover_color = TOKEN_ACCENT
                obj.font_family = FONT_INTER
                obj.page = self.page_key
                obj.save()
                self.message_user(request, "Стилі скинуто до значень за замовчуванням.", messages.SUCCESS)
                return HttpResponseRedirect(request.path)
        return super().changeform_view(request, object_id, form_url, extra_context)


# Застарілі proxy лишаються в коді, але не реєструються в адмінці.
