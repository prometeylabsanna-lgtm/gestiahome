from decimal import Decimal

from django import template
from django.template.loader_tags import BLOCK_CONTEXT_KEY
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from src.core.utils import currency_labels, format_money

register = template.Library()


def _grouped(amount):
    whole = int(Decimal(amount).quantize(Decimal("1")))
    return f"{whole:,}".replace(",", " ")


@register.simple_tag(takes_context=True)
def money(context, amount):
    return format_money(amount, context.get("currency") or "uah")


@register.simple_tag(takes_context=True)
def product_price(context, product):
    currency = context.get("currency") or "uah"
    amount = product.price_eur if currency == "eur" else product.price_uah
    return format_money(amount, currency)


@register.filter
def figma_nbsp(value):
    return str(value).replace(" ", "\u00a0")


@register.filter(is_safe=True)
def figma_lines(value):
    return mark_safe(escape(str(value)).replace(" ", "\u00a0<wbr>"))


@register.simple_tag(takes_context=True)
def line_uah(context, amount):
    currency = context.get("currency") or "uah"
    if currency == "eur":
        return format_money(amount, "eur")
    return f"{_grouped(amount)} {currency_labels()[0]}"


@register.simple_tag(takes_context=True)
def sum_uah(context, amount):
    currency = context.get("currency") or "uah"
    if currency == "eur":
        return format_money(amount, "eur")
    return f"{currency_labels()[1]} {_grouped(amount)} {_('грн')}"


@register.simple_tag(takes_context=True)
def block_text(context, name, default=""):
    block_context = context.render_context.get(BLOCK_CONTEXT_KEY)
    block = block_context.get_block(name) if block_context is not None else None
    if block is None:
        return default
    return mark_safe(block.nodelist.render(context).strip())


@register.simple_tag(takes_context=True)
def home_price(context, product):
    currency = context.get("currency") or "uah"
    if currency == "eur":
        return format_money(product.price_eur, "eur")
    return f"{_grouped(product.price_uah)} {currency_labels()[0]}"
