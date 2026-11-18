from django.db import models

from src.content.models import SingletonModel
from src.content.ui_defaults import ARIA_HELP, UI_FIELDS, UI_GROUPS


class InterfaceCopy(SingletonModel):
    cache_key = "interface_copy_v1"

    class Meta:
        verbose_name = "Тексти інтерфейсу"
        verbose_name_plural = "Тексти інтерфейсу"

    def __str__(self):
        return "Тексти інтерфейсу"


for _key, _label, _uk, _en, _limit, _aria, _group in UI_FIELDS:
    _help = ARIA_HELP if _aria else ""
    InterfaceCopy.add_to_class(
        f"{_key}_uk",
        models.CharField(_label, max_length=_limit, blank=True, help_text=_help),
    )
    InterfaceCopy.add_to_class(
        f"{_key}_en",
        models.CharField(f"{_label} (EN)", max_length=_limit, blank=True, help_text=_help),
    )


def _proxy(name, title):
    return type(
        name,
        (InterfaceCopy,),
        {
            "__module__": __name__,
            "Meta": type("Meta", (), {"proxy": True, "verbose_name": title, "verbose_name_plural": title}),
        },
    )


UiHeader = _proxy("UiHeader", "Шапка")
UiCatalog = _proxy("UiCatalog", "Каталог")
UiProduct = _proxy("UiProduct", "Товар і колекція")
UiCart = _proxy("UiCart", "Кошик і обране")
UiCheckout = _proxy("UiCheckout", "Оформлення і оплата")
UiUtility = _proxy("UiUtility", "Службові сторінки")

UI_PROXY = {
    "header": UiHeader,
    "catalog": UiCatalog,
    "product": UiProduct,
    "cart": UiCart,
    "checkout": UiCheckout,
    "utility": UiUtility,
}

# Групи сайдбара зафіксовані тут, щоб адмінка не розходилась із полями.
assert {key for key, _title in UI_GROUPS} == set(UI_PROXY)
