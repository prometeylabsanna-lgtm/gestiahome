"""Випадаючі фільтри зверху списку. Порожнє значення нічого не ховає."""

from collections.abc import Iterator
from functools import cached_property

from django import forms
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.validators import EMPTY_VALUES
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest
from unfold.contrib.filters.admin.dropdown_filters import (
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.filters.admin.mixins import DropdownMixin, ValueMixin
from unfold.widgets import UnfoldAdminSelectWidget

ALL = ("", "Усі")
_SUBMIT = "if (this.form.requestSubmit) { this.form.requestSubmit(); } else { this.form.submit(); }"


def clean_filter_label(label: str) -> str:
    text = str(label or "").strip()
    lowered = text.casefold()
    for prefix in ("за ", "by "):
        if lowered.startswith(prefix):
            return text[len(prefix):].lstrip()
    return text


class NativeDropdownForm(forms.Form):
    def __init__(self, name, label, choices, multiple=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[name] = forms.ChoiceField(
            label=label,
            required=False,
            choices=choices,
            widget=UnfoldAdminSelectWidget(
                attrs={
                    "class": "admin-top-filter__select",
                    "onchange": _SUBMIT,
                }
            ),
        )


class _CleanLabelMixin:
    form_class = NativeDropdownForm

    def _selected(self) -> str:
        value = self.value()
        return "" if value in EMPTY_VALUES else str(value)

    def _label(self) -> str:
        return clean_filter_label(self.title)

    def _form(self, name: str, choices: list) -> dict:
        return {
            "form": self.form_class(
                label=self._label(),
                name=name,
                choices=choices,
                data={name: self._selected()},
            )
        }


class GestiaChoicesFilter(_CleanLabelMixin, ChoicesDropdownFilter):
    def choices(self, changelist: ChangeList) -> Iterator:
        yield self._form(self.lookup_kwarg, [ALL, *list(self.field.flatchoices)])


class GestiaRelatedFilter(_CleanLabelMixin, RelatedDropdownFilter):
    def choices(self, changelist: ChangeList) -> Iterator:
        yield self._form(self.lookup_kwarg, [ALL, *self.lookup_choices])


class GestiaBooleanFilter(
    _CleanLabelMixin,
    ValueMixin,
    DropdownMixin,
    admin.BooleanFieldListFilter,
):
    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        if self.value() not in EMPTY_VALUES:
            return super().queryset(request, queryset)
        return queryset

    def choices(self, changelist: ChangeList) -> Iterator:
        # «Так» стоїть перед «Ні», але список відкривається на «Усі».
        yield self._form(self.lookup_kwarg, [ALL, ("1", "Так"), ("0", "Ні")])


def skip_horizontal(model_admin) -> bool:
    model = getattr(model_admin, "model", None)
    return bool(model and model.__name__.startswith("NovaPoshta"))


def _filter_field_name(item) -> str | None:
    if isinstance(item, (tuple, list)):
        if not item:
            return None
        return item[0] if isinstance(item[0], str) else None
    if isinstance(item, str):
        return item
    return None


def _is_wrapped(item) -> bool:
    return (
        isinstance(item, (tuple, list))
        and len(item) >= 2
        and not isinstance(item[1], str)
    )


def wrap_list_filter(model, list_filter):
    wrapped = []
    for item in list_filter or ():
        if _is_wrapped(item):
            wrapped.append(item)
            continue
        name = _filter_field_name(item)
        if not name:
            wrapped.append(item)
            continue
        try:
            field = model._meta.get_field(name)
        except Exception:
            wrapped.append(item)
            continue
        if isinstance(field, models.BooleanField):
            filter_cls = GestiaBooleanFilter
        elif field.is_relation:
            filter_cls = GestiaRelatedFilter
        elif getattr(field, "choices", None):
            filter_cls = GestiaChoicesFilter
        else:
            wrapped.append(item)
            continue
        wrapped.append((name, filter_cls))
    return wrapped


def horizontal_filter_options(model, list_filter, existing=None) -> dict:
    options = {key: dict(value) for key, value in dict(existing or {}).items()}
    for item in list_filter or ():
        name = _filter_field_name(item)
        if not name:
            continue
        current = options.get(name, {})
        label = current.get("label")
        if not label:
            try:
                field = model._meta.get_field(name)
                label = clean_filter_label(field.verbose_name)
            except Exception:
                label = clean_filter_label(name)
        else:
            label = clean_filter_label(label)
        options[name] = {**current, "horizontal": True, "label": label}
    return options


def _declared_filter_options(cls) -> dict:
    for parent in cls.mro():
        value = parent.__dict__.get("list_filter_options")
        if isinstance(value, dict):
            return dict(value)
    return {}


class HorizontalFiltersMixin:
    """Горизонтальні випадаючі фільтри зверху списку (крім адмінок Нової пошти)."""

    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        if skip_horizontal(self):
            return filters
        return wrap_list_filter(self.model, filters)

    @cached_property
    def list_filter_sheet(self):
        if skip_horizontal(self):
            return True
        return False

    @cached_property
    def list_filter_submit(self):
        if skip_horizontal(self):
            return False
        return True

    @cached_property
    def list_filter_options(self):
        declared = _declared_filter_options(type(self))
        if skip_horizontal(self):
            return declared
        return horizontal_filter_options(
            self.model, getattr(self, "list_filter", ()), declared
        )
