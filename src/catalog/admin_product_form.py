"""Форма товару: окреме поле на кожну групу фільтрів."""

from django import forms
from unfold.widgets import UnfoldAdminSelect2MultipleWidget

from src.catalog.models import Product, ProductAttributeGroup

ATTR_PREFIX = "attr_group_"


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ("filter_attrs",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected = set()
        if self.instance.pk:
            selected = set(self.instance.filter_attrs.values_list("pk", flat=True))
        for group in ProductAttributeGroup.objects.prefetch_related("values").order_by("name_uk", "pk"):
            name = f"{ATTR_PREFIX}{group.pk}"
            qs = group.values.order_by("sort", "name_uk")
            self.fields[name] = forms.ModelMultipleChoiceField(
                label=group.name_uk,
                queryset=qs,
                required=False,
                widget=UnfoldAdminSelect2MultipleWidget,
            )
            self.fields[name].initial = [pk for pk in selected if qs.filter(pk=pk).exists()]

    def save(self, commit=True):
        obj = super().save(commit=commit)
        chosen = []
        for name, value in self.cleaned_data.items():
            if name.startswith(ATTR_PREFIX) and value is not None:
                chosen.extend(list(value))
        if commit:
            obj.filter_attrs.set(chosen)
        else:
            self._pending_attrs = chosen
        return obj

    def save_m2m(self):
        super().save_m2m()
        pending = getattr(self, "_pending_attrs", None)
        if pending is not None:
            self.instance.filter_attrs.set(pending)


def filter_field_names():
    return [f"{ATTR_PREFIX}{pk}" for pk in ProductAttributeGroup.objects.order_by("name_uk", "pk").values_list("pk", flat=True)]
